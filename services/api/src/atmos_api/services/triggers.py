"""Trigger orchestration for ingestion jobs."""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..config import Settings
from ..schemas import TriggerCatalogEntry, TriggerCatalogResponse, TriggerResponse


@dataclass
class TriggerTarget:
    path: str
    description: str = ""


class UnknownJobError(Exception):
    """Raised when a trigger is requested for an unknown job."""


class TriggerInvocationError(Exception):
    """Raised when the downstream ingestion service responds with an error."""

    def __init__(self, job: str, status_code: int, detail: object):
        super().__init__(f"Trigger for '{job}' failed with status {status_code}")
        self.job = job
        self.status_code = status_code
        self.detail = detail


class TriggerService:
    """Proxy trigger requests to the ingestion service."""

    def __init__(
        self,
        settings: Settings,
        *,
    transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport
        self._registry: dict[str, TriggerTarget] = {}
        self.register_job("nexrad", "/trigger/nexrad", description="NEXRAD Level II radar ingestion")
        self.register_job(
            "nexrad-frames",
            "/trigger/nexrad/frames",
            description="NEXRAD Level II multi-frame ingestion (build animation loop)",
        )
        self.register_job("goes", "/trigger/goes", description="GOES ABI ingestion")

    def register_job(self, job: str, path: str, *, description: str = "") -> None:
        self._registry[job] = TriggerTarget(path=path, description=description)

    def list_jobs(self) -> TriggerCatalogResponse:
        return TriggerCatalogResponse(
            jobs=[
                TriggerCatalogEntry(job=name, description=target.description)
                for name, target in sorted(self._registry.items())
            ]
        )

    async def trigger(self, job: str, parameters: dict[str, object] | None = None) -> TriggerResponse:
        target = self._registry.get(job)
        if target is None:
            raise UnknownJobError(job)

        payload = parameters or {}

        async with httpx.AsyncClient(
            base_url=self._settings.ingestion_base_url,
            timeout=self._settings.http_client_timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post(target.path, json=payload)

        try:
            detail = response.json() if response.content else {}
        except ValueError:
            detail = {"raw": response.text}

        if response.is_error:
            raise TriggerInvocationError(job, response.status_code, detail)

        return TriggerResponse(job=job, detail=detail)


__all__ = ["TriggerService", "UnknownJobError", "TriggerInvocationError", "TriggerTarget"]
