"""Configuration model for the Atmos API service."""
from __future__ import annotations

from pydantic import Field

from atmos_common.config import CommonSettings


class Settings(CommonSettings):
    """Load API configuration from environment variables or `.env`."""

    api_title: str = Field(default="Atmos API", alias="API_TITLE")
    api_version: str = Field(default="0.2.0", alias="API_VERSION")

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

    @property
    def cors_origins(self) -> list[str]:
        """Return a list of CORS origins."""
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


__all__ = ["Settings"]

