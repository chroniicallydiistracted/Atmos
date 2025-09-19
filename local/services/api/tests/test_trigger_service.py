import json

import httpx
import pytest

from local.services.api.src.atmos_api.config import Settings
from local.services.api.src.atmos_api.services.triggers import (
    TriggerInvocationError,
    TriggerService,
    UnknownJobError,
)


@pytest.mark.asyncio
async def test_trigger_success():
    settings = Settings(INGESTION_BASE_URL="https://example.test")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/trigger/nexrad"
        payload = json.loads(request.content)
        assert payload["site"] == "KTLX"
        return httpx.Response(200, json={"status": "ok", "detail": {"site": "KTLX"}})

    transport = httpx.MockTransport(handler)
    service = TriggerService(settings, transport=transport)

    response = await service.trigger("nexrad", {"site": "KTLX"})
    assert response.job == "nexrad"
    assert response.detail["detail"]["site"] == "KTLX"


@pytest.mark.asyncio
async def test_trigger_unknown_job():
    settings = Settings()
    service = TriggerService(settings)

    with pytest.raises(UnknownJobError):
        await service.trigger("unknown", {})


@pytest.mark.asyncio
async def test_trigger_error_response():
    settings = Settings()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "failed"})

    transport = httpx.MockTransport(handler)
    service = TriggerService(settings, transport=transport)

    with pytest.raises(TriggerInvocationError) as exc:
        await service.trigger("nexrad", {})

    assert exc.value.status_code == 500
    assert exc.value.detail == {"error": "failed"}
