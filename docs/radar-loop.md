# NEXRAD Multi-Frame Radar Loop

This document captures the implemented real (non-synthetic) Level II radar ingestion + animation loop pipeline.

## Pipeline Summary

1. Trigger: `POST /v1/trigger/nexrad-frames` with JSON body `{ "parameters": { "site": "KTLX", "frames": 4, "lookback_minutes": 60 } }`.
2. Ingestion service lists recent public AWS NEXRAD Level II volume files (unsigned) within the lookback window.
3. New volumes are converted via Py-ART to a 2D reflectivity grid and written as COGs under `nexrad/{SITE}/{TIMESTAMP}/tilt0_reflectivity.tif` (bucket: derived).
4. Frame metadata accumulated in rolling index: `indices/radar/nexrad/{SITE}/frames.json` (capped by `NEXRAD_MAX_FRAMES`).
5. API endpoint `GET /v1/radar/nexrad/{SITE}/frames` returns recent frame objects (each includes `timestamp_key` and tile template).
6. Frontend periodically triggers ingestion + fetches frames; map swaps raster source tiles to animate.

## Key Paths

| Component | File |
|-----------|------|
| Multi-frame job | `local/services/ingestion/src/atmos_ingestion/jobs/nexrad_level2.py` |
| Trigger registration | `local/services/api/src/atmos_api/services/triggers.py` |
| Frames endpoint | `local/services/api/src/atmos_api/routers/radar.py` |
| Frontend frames hook | `local/services/frontend/src/hooks/useNexradFrames.ts` |
| Validation script (headless) | `web/scripts/validate_nexrad_loop.ts` |

## Environment Variables (excerpt)

* `NEXRAD_MAX_FRAMES` – rolling window size.
* `NEXRAD_LOOKBACK_MINUTES` – default volume search window.
* `NEXRAD_GRID_RES_KM`, `NEXRAD_GRID_RADIUS_KM` – gridding parameters.

## Tile Template

`/tiles/weather/nexrad-{SITE}/{TIMESTAMP_KEY}/{z}/{x}/{y}.png`

`TIMESTAMP_KEY` format: `YYYYMMDDTHHMMSSZ` (Zulu).

## Notes

* Current CRS is placeholder WebMercator grid; future improvement is proper geographic reprojection.
* Frames ingestion is idempotent; existing timestamps are skipped.
* Frontend uses a simple modulo animation loop (400 ms per frame).
