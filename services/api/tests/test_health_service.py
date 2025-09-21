from unittest.mock import MagicMock

import pytest

from src.atmos_api.config import Settings
from src.atmos_api.services.health import HealthService


@pytest.mark.asyncio
async def test_health_service_success():
    settings = Settings()
    minio_client = MagicMock()
    minio_client.list_buckets.return_value = []

    service = HealthService(settings, minio_factory=lambda: minio_client, postgres_dsn="postgresql://user:pass@host/db")

    async def fake_check():
        return await service.probe()

    # Patch the internal postgres check to avoid real connection
    service._check_postgres = lambda: None  # type: ignore[attr-defined]

    response = await fake_check()
    assert response.ok is True
    assert response.status == "ok"
    assert response.checks["minio"] == "ok"
    assert response.checks["postgres"] == "ok"


@pytest.mark.asyncio
async def test_health_service_failure():
    settings = Settings()

    def failing_minio():
        raise RuntimeError("boom")

    service = HealthService(settings, minio_factory=failing_minio)

    # Patch postgres to fail as well
    def failing_pg():
        raise RuntimeError("pg down")

    service._check_postgres = failing_pg  # type: ignore[attr-defined]

    response = await service.probe()
    assert response.ok is False
    assert response.status == "error"
    assert "error" in response.checks["minio"]
    assert "error" in response.checks["postgres"]
