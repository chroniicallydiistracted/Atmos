"""Common configuration models for all Atmos services."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Base settings with shared object-store and env discovery logic."""

    minio_endpoint: str = Field(default="http://object-store:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="localminio", alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(default="change-me-now", alias="MINIO_ROOT_PASSWORD")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    derived_bucket: str = Field(default="derived", alias="S3_BUCKET_DERIVED")

    @staticmethod
    def _discover_env_file() -> Path | None:
        """Discover the .env file in the config directory."""
        here = Path(__file__).resolve()
        for candidate in here.parents:
            top = candidate / "config" / ".env"
            if top.exists():
                return top
        return None

    _env_file = _discover_env_file()

    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )
