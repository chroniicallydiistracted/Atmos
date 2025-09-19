"""GOES ABI ingestion pipeline adapted for the local stack."""
from __future__ import annotations

from datetime import datetime, timezone
from importlib import util
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..clients import ClientBundle
from ..config import IngestionSettings


def _load_goes_handler_module():
    here = Path(__file__).resolve()
    for candidate in here.parents:
        module_path = candidate / "services" / "goes-prepare" / "handler.py"
        if module_path.exists():
            spec = util.spec_from_file_location("legacy_goes_handler", module_path)
            if spec and spec.loader:
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[attr-defined]
                return module
    raise RuntimeError("Unable to locate legacy GOES handler module")


_LEGACY_HANDLER = _load_goes_handler_module()

extract_goes_timestamp = _LEGACY_HANDLER.extract_goes_timestamp  # type: ignore[attr-defined]
find_goes_file_for_time = _LEGACY_HANDLER.find_goes_file_for_time  # type: ignore[attr-defined]
find_latest_goes_data = _LEGACY_HANDLER.find_latest_goes_data  # type: ignore[attr-defined]
process_goes_file = _LEGACY_HANDLER.process_goes_file  # type: ignore[attr-defined]

TimestampInput = Optional[Union[datetime, str]]


class GoesIngestion:
    """Coordinate GOES ingestion using the shared legacy processing logic."""

    def __init__(self, settings: IngestionSettings, clients: ClientBundle):
        self._settings = settings
        self._clients = clients

    def _resolve_band(self, band: Optional[int]) -> int:
        return band or self._settings.goes_default_band

    def _resolve_sector(self, sector: Optional[str]) -> str:
        value = (sector or self._settings.goes_default_sector).strip()
        if not value:
            raise ValueError("Sector must not be empty")
        return value.upper()

    def _normalise_timestamp(self, timestamp: datetime) -> datetime:
        if timestamp.tzinfo is not None:
            return timestamp.astimezone(timezone.utc).replace(tzinfo=None)
        return timestamp

    def _format_timestamp(self, timestamp: datetime) -> str:
        return timestamp.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    def run(self, band: Optional[int], sector: Optional[str], target: TimestampInput) -> Dict[str, Any]:
        resolved_band = self._resolve_band(band)
        resolved_sector = self._resolve_sector(sector)
        bucket = self._settings.goes_bucket

        source_client = self._clients.source
        derived_client = self._clients.derived

        use_latest = target is None
        resolved_request_time: Optional[datetime] = None

        if isinstance(target, str):
            if target.lower() != "latest":
                raise ValueError("timestamp string must be 'latest'")
            use_latest = True
        elif isinstance(target, datetime):
            resolved_request_time = self._normalise_timestamp(target)

        if use_latest:
            timestamp, goes_key = find_latest_goes_data(
                resolved_band,
                resolved_sector,
                bucket=bucket,
                s3_client=source_client,
            )
            if timestamp is None or goes_key is None:
                raise FileNotFoundError(
                    f"No GOES data available for band {resolved_band} sector {resolved_sector}"
                )
        else:
            if resolved_request_time is None:
                raise ValueError("A timestamp must be supplied when not requesting latest data")
            goes_key = find_goes_file_for_time(
                resolved_band,
                resolved_sector,
                resolved_request_time,
                bucket=bucket,
                s3_client=source_client,
            )
            if goes_key is None:
                raise FileNotFoundError(
                    f"GOES file not found for {resolved_sector} at {resolved_request_time.isoformat()}"
                )
            timestamp = extract_goes_timestamp(goes_key.split('/')[-1])
            if timestamp is None:
                timestamp = resolved_request_time

        timestamp = self._normalise_timestamp(timestamp)

        result = process_goes_file(
            resolved_band,
            resolved_sector,
            timestamp,
            goes_key,
            source_bucket=bucket,
            source_s3_client=source_client,
            derived_s3_client=derived_client,
            derived_bucket=self._settings.derived_bucket,
        )

        requested_marker = (
            "latest"
            if use_latest
            else self._format_timestamp(resolved_request_time or timestamp)
        )

        result.update(
            {
                "band": resolved_band,
                "sector": resolved_sector,
                "requested_time": requested_marker,
                "ingested_time": self._format_timestamp(timestamp),
            }
        )
        return result


__all__ = ["GoesIngestion"]
