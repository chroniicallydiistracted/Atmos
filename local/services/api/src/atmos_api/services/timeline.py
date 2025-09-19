"""Timeline querying helpers."""
from __future__ import annotations

from typing import Callable, List

from fastapi.concurrency import run_in_threadpool

from ..clients import create_minio_client
from ..config import Settings
from ..schemas import TimelineResponse


class TimelineService:
    """Read timeline indices from MinIO."""

    def __init__(
        self,
        settings: Settings,
        *,
        minio_factory: Callable[[], object] | None = None,
    ) -> None:
        self._settings = settings
        self._minio_factory = minio_factory or (lambda: create_minio_client(settings))

    async def list_entries(self, layer: str) -> TimelineResponse:
        if not layer:
            raise ValueError("layer must not be empty")

        def _list() -> List[str]:
            client = self._minio_factory()
            prefix = f"indices/{layer}/"
            entries: List[str] = []
            for obj in client.list_objects(self._settings.derived_bucket, prefix=prefix, recursive=True):
                name = getattr(obj, "object_name", "")
                if not name.startswith(prefix) or name.endswith("/"):
                    continue
                entries.append(name[len(prefix) :])
            entries.sort()
            return entries

        objects = await run_in_threadpool(_list)
        return TimelineResponse(layer=layer, count=len(objects), entries=objects)


__all__ = ["TimelineService"]
