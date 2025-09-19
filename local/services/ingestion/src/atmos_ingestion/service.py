"""Service layer that exposes ingestion jobs to the API."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, Optional, Union

from .clients import ClientBundle
from .config import IngestionSettings
from .jobs.goes import GoesIngestion
from .jobs.nexrad import NexradIngestion


class IngestionService:
    """Coordinate ingestion jobs and expose async wrappers for FastAPI."""

    def __init__(self, settings: IngestionSettings):
        self._settings = settings
        self._clients = ClientBundle(settings)
        self._executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self._nexrad = NexradIngestion(settings, self._clients)
        self._goes = GoesIngestion(settings, self._clients)

    async def run_nexrad(self, site: Optional[str], target_time: Optional[datetime]) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()

        def _runner() -> Dict[str, Any]:
            return self._nexrad.run(site, target_time)

        return await loop.run_in_executor(self._executor, _runner)

    async def run_goes(
        self,
        band: Optional[int],
        sector: Optional[str],
        target: Optional[Union[datetime, str]],
    ) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()

        def _runner() -> Dict[str, Any]:
            return self._goes.run(band, sector, target)

        return await loop.run_in_executor(self._executor, _runner)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


__all__ = ["IngestionService"]
