"""GOES ABI ingestion pipeline adapted for the local stack."""
from __future__ import annotations

from datetime import UTC, datetime
from importlib import util
from pathlib import Path
from typing import Any

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
    # Graceful degradation: allow module import to succeed without legacy handler so tests
    # that patch processing functions or ignore GOES logic can still run.
    return None


_LEGACY_HANDLER = _load_goes_handler_module()

if _LEGACY_HANDLER is not None:  # Production path
    extract_goes_timestamp = _LEGACY_HANDLER.extract_goes_timestamp  # type: ignore[attr-defined]
    find_goes_file_for_time = _LEGACY_HANDLER.find_goes_file_for_time  # type: ignore[attr-defined]
    find_latest_goes_data = _LEGACY_HANDLER.find_latest_goes_data  # type: ignore[attr-defined]
    process_goes_file = _LEGACY_HANDLER.process_goes_file  # type: ignore[attr-defined]
else:  # Fallback stubs used in tests when handler absent
    def _missing(*_a, **_k):  # pragma: no cover - executed only when handler missing
        raise RuntimeError("Legacy GOES handler module not available; functionality disabled.")

    def extract_goes_timestamp(*_a, **_k):  # type: ignore
        return None
    find_goes_file_for_time = _missing  # type: ignore
    def find_latest_goes_data(*_a, **_k):  # type: ignore
        return (None, None)
    process_goes_file = _missing  # type: ignore

TimestampInput = datetime | str | None


class GoesIngestion:
    """Coordinate GOES ingestion using the shared legacy processing logic."""

    def __init__(self, settings: IngestionSettings, clients: ClientBundle):
        self._settings = settings
        self._clients = clients

    def _resolve_band(self, band: int | None) -> int:
        return band or self._settings.goes_default_band

    def _resolve_sector(self, sector: str | None) -> str:
        value = (sector or self._settings.goes_default_sector).strip()
        if not value:
            raise ValueError("Sector must not be empty")
        return value.upper()

    def _normalise_timestamp(self, timestamp: datetime) -> datetime:
        if timestamp.tzinfo is not None:
            return timestamp.astimezone(UTC).replace(tzinfo=None)
        return timestamp

    def _format_timestamp(self, timestamp: datetime) -> str:
        return timestamp.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")

    def run(self, band: int | None, sector: str | None, target: TimestampInput) -> dict[str, Any]:
        resolved_band = self._resolve_band(band)
        resolved_sector = self._resolve_sector(sector)
        bucket = self._settings.goes_bucket

        source_client = self._clients.source
        derived_client = self._clients.derived

        use_latest = target is None
        resolved_request_time: datetime | None = None

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
