"""
NWS Alerts MVT baking Lambda.
Fetches active alerts, processes geometries, and generates Mapbox Vector Tiles.
"""
import json
import os
import tempfile
import subprocess
import boto3
import requests
from datetime import datetime
import logging
import gzip
from pathlib import Path

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Bake NWS alerts into Mapbox Vector Tiles.
    Runs every 5 minutes via EventBridge schedule.
    """
    try:
        logger.info("Starting alerts MVT baking process")
        
        # Fetch active alerts from NWS API
        alerts_data = fetch_active_alerts()
        logger.info(f"Fetched {len(alerts_data['features'])} active alerts")
        
        # Process alerts and generate MVT
        mvt_timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = process_alerts_to_mvt(alerts_data, temp_dir, mvt_timestamp)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'timestamp': mvt_timestamp,
                'alerts_count': len(alerts_data['features']),
                **result
            })
        }
        
    except Exception as e:
        logger.error(f"Error baking alerts MVT: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def fetch_active_alerts():
    """Fetch active alerts from NWS API."""
    nws_api_url = "https://api.weather.gov/alerts/active"
    
    headers = {
        'User-Agent': 'AtmosInsight/1.0 (weather.westfam.media)',
        'Accept': 'application/geo+json'
    }
    
    all_features = []
    page_url = nws_api_url
    
    # Handle pagination
    while page_url:
        response = requests.get(page_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        features = data.get('features', [])
        all_features.extend(features)
        
        # Check for next page
        pagination = data.get('pagination', {})
        page_url = pagination.get('next')
        
        # Limit to avoid infinite loops
        if len(all_features) > 10000:
            logger.warning("Reached alert limit of 10000")
            break
    
    # Process alerts for MVT schema
    processed_features = []
    for feature in all_features:
        try:
            processed_feature = process_alert_feature(feature)
            if processed_feature:
                processed_features.append(processed_feature)
        except Exception as e:
            logger.warning(f"Failed to process alert: {e}")
    
    return {
        'type': 'FeatureCollection',
        'features': processed_features
    }

def process_alert_feature(feature):
    """Process a single alert feature for MVT schema."""
    props = feature.get('properties', {})
    geometry = feature.get('geometry')
    
    # Skip if no geometry and no UGC codes for zone lookup
    if not geometry and not props.get('geocode', {}).get('UGC'):
        return None
    
    # Extract key properties for MVT (keep lean)
    processed_props = {
        'id': props.get('id', ''),
        'event': props.get('event', ''),
        'severity': props.get('severity', 'Unknown'),
        'urgency': props.get('urgency', 'Unknown'), 
        'certainty': props.get('certainty', 'Unknown'),
        'status': props.get('status', 'Actual'),
        'sent': props.get('sent', ''),
        'ends': props.get('ends'),
        'area': truncate_text(props.get('areaDesc', ''), 100),
        'ugc': ','.join(props.get('geocode', {}).get('UGC', [])),
        'marine': is_marine_alert(props)
    }
    
    # Handle geometry - prefer alert geometry, fallback to UGC zone lookup
    if geometry:
        final_geometry = geometry
    else:
        # TODO: Implement UGC zone geometry lookup
        # For now, skip alerts without direct geometry
        return None
    
    return {
        'type': 'Feature',
        'geometry': final_geometry,
        'properties': processed_props
    }

def is_marine_alert(props):
    """Check if alert is marine/coastal."""
    marine_keywords = ['marine', 'coastal', 'beach', 'surf', 'rip', 'tsunami']
    event_text = props.get('event', '').lower()
    area_text = props.get('areaDesc', '').lower()
    
    return any(keyword in event_text or keyword in area_text for keyword in marine_keywords)

def truncate_text(text, max_length):
    """Truncate text to max length."""
    if not text:
        return ''
    return text[:max_length] if len(text) > max_length else text

def process_alerts_to_mvt(alerts_data, temp_dir, timestamp):
    """Process alerts GeoJSON to MVT tiles using tippecanoe."""
    s3_client = boto3.client('s3')
    derived_bucket = os.getenv('DERIVED_BUCKET_NAME')
    
    # Write GeoJSON to temporary file
    geojson_path = os.path.join(temp_dir, 'alerts.geojson')
    with open(geojson_path, 'w') as f:
        json.dump(alerts_data, f)
    
    # Create MVT tiles directory
    mvt_dir = os.path.join(temp_dir, 'mvt')
    os.makedirs(mvt_dir)
    
    # Run tippecanoe to generate MVT
    tippecanoe_cmd = [
        'tippecanoe',
        '-o', mvt_dir,
        '--force',
        '--minimum-zoom=3',
        '--maximum-zoom=12',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--layer=alerts',
        '--attribute-type=marine:bool',
        geojson_path
    ]
    
    result = subprocess.run(tippecanoe_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Tippecanoe failed: {result.stderr}")
    
    logger.info("Generated MVT tiles with tippecanoe")
    
    # Upload MVT tiles to S3
    tiles_uploaded = upload_mvt_tiles(s3_client, derived_bucket, mvt_dir, timestamp)
    
    # Create TileJSON metadata
    tilejson = create_tilejson(timestamp)
    tilejson_key = f"tiles/alerts/{timestamp}/tile.json"
    
    s3_client.put_object(
        Bucket=derived_bucket,
        Key=tilejson_key,
        Body=json.dumps(tilejson, indent=2),
        ContentType='application/json',
        ContentEncoding='gzip' if compress_tilejson(tilejson) else None
    )
    
    # Update alerts index
    update_alerts_index(s3_client, derived_bucket, timestamp)
    
    return {
        'tiles_uploaded': tiles_uploaded,
        'tilejson_key': tilejson_key
    }

def upload_mvt_tiles(s3_client, bucket, mvt_dir, timestamp):
    """Upload MVT tiles to S3 with compression."""
    tiles_uploaded = 0
    
    for pbf_file in Path(mvt_dir).rglob('*.pbf'):
        # Extract z/x/y from file path
        relative_path = pbf_file.relative_to(mvt_dir)
        s3_key = f"tiles/alerts/{timestamp}/{relative_path}"
        
        # Gzip compress the tile
        with open(pbf_file, 'rb') as f:
            tile_data = f.read()
        
        compressed_data = gzip.compress(tile_data)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=compressed_data,
            ContentType='application/vnd.mapbox-vector-tile',
            ContentEncoding='gzip',
            CacheControl='public, max-age=3600'
        )
        
        tiles_uploaded += 1
    
    logger.info(f"Uploaded {tiles_uploaded} MVT tiles")
    return tiles_uploaded

def create_tilejson(timestamp):
    """Create TileJSON metadata for the alert tiles."""
    base_url = f"https://weather.westfam.media/tiles/alerts/{timestamp}"
    
    return {
        "tilejson": "3.0.0",
        "name": "NWS Alerts",
        "description": "Active weather alerts from the National Weather Service",
        "version": "1.0.0",
        "attribution": "National Weather Service",
        "scheme": "xyz",
        "tiles": [f"{base_url}/{{z}}/{{x}}/{{y}}.pbf"],
        "minzoom": 3,
        "maxzoom": 12,
        "bounds": [-180, -85.0511, 180, 85.0511],
        "center": [-98.5, 39.5, 4],
        "vector_layers": [
            {
                "id": "alerts",
                "description": "Weather alert polygons",
                "minzoom": 3,
                "maxzoom": 12,
                "fields": {
                    "id": "Alert identifier",
                    "event": "Event type (e.g., Tornado Warning)",
                    "severity": "Severity level",
                    "urgency": "Urgency level",
                    "certainty": "Certainty level",
                    "status": "Alert status",
                    "sent": "Issue timestamp",
                    "ends": "Expiration timestamp",
                    "area": "Affected area description",
                    "ugc": "UGC zone codes",
                    "marine": "Marine/coastal alert flag"
                }
            }
        ]
    }

def compress_tilejson(tilejson_data):
    """Compress TileJSON if it's large enough to benefit."""
    json_str = json.dumps(tilejson_data)
    return len(json_str) > 1024  # Compress if > 1KB

def update_alerts_index(s3_client, bucket, timestamp):
    """Update the alerts timeline index."""
    index_key = "indices/alerts/index.json"
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=index_key)
        index_data = json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        index_data = {
            'latest': '',
            'history': []
        }
    
    # Update index
    history = index_data.get('history', [])
    if timestamp not in history:
        history.append(timestamp)
        history.sort(reverse=True)
        history = history[:24]  # Keep last 24 (2 hours at 5-min intervals)
    
    index_data['latest'] = timestamp
    index_data['history'] = history
    
    s3_client.put_object(
        Bucket=bucket,
        Key=index_key,
        Body=json.dumps(index_data, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Updated alerts index with {len(history)} timestamps")