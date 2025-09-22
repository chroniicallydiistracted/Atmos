"""Client factories used by the ingestion service."""
from __future__ import annotations

import boto3
from botocore import UNSIGNED
from botocore.client import BaseClient
from botocore.config import Config

from .config import IngestionSettings


def build_source_s3_client(settings: IngestionSettings) -> BaseClient:
    """Return a boto3 client that talks to the public NOAA S3 buckets."""
    return boto3.client(
        "s3",
        region_name=settings.nexrad_region,
        config=Config(signature_version=UNSIGNED, retries={"max_attempts": 5, "mode": "standard"}),
    )


def build_minio_s3_client(settings: IngestionSettings) -> BaseClient:
    """Return a boto3 client configured for the local MinIO deployment."""
    addressing = {"addressing_style": "path"}
    secure = settings.minio_secure_flag
    return boto3.client(
        "s3",
        endpoint_url=settings.cleaned_minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name=settings.minio_region,
        use_ssl=secure,
        verify=secure,
        config=Config(signature_version="s3v4", s3=addressing, retries={"max_attempts": 5, "mode": "standard"}),
    )


class ClientBundle:
    """A thin container that memoises expensive boto3 client creation."""

    def __init__(self, settings: IngestionSettings):
        self._settings = settings
        self._source: BaseClient | None = None
        self._derived: BaseClient | None = None

    @property
    def source(self) -> BaseClient:
        if self._source is None:
            self._source = build_source_s3_client(self._settings)
        return self._source

    @property
    def derived(self) -> BaseClient:
        if self._derived is None:
            self._derived = build_minio_s3_client(self._settings)
        return self._derived


__all__ = ["build_source_s3_client", "build_minio_s3_client", "ClientBundle"]
