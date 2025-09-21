#!/usr/bin/env python3
"""Seed the MinIO derived bucket with sample timeline entries."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.client import Config

DEFAULT_LAYER = "goes/sample"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", default=DEFAULT_LAYER, help="Timeline layer prefix (e.g. goes/east/abi)")
    parser.add_argument("--count", type=int, default=3, help="Number of timeline entries to create")
    parser.add_argument(
        "--minutes",
        type=int,
        default=10,
        help="Spacing between timestamps in minutes (relative to now)",
    )
    return parser.parse_args()


def build_s3_client():
    endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    access_key = os.getenv("MINIO_ROOT_USER", "localminio")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "change-me-now")
    region = os.getenv("MINIO_REGION", "us-east-1")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def ensure_indices(client, bucket: str, layer: str, count: int, spacing_minutes: int) -> None:
    now = datetime.now(timezone.utc)
    for index in range(count):
        timestamp = now - timedelta(minutes=spacing_minutes * index)
        timestamp_key = timestamp.strftime("%Y%m%dT%H%M%SZ")
        prefix = f"indices/{layer}/{timestamp_key}"
        meta_key = f"{prefix}/meta.json"

        body = {
            "layer": layer,
            "timestamp": timestamp_key,
            "seeded": True,
        }
        client.put_object(
            Bucket=bucket,
            Key=meta_key,
            Body=json.dumps(body, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        print(f"wrote s3://{bucket}/{meta_key}")


def main() -> None:
    args = parse_args()
    bucket = os.getenv("S3_BUCKET_DERIVED", "derived")
    client = build_s3_client()

    try:
        ensure_indices(client, bucket, args.layer.strip("/"), args.count, args.minutes)
    except Exception as exc:  # pragma: no cover - CLI surface
        raise SystemExit(f"Failed to seed MinIO: {exc}")


if __name__ == "__main__":
    main()
