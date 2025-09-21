"""NEXRAD Level II ingestion pipeline using unsigned public AWS Open Data.

Responsibilities:
- Discover recent volume files for a radar site within lookback window.
- Convert latest new volumes to gridded reflectivity arrays.
- Write each frame as a COG (current: pseudo local planar CRS placeholder) to MinIO.
- Maintain a rolling frames index JSON for animation.

Future improvements:
- Reproject to real geographic / WebMercator coordinates.
- Parallelization & performance tuning.
- Multi-site orchestration & retention policy.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
from typing import Dict, List
import logging

import boto3
from botocore.config import Config
from botocore import UNSIGNED
from botocore.exceptions import ClientError
class RadarSourceAccessError(Exception):
    """Raised when the upstream NEXRAD source bucket cannot be accessed with current configuration."""

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code

import numpy as np
import pyart  # type: ignore
from minio import Minio  # type: ignore
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

DERIVED_BUCKET = os.getenv("DERIVED_BUCKET_NAME") or os.getenv("S3_BUCKET_DERIVED", "derived")
INDEX_PREFIX = "indices/radar/nexrad"
COG_PREFIX = "nexrad"

MAX_FRAMES = int(os.getenv("NEXRAD_MAX_FRAMES", "10"))
LOOKBACK_MINUTES_DEFAULT = int(os.getenv("NEXRAD_LOOKBACK_MINUTES", "60"))
GRID_RES_KM = float(os.getenv("NEXRAD_GRID_RES_KM", "1"))
GRID_RADIUS_KM = float(os.getenv("NEXRAD_GRID_RADIUS_KM", "300"))
NEXRAD_BUCKET_NAME = os.getenv("NEXRAD_BUCKET_NAME", "unidata-nexrad-level2")
# Request payer and credentials are intentionally ignored; bucket must be fully public per local policy.

logger = logging.getLogger("nexrad_level2")

_unsigned_cfg = Config(signature_version=UNSIGNED, retries={"max_attempts": 5, "mode": "standard"})
_s3_unsigned = None  # type: ignore


def _get_s3():
    """Return a singleton anonymous S3 client.

    Local policy forbids embedding AWS credentials or requester-pays semantics.
    All access MUST succeed anonymously; failures surface as RadarSourceAccessError.
    """
    global _s3_unsigned
    if _s3_unsigned is None:
        _s3_unsigned = boto3.client("s3", config=_unsigned_cfg)
    return _s3_unsigned

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "object-store:9000").replace("http://", "").replace("https://", ""),
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False,
)


def _frames_index_key(site: str) -> str:
    return f"{INDEX_PREFIX}/{site}/frames.json"


def load_frames_index(site: str) -> List[Dict]:
    key = _frames_index_key(site)
    try:
        data = minio_client.get_object(DERIVED_BUCKET, key).read()
        return json.loads(data)
    except Exception:
        return []


def save_frames_index(site: str, frames: List[Dict]):
    key = _frames_index_key(site)
    frames = frames[-MAX_FRAMES:]
    payload = json.dumps(frames, separators=(",", ":")).encode()
    minio_client.put_object(
        DERIVED_BUCKET, key, io.BytesIO(payload), len(payload), content_type="application/json"
    )


def list_recent_site_objects(site: str, lookback_minutes: int) -> List[Dict]:
    site = site.upper()
    now = dt.datetime.utcnow()
    date = now.date()
    prefix = f"{date:%Y/%m/%d}/{site}/"
    # Anonymous listing only (no credential fallback by policy)
    paginator = _get_s3().get_paginator("list_objects_v2")
    objs: List[Dict] = []

    # First, collect ALL objects to sort them by timestamp (newest first)
    all_objects = []
    while True:
        try:
            paginate_kwargs = {"Bucket": NEXRAD_BUCKET_NAME, "Prefix": prefix}
            for page in paginator.paginate(**paginate_kwargs):
                for c in page.get("Contents", []):
                    fname = c["Key"].rsplit("/", 1)[-1]
                    try:
                        ts_str = fname[len(site) : len(site) + 15]  # YYYYMMDD_HHMMSS
                        ts = dt.datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                        all_objects.append({"key": c["Key"], "ts": ts})
                    except Exception:
                        continue
            break
        except ClientError as e:
            code = getattr(e, "response", {}).get("Error", {}).get("Code")
            message = (
                f"Failed to list objects in public bucket '{NEXRAD_BUCKET_NAME}' prefix '{prefix}' (code={code}). "
                "Bucket must be publicly listable; local policy forbids credential fallback."
            )
            logger.error(message)
            raise RadarSourceAccessError(message, code=code) from e

    # Sort by timestamp (newest first) and filter efficiently
    all_objects.sort(key=lambda o: o["ts"], reverse=True)
    cutoff_time = now - dt.timedelta(minutes=lookback_minutes)

    for obj in all_objects:
        if obj["ts"] >= cutoff_time:
            objs.append(obj)
        else:
            # Since objects are sorted newest first, we can stop when we hit older data
            break
        # Also limit the total number of objects we consider
        if len(objs) >= MAX_FRAMES * 2:
            break

    # Return in oldest -> newest order for processing
    objs.reverse()
    return objs


def _timestamp_key(site: str, key: str) -> str:
    fname = key.rsplit("/", 1)[-1]
    ts_str = fname[len(site) : len(site) + 15].replace("_", "")  # YYYYMMDDHHMMSS
    return f"{ts_str}Z"


def _already_have(frames: List[Dict], ts_key: str) -> bool:
    return any(f["timestamp_key"] == ts_key for f in frames)


def process_volume(site: str, key: str) -> Dict:
    client = _get_s3()
    try:
        obj = client.get_object(Bucket=NEXRAD_BUCKET_NAME, Key=key)
    except ClientError as e:
        code = getattr(e, "response", {}).get("Error", {}).get("Code")
        message = (
            f"Failed to get object '{key}' from public bucket '{NEXRAD_BUCKET_NAME}' (code={code}). "
            "Bucket/object must be publicly readable; credential fallback is disabled by policy."
        )
        logger.error(message)
        raise RadarSourceAccessError(message, code=code) from e
    raw = io.BytesIO(obj["Body"].read())
    radar = pyart.io.read_nexrad_archive(raw)
    field_name = "reflectivity"
    if field_name not in radar.fields:
        # attempt alias
        for candidate in ("DBZ", "DBZH", "reflectivity_horizontal"):
            if candidate in radar.fields:
                field_name = candidate
                break
        else:
            raise RuntimeError("No reflectivity-like field found in radar volume")

    grid = pyart.map.grid_from_radars(
        (radar,),
        grid_shape=(1, int(GRID_RADIUS_KM / GRID_RES_KM * 2) + 1, int(GRID_RADIUS_KM / GRID_RES_KM * 2) + 1),
        grid_limits=(
            (0, 0),
            (-GRID_RADIUS_KM * 1000, GRID_RADIUS_KM * 1000),
            (-GRID_RADIUS_KM * 1000, GRID_RADIUS_KM * 1000),
        ),
        fields=[field_name],
        weighting_function="Nearest",
    )
    data = grid.fields[field_name]["data"][0]
    arr_f = data.filled(np.nan)
    nodata = -9999.0
    arr = np.where(np.isfinite(arr_f), arr_f, nodata).astype("float32")

    # Local planar transform placeholder (improvement: real projection + warp)
    res_m = GRID_RES_KM * 1000
    transform = from_origin(-GRID_RADIUS_KM * 1000, GRID_RADIUS_KM * 1000, res_m, res_m)

    ts_key = _timestamp_key(site, key)
    # Canonical object layout: nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.* inside the 'derived' bucket
    cog_key = f"nexrad/{site}/{ts_key}/tilt0_reflectivity.tif"
    meta_key = f"nexrad/{site}/{ts_key}/tilt0_reflectivity.json"

    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:3857",  # placeholder
        "transform": transform,
        "nodata": nodata,
        "tiled": True,
        "compress": "DEFLATE",
        "blockxsize": 256,
        "blockysize": 256,
    }

    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(arr, 1)
            dst.build_overviews([2, 4, 8, 16], Resampling.average)

        # Create COG in memory using updated profile
        cog_profile = profile.copy()
        cog_profile.update({
            "driver": "COG",
            "compress": "DEFLATE",
            "BLOCKSIZE": 256,
        })

        with MemoryFile() as cog_mem:
            with cog_mem.open(**cog_profile) as cog_dst:
                with mem.open() as src:
                    cog_dst.write(src.read(1), 1)
                    cog_dst.build_overviews([2, 4, 8, 16], Resampling.average)

            payload = cog_mem.read()
            minio_client.put_object(
                DERIVED_BUCKET, cog_key, io.BytesIO(payload), len(payload), content_type="image/tiff"
            )

    meta = {
        "site": site,
        "timestamp_key": ts_key,
        "product": "NEXRAD Level II",
        "field": field_name,
        "units": "dBZ",
        "rescale": [-30, 75],
        "cog_key": cog_key,
    }
    blob = json.dumps(meta, separators=(",", ":")).encode()
    minio_client.put_object(
        DERIVED_BUCKET, meta_key, io.BytesIO(blob), len(blob), content_type="application/json"
    )

    return {
        "timestamp_key": ts_key,
        "cog_key": cog_key,
        "meta_key": meta_key,
        "tile_template": f"/tiles/weather/nexrad-{site}/{ts_key}/{{z}}/{{x}}/{{y}}.png",
    }


def run_nexrad_level2(site: str, lookback_minutes: int, max_new: int) -> Dict:
    site = site.upper()
    existing = load_frames_index(site)
    objects = list_recent_site_objects(site, lookback_minutes)
    added = []
    for o in objects:
        ts_key = _timestamp_key(site, o["key"])
        if _already_have(existing, ts_key):
            continue
        try:
            frame = process_volume(site, o["key"])
            existing.append(frame)
            added.append(frame)
        except Exception:
            continue
        if len(added) >= max_new:
            break
    existing.sort(key=lambda f: f["timestamp_key"])  # newest last
    if added:
        save_frames_index(site, existing)
    return {"site": site, "added": len(added), "total_frames": len(existing), "frames": existing[-MAX_FRAMES:]}


__all__ = ["run_nexrad_level2", "RadarSourceAccessError"]
