"""Configuration models for the local ingestion service."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    """Load ingestion related configuration from environment variables."""

    # Object-store / MinIO configuration
    minio_endpoint: str = Field(
        default="http://object-store:9000",
        description="URL for the S3-compatible object store endpoint.",
        alias="MINIO_ENDPOINT",
    )
    minio_access_key: str = Field(
        default="localminio",
        alias="MINIO_ROOT_USER",
        description="Access key used for the MinIO/S3-compatible store.",
    )
    minio_secret_key: str = Field(
        default="change-me-now",
        alias="MINIO_ROOT_PASSWORD",
        description="Secret key for the MinIO/S3-compatible store.",
    )
    minio_region: str = Field(
        default="us-east-1",
        alias="MINIO_REGION",
        description="Region string reported to S3 clients (MinIO accepts anything).",
    )
    minio_secure: bool = Field(
        default=False,
        alias="MINIO_SECURE",
        description="When true, talk to the object store over HTTPS.",
    )
    derived_bucket: str = Field(
        default="derived",
        alias="S3_BUCKET_DERIVED",
        description="Bucket/prefix used to persist processed outputs.",
    )

    # Source data configuration
    nexrad_bucket: str = Field(
        default="unidata-nexrad-level2",
        alias="NEXRAD_BUCKET_NAME",
        description="AWS Open Data bucket that exposes Level II radar archives.",
    )
    nexrad_region: str = Field(
        default="us-east-1",
        alias="NEXRAD_SOURCE_REGION",
        description="Region used when talking to the public NEXRAD data bucket.",
    )
    default_site: str = Field(
        default="KTLX",
        alias="NEXRAD_DEFAULT_SITE",
        description="Fallback radar site when none is supplied.",
    )
    default_minutes_lookback: int = Field(
        default=10,
        alias="NEXRAD_DEFAULT_MINUTES_LOOKBACK",
        description="How far back to look when no timestamp is provided.",
        ge=0,
    )

    goes_bucket: str = Field(
        default="noaa-goes16",
        alias="GOES_SOURCE_BUCKET",
        description="AWS Open Data bucket that exposes GOES ABI products.",
    )
    goes_default_band: int = Field(
        default=13,
        alias="GOES_DEFAULT_BAND",
        ge=1,
        le=16,
        description="Default ABI channel number when none is provided.",
    )
    goes_default_sector: str = Field(
        default="CONUS",
        alias="GOES_DEFAULT_SECTOR",
        description="Default GOES sector shorthand (e.g. CONUS, FULL).",
    )

    # Scheduler configuration (not yet wired for automatic runs, but reserved)
    scheduler_enabled: bool = Field(
        default=False,
        alias="INGESTION_ENABLE_SCHEDULER",
        description="Enable background scheduler loops when true.",
    )
    scheduler_interval_minutes: int = Field(
        default=6,
        alias="INGESTION_SCHEDULER_INTERVAL_MINUTES",
        description="How often to re-run the NEXRAD job when the scheduler is active.",
        ge=1,
    )
    max_workers: int = Field(
        default=2,
        alias="INGESTION_MAX_WORKERS",
        description="Maximum number of blocking ingestion jobs to execute concurrently.",
        ge=1,
    )

    @staticmethod
    def _discover_env_file() -> Optional[Path]:
        here = Path(__file__).resolve()
        for candidate in here.parents:
            maybe = candidate / "local" / "config" / ".env"
            if maybe.exists():
                return maybe
        return None

    _env_file = _discover_env_file.__func__()  # type: ignore[misc]

    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cleaned_minio_endpoint(self) -> str:
        """Return an endpoint URL without trailing slashes."""
        value = self.minio_endpoint.rstrip("/")
        parsed = urlparse(value)
        if not parsed.scheme:
            raise ValueError(f"MINIO_ENDPOINT must include a scheme (got: {self.minio_endpoint})")
        return value

    @cached_property
    def minio_host(self) -> str:
        parsed = urlparse(self.cleaned_minio_endpoint)
        return parsed.netloc

    @cached_property
    def minio_scheme(self) -> str:
        parsed = urlparse(self.cleaned_minio_endpoint)
        return parsed.scheme

    @cached_property
    def minio_secure_flag(self) -> bool:
        if self.minio_scheme == "https":
            return True
        if self.minio_scheme == "http":
            return False
        return self.minio_secure


__all__ = ["IngestionSettings"]
