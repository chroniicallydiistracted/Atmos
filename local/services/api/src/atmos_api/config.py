"""Configuration model for the Atmos API service."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load API configuration from environment variables or `.env`."""

    api_title: str = Field(default="Atmos API", alias="API_TITLE")
    api_version: str = Field(default="0.2.0", alias="API_VERSION")

    minio_endpoint: str = Field(default="http://object-store:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="localminio", alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(default="change-me-now", alias="MINIO_ROOT_PASSWORD")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    derived_bucket: str = Field(default="derived", alias="S3_BUCKET_DERIVED")

    database_url: str = Field(
        default="postgresql://osm:change-me-too@postgres:5432/osm",
        alias="DATABASE_URL",
    )

    ingestion_base_url: str = Field(
        default="http://ingestion:8084",
        alias="INGESTION_BASE_URL",
    )
    http_client_timeout_seconds: float = Field(
        default=30.0,
        alias="API_HTTP_TIMEOUT_SECONDS",
        gt=0,
    )
    cors_origins_raw: str = Field(
        default="http://localhost:4173",
        alias="API_CORS_ORIGINS",
        description="Comma-separated list of origins allowed for CORS requests.",
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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


__all__ = ["Settings"]
