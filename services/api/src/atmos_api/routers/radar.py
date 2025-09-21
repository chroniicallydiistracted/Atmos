"""Radar (NEXRAD) frames listing endpoint."""
from __future__ import annotations

import os
import json
from fastapi import APIRouter, HTTPException
from minio import Minio  # type: ignore

router = APIRouter(prefix="/v1/radar", tags=["radar"])

DERIVED_BUCKET = os.getenv("DERIVED_BUCKET_NAME") or os.getenv("S3_BUCKET_DERIVED", "derived")
client = Minio(
    os.getenv("MINIO_ENDPOINT", "object-store:9000").replace("http://", "").replace("https://", ""),
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False,
)

@router.get("/nexrad/{site}/frames")
async def get_nexrad_frames(site: str, limit: int = 10):
    site = site.upper()
    key = f"indices/radar/nexrad/{site}/frames.json"
    try:
        obj = client.get_object(DERIVED_BUCKET, key)
        data = obj.read()
    except Exception:
        raise HTTPException(status_code=404, detail="No frames yet")
    frames = json.loads(data)

    # Frames are already canonical (nexrad/<SITE>/<TS>/...) and stored directly in bucket namespace.
    return {"site": site, "frames": frames[-limit:]}
