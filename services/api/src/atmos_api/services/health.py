"""Health probe helpers."""
from __future__ import annotations

from typing import Callable, Dict

from fastapi.concurrency import run_in_threadpool
import psycopg

from ..clients import create_minio_client
from ..config import Settings
from ..schemas import HealthResponse


class HealthService:
    """Perform health checks against core dependencies."""

    def __init__(
        self,
        settings: Settings,
        *,
        minio_factory: Callable[[], object] | None = None,
        postgres_dsn: str | None = None,
    ) -> None:
        self._settings = settings
        self._minio_factory = minio_factory or (lambda: create_minio_client(settings))
        self._postgres_dsn = postgres_dsn or settings.database_url

    async def probe(self) -> HealthResponse:
        checks: Dict[str, str] = {}

        try:
            client = self._minio_factory()

            def _check_minio() -> None:
                _ = next(iter(client.list_buckets()), None)

            await run_in_threadpool(_check_minio)
            checks["minio"] = "ok"
        except Exception as exc:  # pragma: no cover - defensive
            checks["minio"] = f"error: {exc}"

        try:
            await run_in_threadpool(self._check_postgres)
            checks["postgres"] = "ok"
        except Exception as exc:  # pragma: no cover - defensive
            checks["postgres"] = f"error: {exc}"

        overall = all(status == "ok" for status in checks.values())
        return HealthResponse(ok=overall, status="ok" if overall else "error", checks=checks)

    def _check_postgres(self) -> None:
        with psycopg.connect(self._postgres_dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                _ = cur.fetchone()


__all__ = ["HealthService"]
