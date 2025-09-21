import pytest

from src.atmos_api.config import Settings
from src.atmos_api.services.timeline import TimelineService


class _FakeObject:
    def __init__(self, object_name: str):
        self.object_name = object_name


class _FakeClient:
    def __init__(self, objects):
        self._objects = objects

    def list_objects(self, bucket, prefix, recursive):
        assert bucket == "derived"
        assert prefix == "indices/goes/"
        assert recursive is True
        for obj in self._objects:
            yield obj


@pytest.mark.asyncio
async def test_timeline_lists_entries():
    settings = Settings(S3_BUCKET_DERIVED="derived")
    fake_objects = [
        _FakeObject("indices/goes/2024-09-18/index.json"),
        _FakeObject("indices/goes/subdir/extra.json"),
        _FakeObject("indices/goes/"),
    ]
    service = TimelineService(settings, minio_factory=lambda: _FakeClient(fake_objects))

    response = await service.list_entries("goes")
    assert response.layer == "goes"
    assert response.count == 2
    assert response.entries == ["2024-09-18/index.json", "subdir/extra.json"]


@pytest.mark.asyncio
async def test_timeline_empty_layer_raises():
    service = TimelineService(Settings())
    with pytest.raises(ValueError):
        await service.list_entries("")
