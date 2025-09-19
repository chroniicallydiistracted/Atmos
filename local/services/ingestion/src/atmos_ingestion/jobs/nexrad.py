"""NEXRAD Level II ingestion pipeline for the local stack."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import util
from pathlib import Path
from typing import Any, Dict, Optional

from ..clients import ClientBundle
from ..config import IngestionSettings


def _load_radar_handler():
    here = Path(__file__).resolve()
    for candidate in here.parents:
        module_path = candidate / "services" / "radar-prepare" / "handler.py"
        if module_path.exists():
            spec = util.spec_from_file_location("legacy_radar_handler", module_path)
            if spec and spec.loader:
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[attr-defined]
                return module
    raise RuntimeError("Unable to locate legacy radar handler module")


_RADAR_HANDLER = _load_radar_handler()
process_nexrad_file = _RADAR_HANDLER.process_nexrad_file  # type: ignore[attr-defined]


class NexradIngestion:
    """Coordinate the Level II processing flow using the shared legacy logic."""

    def __init__(self, settings: IngestionSettings, clients: ClientBundle):
        self._settings = settings
        self._clients = clients

    def _resolve_site(self, site: Optional[str]) -> str:
        return (site or self._settings.default_site).strip().upper()

    def _resolve_time(self, target: Optional[datetime]) -> datetime:
        if target is None:
            target = datetime.now(tz=timezone.utc) - timedelta(minutes=self._settings.default_minutes_lookback)
        if target.tzinfo is not None:
            target = target.astimezone(timezone.utc).replace(tzinfo=None)
        return target

    def run(self, site: Optional[str], target_time: Optional[datetime]) -> Dict[str, Any]:
        """Execute the ingestion job synchronously and return metadata about the outcome."""
        resolved_site = self._resolve_site(site)
        resolved_time = self._resolve_time(target_time)

        result = process_nexrad_file(
            resolved_site,
            resolved_time,
            source_s3_client=self._clients.source,
            derived_s3_client=self._clients.derived,
            derived_bucket=self._settings.derived_bucket,
        )
        result.update({
            "site": resolved_site,
            "requested_time": resolved_time.isoformat() + "Z",
        })
        return result


__all__ = ["NexradIngestion"]
