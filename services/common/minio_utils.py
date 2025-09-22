"""Shared MinIO / S3-compatible client helpers.

Centralises construction of a MinIO client using environment variables so that
services (API, ingestion, tiler, etc.) do not duplicate endpoint and credential
logic. Keeping this in a single place simplifies future changes (e.g. adding
STS, rotating keys, or switching to an alternative SDK).
"""
from __future__ import annotations

import os
from functools import lru_cache

from minio import Minio  # type: ignore

def _endpoint_host(raw: str) -> tuple[str, bool]:
    secure = raw.startswith("https://")
    host = raw.replace("https://", "").replace("http://", "")
    return host, secure


@lru_cache(maxsize=1)
def get_minio_client() -> Minio:
    """Return a cached MinIO client configured via environment.

    Environment variables:
        MINIO_ENDPOINT: host:port or http(s)://host:port (default object-store:9000)
        MINIO_ROOT_USER / MINIO_ROOT_PASSWORD: credentials for local dev.
    """
    endpoint_env = os.getenv("MINIO_ENDPOINT", "object-store:9000")
    host, secure = _endpoint_host(endpoint_env)
    return Minio(
        host,
        access_key=os.getenv("MINIO_ROOT_USER", "localminio"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "change-me-now"),
        secure=secure,
    )


def build_object_key(*parts: str) -> str:
    """Join S3 key fragments ensuring no accidental leading slashes."""
    cleaned = [p.strip("/") for p in parts if p]
    return "/".join(cleaned)


def ensure_bucket(name: str) -> None:
    """Create a bucket if it does not already exist (idempotent)."""
    client = get_minio_client()
    if not client.bucket_exists(name):  # type: ignore[attr-defined]
        client.make_bucket(name)  # type: ignore[attr-defined]
