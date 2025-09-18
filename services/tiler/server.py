"""
TiTiler ASGI app for AtmosInsight.
Serves raster tiles from MinIO-hosted COGs with custom styling and caching.

Notes:
- No AWS SDKs or Lambda adapters are used.
- COGs are read via HTTP from the local MinIO endpoint (e.g., http://object-store:9000).
"""
import os
from titiler.application.main import app
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import Response
from rio_tiler.io import Reader
from rio_tiler.utils import render
from minio import Minio

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

# Custom route for AtmosInsight COGs from derived bucket (MinIO)
@app.get("/tiles/weather/{dataset}/{timestamp}/{z}/{x}/{y}.png")
async def weather_tiles(
    dataset: str,
    timestamp: str,
    z: int,
    x: int,
    y: int,
    style: str = "default",
    rescale: Optional[str] = None
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
    # Bucket and MinIO endpoint configuration
    # Prefer DERIVED_BUCKET_NAME, fallback to S3_BUCKET_DERIVED for compatibility.
    derived_bucket = os.getenv("DERIVED_BUCKET_NAME") or os.getenv("S3_BUCKET_DERIVED")
    if not derived_bucket:
        raise HTTPException(status_code=500, detail="Derived bucket not configured")

    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://object-store:9000").rstrip("/")

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

    # Build a pre-signed URL via MinIO SDK so we can securely access private objects via HTTP
    def get_minio_client() -> Minio:
        secure = minio_endpoint.startswith("https://")
        endpoint_host = minio_endpoint.replace("https://", "").replace("http://", "")
        return Minio(
            endpoint_host,
            access_key=os.getenv("MINIO_ROOT_USER", "localminio"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "change-me-now"),
            secure=secure,
        )

    client = get_minio_client()
    # MinIO expects object name without leading slash
    object_name = s3_key
    try:
        # Default expiry 1 hour
        http_url = client.presigned_get_object(derived_bucket, object_name, expires=3600)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign COG URL: {str(e)}")

    try:
        # Read remote COG via HTTP and render a PNG tile
        # rio-tiler returns (data, mask) arrays
        with Reader(http_url) as src:
            rescale_vals = [tuple(map(float, default_rescale.split(",")))]
            data, mask = src.tile(x, y, z, rescale=rescale_vals)
            img_bytes = render(data, mask=mask, img_format="PNG")

            return Response(
                content=img_bytes,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Content-Type": "image/png",
                },
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tile generation failed: {str(e)}")

# Health check endpoints (direct and via Caddy /tiles/* route)
@app.get("/healthz")
@app.get("/tiles/healthz")
async def health_check():
    return {"status": "healthy", "service": "titiler"}

# ASGI app is exposed as `app` for Uvicorn/Gunicorn
