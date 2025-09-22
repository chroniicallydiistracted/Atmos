#!/usr/bin/env python3
"""One-time migration script to normalize NEXRAD object keys.

Canonical layout (inside derived bucket):
  nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.tif
  nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.json

This script:
1. Scans for legacy keys:
   - radar/nexrad/<SITE>/<TIMESTAMP>.tif|json (flat style)
   - derived/nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.* (double-derived)
2. Copies them to canonical path if canonical does not already exist.
3. Rewrites the frames index JSON under indices/radar/nexrad/<SITE>/frames.json
   updating cog_key/meta_key to canonical form.
4. (Optional) Deletes legacy objects if --delete is passed.

Usage:
  python migrate_nexrad_keys.py --site KTLX [--delete]
  python migrate_nexrad_keys.py --all-sites

Assumes access to MinIO via environment variables present in local/.env and that
boto3 style credentials are NOT required (local MinIO only).
"""
from __future__ import annotations

import argparse
import json
import os
from typing import List, Dict
import io
from minio import Minio  # type: ignore

DERIVED_BUCKET = os.getenv("S3_BUCKET_DERIVED", "derived")
INDEX_PREFIX = "indices/radar/nexrad"

    # Use environment variables for configuration
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "object-store:9000")
    access_key = os.getenv("MINIO_ROOT_USER", "localminio")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "change-me-now")
    derived_bucket = os.getenv("S3_BUCKET_DERIVED", "derived")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    client = Minio(
        minio_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )


def list_objects(prefix: str):
    for obj in client.list_objects(DERIVED_BUCKET, prefix=prefix, recursive=True):
        if getattr(obj, "object_name", None):
            yield obj.object_name


def load_frames_index(site: str) -> List[Dict]:
    key = f"{INDEX_PREFIX}/{site}/frames.json"
    try:
        data = client.get_object(DERIVED_BUCKET, key).read()
        return json.loads(data)
    except Exception:
        return []


def save_frames_index(site: str, frames: List[Dict]):
    key = f"{INDEX_PREFIX}/{site}/frames.json"
    payload = json.dumps(frames, separators=(",", ":")).encode()
    client.put_object(DERIVED_BUCKET, key, io.BytesIO(payload), len(payload), content_type="application/json")


def migrate_site(site: str, delete_legacy: bool = False):
    site = site.upper()
    legacy_flat_prefix = f"radar/nexrad/{site}/"
    legacy_double_prefix = f"derived/nexrad/{site}/"
    canonical_prefix = f"nexrad/{site}/"

    to_delete: List[str] = []
    migrated = 0

    # Handle legacy flat style: radar/nexrad/<SITE>/<TS>.tif or .json
    for obj_name in list_objects(legacy_flat_prefix):
        if not obj_name:
            continue
        fname = obj_name.split("/")[-1]
        if not fname.endswith(('.tif', '.json')):
            continue
        ts_key = fname.split('.', 1)[0]  # timestamp_key without extension
        # For flat style original, expected pattern <TIMESTAMP>.tif; keep mapping
        if not ts_key.endswith('Z'):
            # Skip unexpected pattern
            continue
        # Map to canonical
        if fname.endswith('.tif'):
            canonical = f"{canonical_prefix}{ts_key}/tilt0_reflectivity.tif"
        else:
            canonical = f"{canonical_prefix}{ts_key}/tilt0_reflectivity.json"
        if canonical == obj_name:
            continue
        # Copy if not already present
        try:
            client.stat_object(DERIVED_BUCKET, canonical)
        except Exception:
            data = client.get_object(DERIVED_BUCKET, obj_name).read()
            client.put_object(
                DERIVED_BUCKET,
                canonical,
                io.BytesIO(data),
                len(data),
                content_type="application/json" if canonical.endswith('.json') else "image/tiff",
            )
        if delete_legacy:
            to_delete.append(obj_name)
        migrated += 1

    # Handle double-derived style
    for obj_name in list_objects(legacy_double_prefix):
        if not obj_name:
            continue
        # Example: derived/nexrad/KTLX/<TS>/tilt0_reflectivity.tif
        parts = obj_name.split('/')
        if len(parts) < 4:
            continue
        ts_key = parts[3]
        if not ts_key.endswith('Z'):
            continue
        rest = '/'.join(parts[4:])
        canonical = f"{canonical_prefix}{ts_key}/{rest}"
        if canonical == obj_name:
            continue
        try:
            client.stat_object(DERIVED_BUCKET, canonical)
        except Exception:
            data = client.get_object(DERIVED_BUCKET, obj_name).read()
            client.put_object(
                DERIVED_BUCKET,
                canonical,
                io.BytesIO(data),
                len(data),
                content_type="application/json" if canonical.endswith('.json') else "image/tiff",
            )
        if delete_legacy:
            to_delete.append(obj_name)
        migrated += 1

    # Rewrite frames index
    frames = load_frames_index(site)
    changed = False
    for frame in frames:
        ck = frame.get('cog_key')
        mk = frame.get('meta_key')
        if not ck or not mk:
            continue
        # Normalize cog key patterns
        if ck.startswith('radar/nexrad/'):
            ts_key = ck.split('/')[-1].split('.')[0]
            frame['cog_key'] = f"nexrad/{site}/{ts_key}/tilt0_reflectivity.tif"
            changed = True
        elif ck.startswith('derived/nexrad/'):
            parts = ck.split('/')
            # derived/nexrad/<SITE>/<TS>/tilt0_reflectivity.tif
            if len(parts) >= 4:
                ts_key = parts[3]
                frame['cog_key'] = f"nexrad/{site}/{ts_key}/tilt0_reflectivity.tif"
                changed = True
        if mk.startswith('radar/nexrad/'):
            ts_key = mk.split('/')[-1].split('.')[0]
            frame['meta_key'] = f"nexrad/{site}/{ts_key}/tilt0_reflectivity.json"
            changed = True
        elif mk.startswith('derived/nexrad/'):
            parts = mk.split('/')
            if len(parts) >= 4:
                ts_key = parts[3]
                frame['meta_key'] = f"nexrad/{site}/{ts_key}/tilt0_reflectivity.json"
                changed = True
    if changed:
        # Re-upload frames index
        payload = json.dumps(frames, separators=(",", ":")).encode()
        client.put_object(DERIVED_BUCKET, f"{INDEX_PREFIX}/{site}/frames.json", __import__('io').BytesIO(payload), len(payload), content_type="application/json")

    if delete_legacy and to_delete:
        for obj in to_delete:
            try:
                client.remove_object(DERIVED_BUCKET, obj)
            except Exception:
                pass

    return {"migrated": migrated, "deleted": len(to_delete), "frames_changed": changed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', help='Radar site (e.g. KTLX)')
    ap.add_argument('--all-sites', action='store_true', help='Attempt migration for all sites discovered in indices')
    ap.add_argument('--delete', action='store_true', help='Delete legacy objects after successful copy')
    args = ap.parse_args()

    sites: List[str] = []
    if args.all_sites:
        # Discover via index prefix
        for obj in list_objects(INDEX_PREFIX + '/'):
            if not obj:
                continue
            parts = obj.split('/')
            # indices/radar/nexrad/<SITE>/frames.json
            if len(parts) >= 4 and parts[-1] == 'frames.json':
                sites.append(parts[3])
    elif args.site:
        sites = [args.site]
    else:
        ap.error('Provide --site or --all-sites')

    results = {}
    for s in sites:
        results[s] = migrate_site(s, delete_legacy=args.delete)

    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
