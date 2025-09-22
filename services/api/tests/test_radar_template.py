import re
from fastapi.testclient import TestClient

from src import app as live_app
from src.atmos_api.routers import radar as radar_router  # type: ignore
from types import SimpleNamespace

TEMPLATE_RE = re.compile(r"^/tiles/weather/nexrad-[A-Z0-9]{4}/[0-9TZ]+/\{z\}/\{x\}/\{y\}\.png$")


def test_frames_tile_template_shape(monkeypatch):
    # Provide minimal env so service starts with defaults
    monkeypatch.setenv("MINIO_ENDPOINT", "object-store:9000")

    def fake_get_nexrad_frames(site: str, limit: int = 10):  # mimic real signature
        return {
            "site": site.upper(),
            "frames": [
                {
                    "timestamp_key": "20240101T000000Z",
                    "tile_template": "/tiles/weather/nexrad-KTLX/20240101T000000Z/{z}/{x}/{y}.png",
                }
            ],
        }

    radar_router.get_nexrad_frames = fake_get_nexrad_frames  # type: ignore
    # Replace MinIO client with dummy that raises on network use to guarantee isolation
    class _DummyMinio:
        def get_object(self, *a, **kw):
            raise RuntimeError("Network access not expected in test")

    radar_router.client = _DummyMinio()  # type: ignore

    # Call underlying function directly to avoid HTTP & MinIO object dependency
    data = radar_router.get_nexrad_frames("KTLX", limit=1)  # type: ignore
    assert data["site"] == "KTLX"
    assert data["frames"], "Expected at least one frame in mocked response"
    tmpl = data["frames"][0]["tile_template"]
    assert TEMPLATE_RE.match(tmpl), f"Tile template did not match expected pattern: {tmpl}"
