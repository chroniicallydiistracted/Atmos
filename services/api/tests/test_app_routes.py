from fastapi.testclient import TestClient
import pytest

from src import app as live_app
from src.atmos_api.deps import (
    get_health_service,
    get_timeline_service,
    get_trigger_service,
)
from src.atmos_api.schemas import (
    HealthResponse,
    TimelineResponse,
    TriggerCatalogResponse,
    TriggerResponse,
)


class _StubHealthService:
    async def probe(self) -> HealthResponse:
        return HealthResponse(checks={"minio": "ok"}, ok=True)


class _StubTimelineService:
    async def list_entries(self, layer: str) -> TimelineResponse:
        return TimelineResponse(layer=layer, count=1, entries=["example.json"])


class _StubTriggerService:
    def list_jobs(self) -> TriggerCatalogResponse:
        return TriggerCatalogResponse(jobs=[])

    async def trigger(self, job: str, parameters):
        return TriggerResponse(job=job, detail={"echo": parameters})


@pytest.fixture
def client():
    app = live_app
    app.dependency_overrides[get_health_service] = lambda: _StubHealthService()
    app.dependency_overrides[get_timeline_service] = lambda: _StubTimelineService()
    app.dependency_overrides[get_trigger_service] = lambda: _StubTriggerService()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_route(client):
    response = client.get("/v1/healthz")
    assert response.status_code == 200
    assert response.json()["checks"]["minio"] == "ok"


def test_timeline_route(client):
    response = client.get("/v1/timeline/goes")
    assert response.status_code == 200
    payload = response.json()
    assert payload["layer"] == "goes"
    assert payload["entries"] == ["example.json"]


def test_trigger_route(client):
    response = client.post("/v1/trigger/nexrad", json={"parameters": {"site": "KTLX"}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["job"] == "nexrad"
    assert payload["detail"]["echo"] == {"site": "KTLX"}
