"""
MRMS mosaic preparation Lambda.
Downloads MRMS composite reflectivity from AWS Open Data and creates national mosaic COG.
"""
import json
import os
import tempfile
import boto3
from datetime import datetime, timedelta
import numpy as np
import xarray as xr
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import gzip
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Prepare MRMS composite reflectivity mosaic for tiling.
    Triggered by EventBridge every 5 minutes.
    
    Event parameters:
    - product: MRMS product (default: reflq)
    - time: UTC timestamp or 'latest'
    """
    try:
        # Parse parameters
        product = event.get('product', 'reflq')  # MergedReflectivityQComposite
        time_param = event.get('time', 'latest')
        
        logger.info(f"Processing MRMS {product}, time {time_param}")
        
        # Find the target timestamp
        if time_param == 'latest':
            target_time = find_latest_mrms_data(product)
        else:
            target_time = datetime.fromisoformat(time_param.replace('Z', '+00:00'))
        
        if not target_time:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No MRMS data found'})
            }
        
        # Process the MRMS file
        result = process_mrms_file(product, target_time)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'product': product,
                'timestamp': target_time.isoformat() + 'Z',
                **result
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing MRMS data: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def find_latest_mrms_data(product):
    """Find the most recent MRMS file in the AWS Open Data bucket."""
    s3 = boto3.client('s3', region_name='us-east-1')
    mrms_bucket = 'noaa-mrms-pds'
    
    # MRMS updates every 2 minutes, look back up to 30 minutes
    now = datetime.utcnow()
    for minutes_back in range(0, 30, 2):  # Every 2 minutes
        check_time = now - timedelta(minutes=minutes_back)
        
        # MRMS file naming pattern
        year = check_time.strftime('%Y')
        month = check_time.strftime('%m')
        day = check_time.strftime('%d')
        
        # Try different product names for MergedReflectivityQComposite
        product_names = [
            'MergedReflectivityQComposite',
            'MergedReflectivityComposite_00.50',
            'MRMS_MergedReflectivityQC'
        ]
        
        for product_name in product_names:
            # MRMS path structure: YYYY/MM/DD/product_name/
            prefix = f"{year}/{month}/{day}/{product_name}/"
            
            try:
                response = s3.list_objects_v2(
                    Bucket=mrms_bucket,
                    Prefix=prefix,
                    MaxKeys=20
                )
                
                if 'Contents' in response:
                    # Find files matching our time window (±10 minutes)
                    time_window_files = []
                    
                    for obj in response['Contents']:
                        filename = os.path.basename(obj['Key'])
                        
                        # Try to extract timestamp from filename
                        # Format: product_name_YYYYMMDD-HHMMSS.grib2.gz
                        file_time = extract_time_from_mrms_filename(filename)
                        if file_time:
                            time_diff = abs(check_time - file_time)
                            if time_diff <= timedelta(minutes=10):
                                time_window_files.append((obj['Key'], file_time, time_diff))
                    
                    if time_window_files:
                        # Use the most recent file in the window
                        best_file = min(time_window_files, key=lambda x: x[2])
                        logger.info(f"Found MRMS file: {best_file[0]} at {best_file[1]}")
                        return best_file[1]  # Return the file timestamp
                        
            except Exception as e:
                logger.debug(f"No data found for {prefix}: {e}")
                continue
    
    logger.warning("No recent MRMS data found")
    return None

def extract_time_from_mrms_filename(filename):
    """Extract timestamp from MRMS filename."""
    try:
        # Various MRMS filename formats
        # MergedReflectivityQComposite_00.50_20241201-180000.grib2.gz
        # MRMS_MergedReflectivityQC_00.50_20241201-180000.grib2.gz
        
        parts = filename.split('_')
        for part in parts:
            if '-' in part and len(part.replace('.grib2', '').replace('.gz', '')) >= 15:
                # Found potential timestamp part: YYYYMMDD-HHMMSS
                timestamp_part = part.split('.')[0]  # Remove file extensions
                if len(timestamp_part) == 15:  # YYYYMMDD-HHMMSS
                    return datetime.strptime(timestamp_part, '%Y%m%d-%H%M%S')
        
        return None
    except Exception:
        return None

def process_mrms_file(product, target_time):
    """Download and process MRMS file to COG."""
    s3_client = boto3.client('s3')
    derived_bucket = os.getenv('DERIVED_BUCKET_NAME')
    
    if not derived_bucket:
        raise ValueError("DERIVED_BUCKET_NAME environment variable not set")
    
    # Find the actual MRMS file
    mrms_key = find_mrms_file_for_time(product, target_time)
    
    if not mrms_key:
        raise FileNotFoundError(f"No MRMS {product} data found for {target_time}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download MRMS GRIB2 file
        grib_file = os.path.join(temp_dir, 'mrms.grib2.gz')
        
        logger.info(f"Downloading MRMS file: {mrms_key}")
        s3_client.download_file('noaa-mrms-pds', mrms_key, grib_file)
        
        # Decompress if needed
        if grib_file.endswith('.gz'):
            decompressed_file = os.path.join(temp_dir, 'mrms.grib2')
            with gzip.open(grib_file, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            grib_file = decompressed_file
        
        # Read GRIB2 with xarray
        logger.info("Reading MRMS GRIB2 file")
        
        try:
            # Try different engines for GRIB2 reading
            ds = xr.open_dataset(grib_file, engine='cfgrib')
        except Exception as e:
            logger.warning(f"cfgrib failed: {e}, trying pynio")
            try:
                ds = xr.open_dataset(grib_file, engine='pynio')
            except Exception as e2:
                raise Exception(f"Failed to read GRIB2 file with both cfgrib and pynio: {e}, {e2}")
        
        # Extract reflectivity data
        # MRMS variable names can vary
        refl_var = None
        for var_name in ds.data_vars:
            var = ds[var_name]
            if hasattr(var, 'long_name') or hasattr(var, 'standard_name'):
                long_name = getattr(var, 'long_name', '').lower()
                standard_name = getattr(var, 'standard_name', '').lower()
                
                if 'reflect' in long_name or 'reflect' in standard_name or 'dbz' in var_name.lower():
                    refl_var = var_name
                    break
        
        if not refl_var:
            # Fallback: use the first data variable
            refl_var = list(ds.data_vars)[0]
            logger.warning(f"No clear reflectivity variable found, using: {refl_var}")
        
        refl_data = ds[refl_var]
        logger.info(f"Using variable: {refl_var}, shape: {refl_data.shape}")
        
        # Get coordinate information
        # MRMS uses various coordinate names
        lat_coord = None
        lon_coord = None
        
        for coord_name in refl_data.coords:
            coord = refl_data.coords[coord_name]
            if hasattr(coord, 'long_name'):
                long_name = coord.long_name.lower()
                if 'lat' in long_name:
                    lat_coord = coord_name
                elif 'lon' in long_name:
                    lon_coord = coord_name
        
        # Fallback coordinate detection
        if not lat_coord or not lon_coord:
            coord_names = list(refl_data.coords)
            if len(coord_names) >= 2:
                # Assume last two coords are lat/lon
                lat_coord = coord_names[-2] if not lat_coord else lat_coord
                lon_coord = coord_names[-1] if not lon_coord else lon_coord
        
        if not lat_coord or not lon_coord:
            raise ValueError(f"Could not identify lat/lon coordinates. Available: {list(refl_data.coords)}")
        
        # Get coordinate arrays
        lats = refl_data.coords[lat_coord].values
        lons = refl_data.coords[lon_coord].values
        
        # Handle 2D vs 1D coordinates
        if lats.ndim == 1 and lons.ndim == 1:
            # Create mesh grid for 1D coordinates
            lons_2d, lats_2d = np.meshgrid(lons, lats)
        else:
            lats_2d = lats
            lons_2d = lons
        
        # Get reflectivity values
        refl_values = refl_data.values
        if refl_values.ndim > 2:
            # Take first time/level slice if multidimensional
            refl_values = refl_values[0] if refl_values.shape[0] == 1 else refl_values.squeeze()
        
        # Ensure 2D
        while refl_values.ndim > 2:
            refl_values = refl_values[0]
        
        # Handle missing/invalid values
        if hasattr(refl_data, '_FillValue'):
            fill_value = refl_data._FillValue
            refl_values = np.where(refl_values == fill_value, np.nan, refl_values)
        
        # Convert to dBZ if needed (some MRMS products are in linear units)
        if np.nanmax(refl_values) > 100:  # Likely linear reflectivity
            refl_values = 10 * np.log10(np.maximum(refl_values, 0.01))
        
        # Create output raster
        # Define CONUS extent for consistent output
        conus_bounds = (-130.0, 20.0, -60.0, 55.0)  # west, south, east, north
        output_shape = (1400, 2800)  # ~2.5km resolution
        
        # Create output transform
        output_transform = from_bounds(*conus_bounds, output_shape[1], output_shape[0])
        
        # Reproject/interpolate MRMS data to regular grid
        logger.info("Reprojecting MRMS data to regular CONUS grid")
        
        # Create regular output grid
        output_data = np.full(output_shape, np.nan, dtype=np.float32)
        
        # Simple nearest neighbor interpolation for now
        # In production, would use proper interpolation methods
        west, south, east, north = conus_bounds
        
        # Map MRMS coordinates to output grid indices
        y_indices = ((lats_2d - south) / (north - south) * (output_shape[0] - 1)).astype(int)
        x_indices = ((lons_2d - west) / (east - west) * (output_shape[1] - 1)).astype(int)
        
        # Filter valid indices
        valid_mask = (
            (y_indices >= 0) & (y_indices < output_shape[0]) &
            (x_indices >= 0) & (x_indices < output_shape[1]) &
            ~np.isnan(refl_values)
        )
        
        # Assign values to output grid
        if valid_mask.any():
            output_data[y_indices[valid_mask], x_indices[valid_mask]] = refl_values[valid_mask]
        
        # Create temporary GeoTIFF
        temp_tiff = os.path.join(temp_dir, 'mrms_mosaic.tif')
        
        with rasterio.open(
            temp_tiff,
            'w',
            driver='GTiff',
            height=output_shape[0],
            width=output_shape[1],
            count=1,
            dtype=output_data.dtype,
            crs=CRS.from_epsg(4326),
            transform=output_transform,
            nodata=np.nan,
            compress='lzw'
        ) as dst:
            dst.write(output_data, 1)
        
        # Convert to COG and upload
        timestamp_str = target_time.strftime('%Y%m%dT%H%M%SZ')
        s3_key_base = f"derived/mrms/reflq/{timestamp_str}"
        
        cog_key = f"{s3_key_base}/mosaic.tif"
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
        metadata = {
            'units': 'dBZ',
            'product': 'MRMS Merged Reflectivity Composite',
            'timestamp': target_time.isoformat() + 'Z',
            'coverage': 'CONUS',
            'resolution': '~2.5km',
            'bounds': conus_bounds,
            'shape': output_shape,
            'rescale': [-30, 80],
            'color_palette': 'nexrad_reflectivity',
            'provenance': 'NOAA MRMS',
            'update_cadence': '2-5 minutes',
            'caveats': ['Composite product from multiple radars', 'Some interpolation artifacts possible']
        }
        
        s3_client.put_object(
            Bucket=derived_bucket,
            Key=meta_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        # Update timeline index
        update_mrms_timeline_index(s3_client, derived_bucket, timestamp_str)
        
        logger.info("Successfully processed MRMS data")
        
        return {
            'cog_key': cog_key,
            'meta_key': meta_key,
            'data_shape': output_shape,
            'source_file': os.path.basename(mrms_key)
        }

def find_mrms_file_for_time(product, target_time):
    """Find MRMS file for specific timestamp."""
    s3 = boto3.client('s3')
    mrms_bucket = 'noaa-mrms-pds'
    
    # Search around target time
    year = target_time.strftime('%Y')
    month = target_time.strftime('%m')
    day = target_time.strftime('%d')
    
    product_names = [
        'MergedReflectivityQComposite',
        'MergedReflectivityComposite_00.50',
        'MRMS_MergedReflectivityQC'
    ]
    
    for product_name in product_names:
        prefix = f"{year}/{month}/{day}/{product_name}/"
        
        try:
            response = s3.list_objects_v2(
                Bucket=mrms_bucket,
                Prefix=prefix,
                MaxKeys=50
            )
            
            if 'Contents' in response:
                # Find best matching file
                best_file = None
                best_diff = timedelta(hours=1)  # Max 1 hour difference
                
                for obj in response['Contents']:
                    filename = os.path.basename(obj['Key'])
                    file_time = extract_time_from_mrms_filename(filename)
                    
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

def update_mrms_timeline_index(s3_client, bucket, timestamp):
    """Update the MRMS timeline index with the new timestamp."""
    index_key = "indices/mrms/reflq/index.json"
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=index_key)
        index_data = json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        index_data = {
            'timestamps': [],
            'latest': '',
            'cadence_minutes': 5
        }
    
    # Add new timestamp and keep only last 12 (1 hour at 5-min intervals)
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
    
    logger.info(f"Updated MRMS timeline index: {len(timestamps)} timestamps")