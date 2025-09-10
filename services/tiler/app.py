"""
TiTiler Lambda handler for AtmosInsight.
Serves raster tiles from S3 COGs with custom styling and caching.
"""
import os
from mangum import Mangum
from titiler.application.main import app
from titiler.core.errors import add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware, CompressionMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import Response

# Configure CORS for AtmosInsight domain
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Allow requests from AtmosInsight domain
    origin = request.headers.get("origin")
    allowed_origins = [
        "https://weather.westfam.media",
        "http://localhost:3000",  # Development
        "http://127.0.0.1:3000"   # Development
    ]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

# Custom route for AtmosInsight COGs from derived bucket
@app.get("/tiles/weather/{dataset}/{timestamp}/{z}/{x}/{y}.png")
async def weather_tiles(
    dataset: str,
    timestamp: str, 
    z: int,
    x: int,
    y: int,
    style: str = "default",
    rescale: str = None
):
    """
    Serve weather data tiles from AtmosInsight derived bucket.
    
    Args:
        dataset: goes-c13, mrms-reflq, nexrad-{site}
        timestamp: ISO8601 timestamp  
        z, x, y: Tile coordinates
        style: Rendering style (kelvin, celsius, fahrenheit for GOES)
        rescale: Custom rescale range (e.g., "180,330")
    """
    derived_bucket = os.getenv('DERIVED_BUCKET_NAME')
    if not derived_bucket:
        raise HTTPException(status_code=500, detail="Derived bucket not configured")
    
    # Map dataset to S3 path
    if dataset == "goes-c13":
        s3_key = f"derived/goes/east/abi/c13/conus/{timestamp}/bt_c13.tif"
        default_rescale = "180,330" if not rescale else rescale
        
        # Handle temperature unit conversions
        if style == "celsius":
            # Apply Kelvin to Celsius conversion in colormap
            pass  # Implement temperature conversion logic
        elif style == "fahrenheit":
            # Apply Kelvin to Fahrenheit conversion in colormap  
            pass  # Implement temperature conversion logic
            
    elif dataset == "mrms-reflq":
        s3_key = f"derived/mrms/reflq/{timestamp}/mosaic.tif"
        default_rescale = "-30,80" if not rescale else rescale
        
    elif dataset.startswith("nexrad-"):
        site = dataset.replace("nexrad-", "").upper()
        s3_key = f"derived/nexrad/{site}/{timestamp}/tilt0_reflectivity.tif"
        default_rescale = "-30,80" if not rescale else rescale
        
    else:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset}")
    
    # Construct S3 URL
    s3_url = f"s3://{derived_bucket}/{s3_key}"
    
    try:
        # Use TiTiler's built-in tile rendering
        from titiler.core.factory import TilerFactory
        from rio_tiler.io import Reader
        
        tiler = TilerFactory()
        
        with Reader(s3_url) as src:
            tile = src.tile(x, y, z, rescale=default_rescale.split(","))
            
            # Return PNG tile
            return Response(
                content=tile.render(img_format="PNG"),
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Content-Type": "image/png"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tile generation failed: {str(e)}")

# Health check endpoint
@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "titiler"}

# Lambda handler
handler = Mangum(app)