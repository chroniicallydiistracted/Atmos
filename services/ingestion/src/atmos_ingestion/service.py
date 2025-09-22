"""Service layer that exposes ingestion jobs to the API."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from .clients import ClientBundle
from .config import IngestionSettings
from .jobs.goes import GoesIngestion
from .jobs.nexrad_level2 import run_nexrad_level2


class IngestionService:
    """Coordinate ingestion jobs and expose async wrappers for FastAPI."""

    def __init__(self, settings: IngestionSettings):
        self._settings = settings
        self._clients = ClientBundle(settings)
        self._executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self._goes = GoesIngestion(settings, self._clients)

    async def run_nexrad(self, site: str | None, target_time: datetime | None) -> dict[str, Any]:
        # Use the unified NEXRAD Level 2 implementation with single frame
        loop = asyncio.get_running_loop()
        def _runner() -> dict[str, Any]:
            return run_nexrad_level2(site or self._settings.default_site,
                                   self._settings.default_minutes_lookback, 1)
        return await loop.run_in_executor(self._executor, _runner)

    async def run_nexrad_frames(self, site: str, frames: int, lookback_minutes: int) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        def _runner() -> dict[str, Any]:
            return run_nexrad_level2(site, lookback_minutes, frames)
        return await loop.run_in_executor(self._executor, _runner)

    async def run_goes(
        self,
        band: int | None,
        sector: str | None,
        target: datetime | str | None,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()

        def _runner() -> dict[str, Any]:
            return self._goes.run(band, sector, target)

        return await loop.run_in_executor(self._executor, _runner)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


__all__ = ["IngestionService"]
