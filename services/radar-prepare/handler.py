"""
NEXRAD Level II radar preparation Lambda.
Downloads Level II data, extracts tilt 0 reflectivity, grids to Cartesian, and creates COG.
"""
import json
import os
import tempfile
import boto3
from botocore.client import BaseClient
from datetime import datetime, timedelta
import numpy as np
import pyart
import xarray as xr
from rasterio import transform
from rasterio.crs import CRS
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import rasterio
from rasterio.transform import from_bounds
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Prepare NEXRAD Level II radar data for tiling.
    
    Event parameters:
    - site: Radar site (e.g., KTLX)
    - time: UTC timestamp
    """
    try:
        # Parse parameters from query string or direct invocation
        if 'queryStringParameters' in event and event['queryStringParameters']:
            site = event['queryStringParameters'].get('site', 'KTLX')
            time_param = event['queryStringParameters'].get('time', '')
        else:
            site = event.get('site', 'KTLX')
            time_param = event.get('time', '')
        
        if not time_param:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'time parameter is required'})
            }
        
        logger.info(f"Processing NEXRAD Level II for site {site}, time {time_param}")
        
        # Parse timestamp
        target_time = datetime.fromisoformat(time_param.replace('Z', '+00:00'))
        
        # Process the NEXRAD file
        result = process_nexrad_file(site, target_time)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'site': site,
                'timestamp': target_time.isoformat() + 'Z',
                **result
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing NEXRAD data: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def find_nexrad_file(site, target_time, s3_client: BaseClient | None = None):
    """Find the closest NEXRAD Level II file in AWS Open Data.

    Args:
        site: Four letter radar site identifier (e.g. ``KTLX``).
        target_time: Desired observation timestamp (naive UTC ``datetime``).
        s3_client: Optional boto3 S3 client. When omitted the default
            ``us-east-1`` client is created which targets AWS Open Data.
    """
    s3 = s3_client or boto3.client('s3', region_name='us-east-1')
    nexrad_bucket = 'noaa-nexrad-level2'
    
    # NEXRAD file structure: YYYY/MM/DD/SITE/
    year = target_time.strftime('%Y')
    month = target_time.strftime('%m')
    day = target_time.strftime('%d')
    
    prefix = f"{year}/{month}/{day}/{site}/"
    
    try:
        response = s3.list_objects_v2(
            Bucket=nexrad_bucket,
            Prefix=prefix,
            MaxKeys=100
        )
        
        if 'Contents' not in response:
            logger.warning(f"No NEXRAD files found for {site} on {year}-{month}-{day}")
            return None, None
        
        # Find the file closest to target time
        best_file = None
        best_time_diff = timedelta(days=1)  # Max 1 day difference
        
        for obj in response['Contents']:
            filename = os.path.basename(obj['Key'])
            
            # NEXRAD Level II filename format: SITE_YYYYMMDD_HHMMSS_V06
            if not filename.startswith(site):
                continue
                
            try:
                # Extract timestamp from filename
                parts = filename.split('_')
                if len(parts) >= 3:
                    date_part = parts[1]  # YYYYMMDD
                    time_part = parts[2]  # HHMMSS
                    
                    file_time = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                    time_diff = abs(target_time - file_time)
                    
                    if time_diff < best_time_diff:
                        best_time_diff = time_diff
                        best_file = obj['Key']
                        
            except ValueError:
                continue
        
        if best_file:
            logger.info(f"Found NEXRAD file: {best_file} (diff: {best_time_diff})")
            return best_file, best_time_diff
        else:
            return None, None
            
    except Exception as e:
        logger.error(f"Error searching for NEXRAD file: {e}")
        return None, None

def process_nexrad_file(
    site,
    target_time,
    *,
    source_s3_client: BaseClient | None = None,
    derived_s3_client: BaseClient | None = None,
    derived_bucket: str | None = None,
):
    """Download and process NEXRAD Level II file to COG.

    Parameters mirror the legacy Lambda implementation but now support dependency
    injection so alternative storage backends (e.g. MinIO) can be supplied when
    running outside AWS.
    """
    derived_client = derived_s3_client or boto3.client('s3')
    source_client = source_s3_client or boto3.client('s3', region_name='us-east-1')
    derived_bucket_name = derived_bucket or os.getenv('DERIVED_BUCKET_NAME')

    if not derived_bucket_name:
        raise ValueError("DERIVED_BUCKET_NAME environment variable not set")

    # Find the NEXRAD file
    nexrad_key, time_diff = find_nexrad_file(site, target_time, s3_client=source_client)
    
    if not nexrad_key:
        raise FileNotFoundError(f"No NEXRAD Level II data found for {site} near {target_time}")
    
    # If file is more than 30 minutes from target, warn but continue
    if time_diff and time_diff > timedelta(minutes=30):
        logger.warning(f"NEXRAD file is {time_diff} from requested time")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download NEXRAD file
        nexrad_file = os.path.join(temp_dir, 'nexrad.gz')
        
        logger.info(f"Downloading NEXRAD file: {nexrad_key}")
        source_client.download_file('noaa-nexrad-level2', nexrad_key, nexrad_file)
        
        # Process with Py-ART
        logger.info("Processing NEXRAD file with Py-ART")
        radar = pyart.io.read_nexrad_archive(nexrad_file)
        
        # Extract tilt 0 (lowest elevation) reflectivity
        tilt_0_index = 0  # First sweep is typically lowest elevation
        refl_field = 'reflectivity'
        
        if refl_field not in radar.fields:
            # Try alternative field names
            for alt_name in ['DBZH', 'DBZ', 'reflectivity_horizontal']:
                if alt_name in radar.fields:
                    refl_field = alt_name
                    break
            else:
                raise ValueError(f"No reflectivity field found in radar data. Available: {list(radar.fields.keys())}")
        
        # Get radar location
        radar_lat = radar.latitude['data'][0]
        radar_lon = radar.longitude['data'][0]
        radar_alt = radar.altitude['data'][0]
        
        logger.info(f"Radar location: {radar_lat:.4f}°N, {radar_lon:.4f}°W, {radar_alt}m")
        
        # Grid radar data to Cartesian coordinates
        # Use 1km resolution in 240km x 240km grid (super-res coverage)
        grid_shape = (480, 480)  # 1km pixels
        grid_limits = ((-240000, 240000), (-240000, 240000), (500, 20000))
        
        logger.info("Gridding radar data to Cartesian coordinates")
        grid = pyart.map.grid_from_radars(
            radar, 
            grid_shape=grid_shape,
            grid_limits=grid_limits,
            fields=[refl_field],
            weighting_function='Barnes2',
            roi_func='dist_beam'
        )
        
        # Extract gridded reflectivity (level 0 = surface)
        refl_data = grid.fields[refl_field]['data'][0]  # Surface level
        
        # Create geospatial metadata
        # Grid is centered on radar location with 1km resolution
        pixel_size = 1000.0  # 1km in meters
        
        # Calculate bounds (grid is centered on radar)
        west = radar_lon - (grid_shape[1] * pixel_size / 2) / 111320  # rough deg per meter
        east = radar_lon + (grid_shape[1] * pixel_size / 2) / 111320
        south = radar_lat - (grid_shape[0] * pixel_size / 2) / 110540  # rough deg per meter  
        north = radar_lat + (grid_shape[0] * pixel_size / 2) / 110540
        
        # Create rasterio transform
        transform_matrix = from_bounds(west, south, east, north, grid_shape[1], grid_shape[0])
        
        # Convert masked array to regular array with nodata
        if hasattr(refl_data, 'mask'):
            refl_data = np.ma.filled(refl_data, fill_value=-999.0)
        
        # Create temporary GeoTIFF
        temp_tiff = os.path.join(temp_dir, 'reflectivity.tif')
        
        with rasterio.open(
            temp_tiff,
            'w',
            driver='GTiff',
            height=grid_shape[0],
            width=grid_shape[1],
            count=1,
            dtype=refl_data.dtype,
            crs=CRS.from_epsg(4326),  # WGS84
            transform=transform_matrix,
            nodata=-999.0,
            compress='lzw'
        ) as dst:
            dst.write(refl_data.astype(refl_data.dtype), 1)
        
        # Convert to COG
        timestamp_str = target_time.strftime('%Y%m%dT%H%M%SZ')
        s3_key_base = f"derived/nexrad/{site.upper()}/{timestamp_str}"
        
        cog_key = f"{s3_key_base}/tilt0_reflectivity.tif"
        meta_key = f"{s3_key_base}/meta.json"
        
        # Upload COG to S3
        logger.info("Converting to COG and uploading to S3")
        
        # Create COG in memory
        cog_profile = cog_profiles.get('lzw')
        cog_profile.update({'TILED': 'YES', 'BLOCKXSIZE': 256, 'BLOCKYSIZE': 256})
        
        with tempfile.NamedTemporaryFile(suffix='.tif') as cog_file:
            cog_translate(
                temp_tiff,
                cog_file.name,
                cog_profile,
                overview_level=5,
                web_optimized=True
            )
            
            # Upload COG
            cog_file.seek(0)
            derived_client.upload_fileobj(
                cog_file,
                derived_bucket_name,
                cog_key,
                ExtraArgs={
                    'ContentType': 'image/tiff',
                    'CacheControl': 'public, max-age=3600'
                }
            )

        # Create and upload metadata
        actual_time = extract_actual_time_from_file(nexrad_key) or target_time
        
        metadata = {
            'units': 'dBZ',
            'product': 'Level II Reflectivity',
            'tilt': 0,
            'timestamp': actual_time.isoformat() + 'Z',
            'site': site.upper(),
            'radar_location': {
                'latitude': float(radar_lat),
                'longitude': float(radar_lon),
                'elevation_m': float(radar_alt)
            },
            'grid_info': {
                'resolution_m': pixel_size,
                'extent_km': 240,
                'shape': grid_shape
            },
            'rescale': [-30, 80],
            'color_palette': 'nexrad_reflectivity',
            'provenance': 'NOAA NEXRAD Level II',
            'processing': 'Py-ART gridding with Barnes weighting',
            'caveats': ['Polar to Cartesian interpolation artifacts possible near radar']
        }
        
        derived_client.put_object(
            Bucket=derived_bucket_name,
            Key=meta_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Successfully processed NEXRAD data for {site}")
        
        return {
            'cog_key': cog_key,
            'meta_key': meta_key,
            'actual_timestamp': actual_time.isoformat() + 'Z',
            'grid_shape': grid_shape,
            'time_difference_minutes': time_diff.total_seconds() / 60 if time_diff else 0
        }

def extract_actual_time_from_file(nexrad_key):
    """Extract actual timestamp from NEXRAD filename."""
    try:
        filename = os.path.basename(nexrad_key)
        parts = filename.split('_')
        if len(parts) >= 3:
            date_part = parts[1]  # YYYYMMDD
            time_part = parts[2]  # HHMMSS
            return datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
    except:
        pass
    return None
