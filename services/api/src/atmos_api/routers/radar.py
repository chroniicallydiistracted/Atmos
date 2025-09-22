"""Radar (NEXRAD) frames listing endpoint."""
from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, HTTPException

try:
    from services.common.minio_utils import get_minio_client  # type: ignore
except ImportError:  # pragma: no cover - fallback for path issues
    from ...clients import create_minio_client as get_minio_client  # type: ignore

router = APIRouter(prefix="/v1/radar", tags=["radar"])

logger = logging.getLogger("radar_router")

_legacy_bucket = os.getenv("DERIVED_BUCKET_NAME")
if _legacy_bucket:
    logger.warning("DERIVED_BUCKET_NAME is deprecated; use S3_BUCKET_DERIVED instead.")
DERIVED_BUCKET = _legacy_bucket or os.getenv("S3_BUCKET_DERIVED", "derived")
client = get_minio_client()

@router.get("/nexrad/{site}/frames")
async def get_nexrad_frames(site: str, limit: int = 10):
    site = site.upper()
    key = f"indices/radar/nexrad/{site}/frames.json"
    try:
        obj = client.get_object(DERIVED_BUCKET, key)
        data = obj.read()
    except Exception:  # noqa: BLE001 - broad to map storage errors uniformly
        # Use explicit exception chaining suppression so traceback does not include MinIO internals.
        raise HTTPException(status_code=404, detail="No frames yet") from None
    frames = json.loads(data)

    # Frames are already canonical (nexrad/<SITE>/<TS>/...) and stored directly in bucket namespace.
    return {"site": site, "frames": frames[-limit:]}
