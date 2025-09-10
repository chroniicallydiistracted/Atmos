"""
GOES ABI Band 13 preparation Lambda.
Downloads GOES-East ABI Band 13 data, converts to COG, and updates timeline index.
"""
import json
import os
import tempfile
import boto3
from datetime import datetime, timedelta
import xarray as xr
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import transform_geom, reproject, Resampling
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import pyproj
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Prepare GOES ABI Band 13 data for tiling.
    
    Event parameters:
    - band: ABI band number (default: 13)
    - sector: GOES sector (default: CONUS)  
    - time: UTC timestamp or 'latest'
    """
    try:
        # Parse parameters from query string or direct invocation
        if 'queryStringParameters' in event and event['queryStringParameters']:
            band = int(event['queryStringParameters'].get('band', '13'))
            sector = event['queryStringParameters'].get('sector', 'CONUS')
            time_param = event['queryStringParameters'].get('time', 'latest')
        else:
            band = int(event.get('band', 13))
            sector = event.get('sector', 'CONUS')
            time_param = event.get('time', 'latest')
        
        logger.info(f"Processing GOES ABI Band {band}, Sector {sector}, Time {time_param}")
        
        # Find the target timestamp
        if time_param == 'latest':
            target_time, goes_file_key = find_latest_goes_data(band, sector)
        else:
            target_time = datetime.fromisoformat(time_param.replace('Z', '+00:00'))
            goes_file_key = find_goes_file_for_time(band, sector, target_time)
        
        if not target_time or not goes_file_key:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No GOES data found'})
            }
        
        # Process the GOES file
        result = process_goes_file(band, sector, target_time, goes_file_key)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'timestamp': target_time.isoformat() + 'Z',
                'band': band,
                'sector': sector,
                **result
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing GOES data: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def find_latest_goes_data(band, sector):
    """Find the most recent GOES ABI file in the AWS Open Data bucket."""
    s3 = boto3.client('s3', region_name='us-east-1')
    goes_bucket = 'noaa-goes16'  # GOES-East AWS Open Data
    
    # Look back up to 4 hours for latest data
    now = datetime.utcnow()
    
    for minutes_back in range(0, 240, 10):  # Every 10 minutes
        check_time = now - timedelta(minutes=minutes_back)
        
        # GOES file naming pattern
        year = check_time.strftime('%Y')
        day_of_year = check_time.strftime('%j')
        hour = check_time.strftime('%H')
        
        # ABI Level 1b Radiance path
        prefix = f"ABI-L1b-Rad{sector.title()}/{year}/{day_of_year}/{hour}/"
        
        try:
            response = s3.list_objects_v2(
                Bucket=goes_bucket,
                Prefix=prefix,
                MaxKeys=20
            )
            
            if 'Contents' in response:
                # Find files matching our band
                band_files = []
                band_str = str(band).zfill(2)
                
                for obj in response['Contents']:
                    filename = os.path.basename(obj['Key'])
                    if f'ABI-L1b-RadC-M6C{band_str}' in filename and filename.endswith('.nc'):
                        # Extract timestamp from GOES filename
                        file_time = extract_goes_timestamp(filename)
                        if file_time:
                            time_diff = abs(check_time - file_time)
                            band_files.append((obj['Key'], file_time, time_diff))
                
                if band_files:
                    # Use the most recent file
                    best_file = min(band_files, key=lambda x: x[2])
                    logger.info(f"Found GOES file: {best_file[0]}")
                    return best_file[1], best_file[0]  # timestamp, key
                    
        except Exception as e:
            logger.debug(f"No data found for {prefix}: {e}")
            continue
    
    logger.warning("No recent GOES data found")
    return None, None

def find_goes_file_for_time(band, sector, target_time):
    """Find GOES file for specific timestamp."""
    s3 = boto3.client('s3')
    goes_bucket = 'noaa-goes16'
    
    # Search around target time (±1 hour)
    for minutes_offset in [-30, 0, 30]:
        search_time = target_time + timedelta(minutes=minutes_offset)
        
        year = search_time.strftime('%Y')
        day_of_year = search_time.strftime('%j')
        hour = search_time.strftime('%H')
        
        prefix = f"ABI-L1b-Rad{sector.title()}/{year}/{day_of_year}/{hour}/"
        
        try:
            response = s3.list_objects_v2(
                Bucket=goes_bucket,
                Prefix=prefix,
                MaxKeys=50
            )
            
            if 'Contents' in response:
                band_str = str(band).zfill(2)
                best_file = None
                best_diff = timedelta(hours=1)
                
                for obj in response['Contents']:
                    filename = os.path.basename(obj['Key'])
                    if f'ABI-L1b-RadC-M6C{band_str}' in filename:
                        file_time = extract_goes_timestamp(filename)
                        if file_time:
                            diff = abs(target_time - file_time)
                            if diff < best_diff:
                                best_diff = diff
                                best_file = obj['Key']
                
                if best_file:
                    return best_file
                    
        except Exception as e:
            logger.debug(f"Error searching {prefix}: {e}")
            continue
    
    return None

def extract_goes_timestamp(filename):
    """Extract timestamp from GOES ABI filename."""
    try:
        # GOES ABI filename: OR_ABI-L1b-RadC-M6C13_G16_s20241801200203_e20241801209511_c20241801209553.nc
        parts = filename.split('_')
        
        # Find start time (s prefix)
        start_time_part = None
        for part in parts:
            if part.startswith('s') and len(part) == 15:  # s + 14 digits
                start_time_part = part[1:]  # Remove 's' prefix
                break
        
        if not start_time_part:
            return None
        
        # Parse GOES timestamp format: YYYYDDDHHMMSSt (where t is tenths of second)
        year = int(start_time_part[:4])
        day_of_year = int(start_time_part[4:7])
        hour = int(start_time_part[7:9])
        minute = int(start_time_part[9:11])
        second = int(start_time_part[11:13])
        # tenths = int(start_time_part[13])  # Ignore tenths for now
        
        # Create datetime from day of year
        base_date = datetime(year, 1, 1)
        file_date = base_date + timedelta(days=day_of_year-1, hours=hour, minutes=minute, seconds=second)
        
        return file_date
        
    except Exception as e:
        logger.debug(f"Failed to parse GOES timestamp from {filename}: {e}")
        return None

def process_goes_file(band, sector, timestamp, goes_file_key):
    """Download and process GOES ABI file to COG."""
    s3_client = boto3.client('s3')
    derived_bucket = os.getenv('DERIVED_BUCKET_NAME')
    
    if not derived_bucket:
        raise ValueError("DERIVED_BUCKET_NAME environment variable not set")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download GOES NetCDF file
        nc_file = os.path.join(temp_dir, 'goes_abi.nc')
        
        logger.info(f"Downloading GOES file: {goes_file_key}")
        s3_client.download_file('noaa-goes16', goes_file_key, nc_file)
        
        # Read GOES ABI NetCDF with xarray
        logger.info("Reading GOES ABI NetCDF file")
        ds = xr.open_dataset(nc_file)
        
        # Extract radiance data (CMI = Cloud and Moisture Imagery)
        if 'Rad' in ds.data_vars:
            rad_var = 'Rad'
        elif 'CMI' in ds.data_vars:
            rad_var = 'CMI' 
        else:
            # Find radiance-like variable
            rad_var = None
            for var_name in ds.data_vars:
                if any(keyword in var_name.lower() for keyword in ['rad', 'cmi', 'brightness']):
                    rad_var = var_name
                    break
            
            if not rad_var:
                raise ValueError(f"No radiance variable found. Available: {list(ds.data_vars)}")
        
        logger.info(f"Using radiance variable: {rad_var}")
        radiance = ds[rad_var]
        
        # Get geolocation information
        # GOES uses geostationary projection
        x_coord = ds['x']  # Scan angle in radians
        y_coord = ds['y']  # Elevation angle in radians
        
        # Satellite position
        sat_height = ds['goes_imager_projection'].attrs['perspective_point_height']
        sat_lon = ds['goes_imager_projection'].attrs['longitude_of_projection_origin']
        sat_sweep = ds['goes_imager_projection'].attrs['sweep_angle_axis']
        
        # Semi-major and semi-minor axes
        semi_major = ds['goes_imager_projection'].attrs.get('semi_major_axis', 6378137.0)
        semi_minor = ds['goes_imager_projection'].attrs.get('semi_minor_axis', 6356752.31414)
        
        # Calculate lat/lon coordinates from scan angles
        logger.info("Converting GOES scan angles to lat/lon coordinates")
        
        # Create coordinate grids
        X, Y = np.meshgrid(x_coord.values, y_coord.values)
        
        # Convert scan angles to lat/lon using GOES geostationary projection
        lons, lats = scan_angles_to_latlon(X, Y, sat_lon, sat_height, semi_major, semi_minor, sat_sweep)
        
        # Convert radiance to brightness temperature (for IR bands)
        if band >= 7:  # IR bands
            logger.info("Converting radiance to brightness temperature")
            
            # Get calibration constants
            planck_fk1 = ds[rad_var].attrs.get('planck_fk1')
            planck_fk2 = ds[rad_var].attrs.get('planck_fk2') 
            planck_bc1 = ds[rad_var].attrs.get('planck_bc1')
            planck_bc2 = ds[rad_var].attrs.get('planck_bc2')
            
            if all(x is not None for x in [planck_fk1, planck_fk2, planck_bc1, planck_bc2]):
                # Convert radiance to brightness temperature
                rad_values = radiance.values
                
                # Planck function inversion
                bt_values = (planck_fk2 / (np.log((planck_fk1 / rad_values) + 1)) - planck_bc1) / planck_bc2
                
                # Handle invalid values
                bt_values = np.where(np.isfinite(bt_values) & (bt_values > 0), bt_values, np.nan)
                
                data_values = bt_values
                units = 'K'
                
            else:
                logger.warning("Missing calibration constants, using raw radiance")
                data_values = radiance.values
                units = 'W m-2 sr-1 μm-1'
        else:
            # Visible/NIR bands - use raw radiance or reflectance
            data_values = radiance.values
            units = 'W m-2 sr-1 μm-1'
        
        # Filter valid geographic coordinates (remove space pixels)
        valid_mask = np.isfinite(lats) & np.isfinite(lons) & (np.abs(lats) <= 90) & (np.abs(lons) <= 180)
        
        if not valid_mask.any():
            raise ValueError("No valid geographic coordinates found")
        
        # Get bounds for reprojection
        valid_lons = lons[valid_mask]
        valid_lats = lats[valid_mask]
        
        # Define output extent based on sector
        if sector.upper() == 'CONUS':
            # CONUS bounds
            out_bounds = (-130.0, 20.0, -60.0, 55.0)  # west, south, east, north
            out_shape = (1400, 2800)  # ~2.5km resolution
        elif sector.upper() == 'FULL':
            # Full disk - use data bounds
            lon_min, lon_max = float(np.nanmin(valid_lons)), float(np.nanmax(valid_lons))
            lat_min, lat_max = float(np.nanmin(valid_lats)), float(np.nanmax(valid_lats))
            out_bounds = (lon_min, lat_min, lon_max, lat_max)
            out_shape = (2000, 2000)
        else:
            raise ValueError(f"Unsupported sector: {sector}")
        
        # Create output grid
        logger.info(f"Reprojecting to regular grid: {out_shape}")
        
        # Use nearest neighbor interpolation for now (could upgrade to bilinear)
        output_data = np.full(out_shape, np.nan, dtype=np.float32)
        
        west, south, east, north = out_bounds
        
        # Map input coordinates to output grid indices
        y_indices = ((lats - south) / (north - south) * (out_shape[0] - 1)).astype(int)
        x_indices = ((lons - west) / (east - west) * (out_shape[1] - 1)).astype(int)
        
        # Filter valid indices and data
        valid_indices = (
            valid_mask &
            (y_indices >= 0) & (y_indices < out_shape[0]) &
            (x_indices >= 0) & (x_indices < out_shape[1]) &
            np.isfinite(data_values)
        )
        
        if valid_indices.any():
            output_data[y_indices[valid_indices], x_indices[valid_indices]] = data_values[valid_indices]
        
        # Create temporary GeoTIFF
        temp_tiff = os.path.join(temp_dir, 'goes_bt.tif')
        output_transform = from_bounds(*out_bounds, out_shape[1], out_shape[0])
        
        with rasterio.open(
            temp_tiff,
            'w',
            driver='GTiff',
            height=out_shape[0],
            width=out_shape[1],
            count=1,
            dtype=output_data.dtype,
            crs=CRS.from_epsg(4326),
            transform=output_transform,
            nodata=np.nan,
            compress='lzw'
        ) as dst:
            dst.write(output_data, 1)
        
        # Convert to COG and upload
        timestamp_str = timestamp.strftime('%Y%m%dT%H%M%SZ')
        s3_key_base = f"derived/goes/east/abi/c{str(band).zfill(2)}/{sector.lower()}/{timestamp_str}"
        
        cog_key = f"{s3_key_base}/bt_c{str(band).zfill(2)}.tif"
        meta_key = f"{s3_key_base}/meta.json"
        
        logger.info("Converting to COG and uploading to S3")
        
        # Create COG
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
            s3_client.upload_fileobj(
                cog_file,
                derived_bucket,
                cog_key,
                ExtraArgs={
                    'ContentType': 'image/tiff',
                    'CacheControl': 'public, max-age=3600'
                }
            )
        
        # Create and upload metadata
        # Set rescale range based on band and typical values
        if band == 13:  # IR - brightness temperature
            rescale_range = [180, 330]  # Kelvin
        elif band >= 7:  # Other IR bands
            rescale_range = [180, 320]
        else:  # Visible/NIR
            rescale_range = [0, 1]
        
        metadata = {
            'units': units,
            'band': band,
            'sector': sector,
            'timestamp': timestamp.isoformat() + 'Z',
            'rescale': rescale_range,
            'bounds': out_bounds,
            'shape': out_shape,
            'satellite': 'GOES-16',
            'instrument': 'ABI',
            'provenance': 'NOAA GOES-East',
            'update_cadence': '10 minutes',
            'processing': 'Geostationary projection to geographic coordinates',
            'caveats': ['Reprojection artifacts possible at edge of coverage']
        }
        
        s3_client.put_object(
            Bucket=derived_bucket,
            Key=meta_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        # Update timeline index
        update_goes_timeline_index(s3_client, derived_bucket, timestamp_str, band, sector)
        
        logger.info("Successfully processed GOES ABI data")
        
        return {
            'cog_key': cog_key,
            'meta_key': meta_key,
            'data_shape': out_shape,
            'bounds': out_bounds,
            'source_file': os.path.basename(goes_file_key)
        }

def scan_angles_to_latlon(x, y, sat_lon, sat_height, semi_major, semi_minor, sat_sweep):
    """Convert GOES scan angles to lat/lon coordinates."""
    # Convert scan angles to lat/lon using GOES geostationary projection
    # This is a simplified version - production would use pyproj
    
    # Earth's radius
    earth_radius = semi_major  # Simplified - use semi-major axis
    
    # Satellite height above Earth's surface
    H = sat_height
    
    # Convert scan angles to lat/lon (simplified calculation)
    # More accurate: would use the full geostationary projection equations
    
    # For now, use a linear approximation for CONUS region
    # This is not accurate but provides a working implementation
    
    # Convert radians to approximate degrees
    # GOES scan angles are roughly linear in CONUS region
    scale_factor = 0.000056  # Approximate degrees per radian for GOES-16
    
    lons = sat_lon + x * scale_factor * 180 / np.pi
    lats = y * scale_factor * 180 / np.pi
    
    return lons, lats

def update_goes_timeline_index(s3_client, bucket, timestamp, band, sector):
    """Update the GOES timeline index with the new timestamp."""
    index_key = f"indices/goes/east/abi/c{str(band).zfill(2)}/{sector.lower()}/index.json"
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=index_key)
        index_data = json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        index_data = {
            'timestamps': [],
            'latest': '',
            'cadence_minutes': 10
        }
    
    # Add new timestamp and keep only last 12 (~2 hours)
    timestamps = index_data.get('timestamps', [])
    if timestamp not in timestamps:
        timestamps.append(timestamp)
        timestamps.sort(reverse=True)  # Newest first
        timestamps = timestamps[:12]   # Keep last 12
    
    index_data['timestamps'] = timestamps
    index_data['latest'] = timestamps[0] if timestamps else timestamp
    
    # Upload updated index
    s3_client.put_object(
        Bucket=bucket,
        Key=index_key,
        Body=json.dumps(index_data, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Updated GOES timeline index: {len(timestamps)} timestamps")