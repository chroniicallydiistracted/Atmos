"""Client factories shared across services."""
from __future__ import annotations

from typing import Tuple
from urllib.parse import urlparse

from minio import Minio

from .config import Settings


def create_minio_client(settings: Settings) -> Minio:
    """Instantiate a MinIO client from configuration."""
    parsed = urlparse(settings.minio_endpoint)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported scheme in MINIO_ENDPOINT: {settings.minio_endpoint}")
    if not parsed.netloc:
        raise ValueError("MINIO_ENDPOINT must include host[:port]")

    secure = parsed.scheme == "https"
    endpoint = parsed.netloc

    return Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )


__all__ = ["create_minio_client"]
