"""
TiTiler ASGI app for AtmosInsight.
Serves raster tiles from MinIO-hosted COGs with custom styling and caching.

Notes:
- No AWS SDKs or Lambda adapters are used.
- COGs are read via HTTP from the local MinIO endpoint (e.g., http://object-store:9000).
"""
import logging
import os
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from minio import Minio

try:
    from services.common.minio_utils import get_minio_client  # type: ignore
except ImportError:  # pragma: no cover
    get_minio_client = None  # type: ignore
try:  # Allow operation without heavy tiler deps (e.g., unit tests without rio-tiler installed)
    from rio_tiler.io import Reader  # type: ignore
    from rio_tiler.utils import render  # type: ignore
    from titiler.application.main import app  # type: ignore
    _tiler_available = True
except Exception:  # pragma: no cover - executed only when deps absent
    Reader = None  # type: ignore
    render = None  # type: ignore
    app = FastAPI(title="Atmos Tiler (degraded)")
    _tiler_available = False

logger = logging.getLogger("tiler")

# Deprecation: prefer S3_BUCKET_DERIVED over legacy DERIVED_BUCKET_NAME
_legacy_bucket = os.getenv("DERIVED_BUCKET_NAME")
if _legacy_bucket:
    logger.warning("DERIVED_BUCKET_NAME is deprecated; use S3_BUCKET_DERIVED instead.")

# Configure CORS for AtmosInsight domain
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)

    # Allow requests from AtmosInsight domain
    origin = request.headers.get("origin")
    allowed_origins = [
        "https://weather.westfam.media",
        "http://localhost:4173",  # Development
        "http://127.0.0.1:4173"   # Development
    ]

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"

    return response

def _temp_rescale_for_style(base_range: tuple[float, float], style: str) -> tuple[float, float]:
    """Return rescale range appropriate for requested temperature style.

    Input range is in Kelvin. We transform the bounds when converting units.
    """
    k_min, k_max = base_range
    if style == "celsius":
        return (k_min - 273.15, k_max - 273.15)
    if style == "fahrenheit":
        return ((k_min - 273.15) * 9 / 5 + 32, (k_max - 273.15) * 9 / 5 + 32)
    return (k_min, k_max)


def _convert_temperature(data, style: str):  # numpy imported lazily later; keep generic signature
    if style == "celsius":
        return data - 273.15
    if style == "fahrenheit":
        return (data - 273.15) * 9 / 5 + 32
    return data

# Custom route for AtmosInsight COGs from derived bucket (MinIO)
@app.get("/tiles/weather/{dataset}/{timestamp}/{z}/{x}/{y}.png")
async def weather_tiles(
    dataset: str,
    timestamp: str,
    z: int,
    x: int,
    y: int,
    style: str = "default",
    rescale: str | None = None
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
    derived_bucket = os.getenv("S3_BUCKET_DERIVED")
    if not derived_bucket:
        raise HTTPException(status_code=500, detail="Derived bucket not configured")

    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://object-store:9000").rstrip("/")

    # Map dataset to S3 path
    if dataset == "goes-c13":
        s3_key = f"derived/goes/east/abi/c13/conus/{timestamp}/bt_c13.tif"
        base_range = (180.0, 330.0)
        style_range = _temp_rescale_for_style(base_range, style)
        default_rescale = f"{style_range[0]},{style_range[1]}" if not rescale else rescale

    elif dataset == "mrms-reflq":
        s3_key = f"derived/mrms/reflq/{timestamp}/mosaic.tif"
        default_rescale = "-30,80" if not rescale else rescale

    elif dataset.startswith("nexrad-"):
        site = dataset.replace("nexrad-", "").upper()
        # Canonical NEXRAD layout (inside derived bucket): nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.tif
        s3_key = f"nexrad/{site}/{timestamp}/tilt0_reflectivity.tif"
        default_rescale = "-30,80" if not rescale else rescale

    else:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset}")

    # Build a pre-signed URL via MinIO SDK so we can securely access private objects via HTTP
    if get_minio_client is None:  # fallback local inline construction
        secure = minio_endpoint.startswith("https://")
        endpoint_host = minio_endpoint.replace("https://", "").replace("http://", "")
        client = Minio(
            endpoint_host,
            access_key=os.getenv("MINIO_ROOT_USER", "localminio"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "change-me-now"),
            secure=secure,
        )
    else:
        client = get_minio_client()
    # MinIO expects object name without leading slash
    object_name = s3_key
    try:
        # Default expiry 1 hour
        http_url = client.presigned_get_object(derived_bucket, object_name, expires=timedelta(hours=1))
    except Exception as e:  # noqa: BLE001
        # Suppress internal MinIO stack details in outward facing error
        raise HTTPException(status_code=500, detail=f"Failed to sign COG URL: {str(e)}") from None

    if not _tiler_available:
        raise HTTPException(status_code=500, detail="Tiler dependencies unavailable")

    try:
        # Read remote COG via HTTP and render a PNG tile
        # rio-tiler returns (data, mask) arrays
        with Reader(http_url) as src:  # type: ignore[misc]
            rescale_vals = [tuple(map(float, default_rescale.split(",")))]
            data, mask = src.tile(x, y, z)
            # Apply style conversions before numeric rescale
            if dataset == "goes-c13":
                data = _convert_temperature(data, style)
            # Apply rescaling to convert float32 to uint8 for PNG
            import numpy as np
            data_scaled = np.clip((data - rescale_vals[0][0]) / (rescale_vals[0][1] - rescale_vals[0][0]) * 255, 0, 255).astype("uint8")
            if render is None:  # safety guard (shouldn't happen if _tiler_available True)
                raise HTTPException(status_code=500, detail="Render backend unavailable")
            img_bytes = render(data_scaled, mask=mask, img_format="PNG")  # type: ignore[operator]

            return Response(
                content=img_bytes,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Content-Type": "image/png",
                },
            )

    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Tile generation failed: {str(e)}") from None

# Health check endpoints (direct and via Caddy /tiles/* route)
@app.get("/healthz")
@app.get("/tiles/healthz")
async def health_check():
    return {"status": "healthy", "service": "titiler"}

# ASGI app is exposed as `app` for Uvicorn/Gunicorn
