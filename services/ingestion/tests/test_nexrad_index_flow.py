"""Unit test for NEXRAD index update logic with mocked dependencies.

Focus: list -> dedupe -> process -> index persistence without invoking heavy radar parsing.
"""
from __future__ import annotations

import datetime as dt


def _build_fake_s3(keys):
    class _Paginator:
        def paginate(self, **_kwargs):  # noqa: D401
            yield {"Contents": [{"Key": k} for k in keys]}

    class _Client:
        def get_paginator(self, _name):
            return _Paginator()

    return _Client()


class _MemObj:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):  # MinIO style
        return self._data


class _MemMinio:
    def __init__(self):
        self.store: dict[str, bytes] = {}

    # get_object / put_object mimic subset used by nexrad code
    def get_object(self, bucket: str, key: str):  # noqa: D401
        return _MemObj(self.store[f"{bucket}/{key}"])

    def put_object(self, bucket: str, key: str, data, length: int, content_type: str):  # noqa: D401
        self.store[f"{bucket}/{key}"] = data.read()


def test_run_nexrad_level2_index_flow(monkeypatch):
    # Import the module directly via spec to avoid side-effects from goes handler resolution
    import importlib.util
    import pathlib
    import sys
    base = pathlib.Path(__file__).resolve().parents[1] / "src" / "atmos_ingestion" / "jobs" / "nexrad_level2.py"
    spec = importlib.util.spec_from_file_location("nexrad_level2", base)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    bucket = module.DERIVED_BUCKET
    mem_minio = _MemMinio()
    monkeypatch.setattr(module, "minio_client", mem_minio)

    # Freeze time by constructing keys for today
    now = dt.datetime.utcnow()
    date_prefix = f"{now:%Y/%m/%d}"
    site = "KTLX"
    # Create two volume file keys with distinct timestamps
    keys = [
        f"{date_prefix}/{site}/{site}{now:%Y%m%d_%H%M%S}_V06",  # second precision
        f"{date_prefix}/{site}/{site}{(now - dt.timedelta(seconds=60)):%Y%m%d_%H%M%S}_V06",
    ]

    fake_s3 = _build_fake_s3(keys)
    monkeypatch.setattr(module, "_get_s3", lambda: fake_s3)

    # Stub process_volume so we don't depend on pyart / rasterio heavy stack
    def _fake_process(site_arg: str, key: str):
        ts_key = module._timestamp_key(site_arg, key)  # noqa: SLF001
        return {
            "timestamp_key": ts_key,
            "cog_key": f"nexrad/{site_arg}/{ts_key}/tilt0_reflectivity.tif",
            "meta_key": f"nexrad/{site_arg}/{ts_key}/tilt0_reflectivity.json",
            "tile_template": f"/tiles/weather/nexrad-{site_arg}/{ts_key}/{{z}}/{{x}}/{{y}}.png",
        }

    monkeypatch.setattr(module, "process_volume", _fake_process)

    result = module.run_nexrad_level2(site, lookback_minutes=120, max_new=5)
    assert result["added"] == 2
    assert result["total_frames"] == 2
    # Frames should be sorted oldest -> newest, newest last
    ts_keys = [f["timestamp_key"] for f in result["frames"]]
    assert ts_keys == sorted(ts_keys)

    # Second invocation should add zero (idempotent)
    result2 = module.run_nexrad_level2(site, lookback_minutes=120, max_new=5)
    assert result2["added"] == 0
    assert result2["total_frames"] == 2

    # Ensure index file persisted in in-memory store
    stored_keys = list(mem_minio.store.keys())
    assert any(k.startswith(f"{bucket}/indices/radar/nexrad/{site}/frames.json") for k in stored_keys)
