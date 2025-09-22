"""Legend and layer metadata endpoints.

Currently surfaces reflectivity metadata for NEXRAD ingested outputs.
This reads the metadata JSON stored in the derived bucket (uploaded by the
radar processing pipeline) and returns a trimmed structure suitable for UI legends.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from minio import Minio

from ..config import Settings
from ..deps import get_settings

router = APIRouter(prefix="/v1/legend", tags=["legend"])


def _get_minio_client(settings: Settings) -> Minio:
    return Minio(
        settings.minio_endpoint.replace("http://", "").replace("https://", ""),
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


@router.get("/nexrad/{site}/{timestamp_key}")
def nexrad_legend(
    site: str = Path(..., description="Radar site (e.g. KTLX)"),
    timestamp_key: str = Path(..., description="Timestamp key directory (e.g. 20250101T010203Z)"),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Return legend + metadata subset for a processed NEXRAD product.

    The ingestion pipeline stores metadata under the canonical key layout (bucket: derived):
        nexrad/{SITE}/{TIMESTAMP_KEY}/tilt0_reflectivity.json
    """
    bucket = settings.derived_bucket
    object_name = f"nexrad/{site.upper()}/{timestamp_key}/tilt0_reflectivity.json"
    client = _get_minio_client(settings)
    try:
        response = client.get_object(bucket, object_name)
        try:
            raw = response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Metadata not found: {object_name}") from exc

    try:
        meta = json.loads(raw)
    except ValueError as exc:  # malformed JSON
        raise HTTPException(status_code=500, detail="Corrupt metadata JSON") from exc

    # Subset relevant legend fields; keep original for debugging
    legend = {
        "product": meta.get("product"),
        "units": meta.get("units"),
        "rescale": meta.get("rescale"),
        "palette": meta.get("color_palette"),
        "timestamp": meta.get("timestamp"),
        "site": meta.get("site"),
        "extent_km": meta.get("grid_info", {}).get("extent_km"),
        "resolution_m": meta.get("grid_info", {}).get("resolution_m"),
    }
    return {"legend": legend, "raw": meta}


__all__ = ["router"]
