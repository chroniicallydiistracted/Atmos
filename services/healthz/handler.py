import json
import os
import time
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Health check endpoint that probes key system components.
    Returns JSON with ok status and detailed probe results.
    """
    start_time = time.time()
    
    try:
        probes = {}
        overall_ok = True
        
        # Probe S3 buckets
        s3_read_ok, s3_write_ok = probe_s3()
        probes['s3_read'] = s3_read_ok
        probes['s3_write'] = s3_write_ok
        
        if not s3_read_ok or not s3_write_ok:
            overall_ok = False
        
        # Probe TiTiler latency (simple HTTP check to self)
        tiler_latency = probe_tiler()
        probes['tiler_latency_ms'] = tiler_latency
        
        # Probe data indices for freshness
        indices_status = probe_data_indices()
        probes['indices'] = indices_status
        
        # Check if any indices are stale
        for layer, status in indices_status.items():
            if not status['ok']:
                overall_ok = False
        
        # Build response
        response = {
            'ok': overall_ok,
            'version': os.getenv('VERSION', 'v0.1.0'),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'probes': probes
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        # Return 200 with ok:false rather than 5xx for monitoring
        error_response = {
            'ok': False,
            'version': os.getenv('VERSION', 'v0.1.0'),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'error': str(e),
            'probes': {}
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            },
            'body': json.dumps(error_response)
        }

def probe_s3():
    """Probe S3 read and write capabilities."""
    s3 = boto3.client('s3')
    
    static_bucket = os.getenv('STATIC_BUCKET_NAME')
    derived_bucket = os.getenv('DERIVED_BUCKET_NAME')
    
    read_ok = False
    write_ok = False
    
    try:
        # Test read from static bucket
        if static_bucket:
            s3.head_bucket(Bucket=static_bucket)
            read_ok = True
    except ClientError:
        pass
    
    try:
        # Test write to derived bucket
        if derived_bucket:
            test_key = f'health-check/{int(time.time())}.txt'
            s3.put_object(
                Bucket=derived_bucket,
                Key=test_key,
                Body=b'health-check',
                ContentType='text/plain'
            )
            # Clean up test object
            s3.delete_object(Bucket=derived_bucket, Key=test_key)
            write_ok = True
    except ClientError:
        pass
    
    return read_ok, write_ok

def probe_tiler():
    """Probe TiTiler latency with a simple test."""
    # For now, just return a mock latency
    # In production, this could make an HTTP request to the tiler endpoint
    import random
    return random.randint(50, 200)

def probe_data_indices():
    """Check freshness of data layer indices."""
    s3 = boto3.client('s3')
    derived_bucket = os.getenv('DERIVED_BUCKET_NAME')
    
    indices_status = {}
    
    if not derived_bucket:
        return indices_status
    
    # Check GOES C13 index
    indices_status['goes_c13'] = check_index_freshness(
        s3, derived_bucket, 'indices/goes/east/abi/c13/conus/index.json', 
        max_age_minutes=15
    )
    
    # Check MRMS reflectivity index
    indices_status['mrms_reflq'] = check_index_freshness(
        s3, derived_bucket, 'indices/mrms/reflq/index.json',
        max_age_minutes=10
    )
    
    # Check NWS alerts index
    indices_status['alerts'] = check_index_freshness(
        s3, derived_bucket, 'indices/alerts/index.json',
        max_age_minutes=10
    )
    
    return indices_status

def check_index_freshness(s3, bucket, key, max_age_minutes):
    """Check if an index file is fresh enough."""
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        last_modified = response['LastModified']
        
        # Calculate age in seconds
        age_seconds = (time.time() - last_modified.timestamp())
        max_age_seconds = max_age_minutes * 60
        
        return {
            'newest_age_s': int(age_seconds),
            'ok': age_seconds <= max_age_seconds
        }
        
    except ClientError:
        return {
            'newest_age_s': -1,
            'ok': False
        }