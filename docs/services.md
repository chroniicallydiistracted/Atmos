# Service Catalogue

This document enumerates the services under `services/`. Each is implemented (or planned) without AWS-specific assumptions.

## 1. object-store
- **Purpose**: Provide an S3-compatible interface using MinIO.
- **Inputs**: None (persistent volume mounted at `data/object-store`).
- **Outputs**: Accessible buckets `raw/`, `derived/`, `tiles/`, `logs/`.
- **Notes**: Configure via `config/minio.env`; use `mc` for admin tasks.

## 2. ingestion
- **Purpose**: Fetch NOAA datasets (GOES, MRMS, NEXRAD), normalize, write COGs/indices.
- **Tech**: Python 3.11 + FastAPI (for manual triggers) + APScheduler.
- **Outputs**: `derived/` bucket prefixes, metadata JSON.
- **Dependencies**: Object store, `config/ingestion.yml` for schedule and retention.

## 3. alerts
- **Purpose**: Fetch NWS alerts, generate vector tiles with Tippecanoe.
- **Tech**: Python + Tippecanoe container.
- **Outputs**: `tiles/alerts/{timestamp}/...`, updated `indices/` entry.

## 4. basemap
- **Purpose**: CyclOSM raster renderer backed by PostGIS.
- **Tech**: Node + Mapnik, Postgres/PostGIS (separate container `database`).
- **Outputs**: Raster tiles under `tiles/cyclosm/` and HTTP endpoint for direct render.
- **Dependencies**: PostGIS import process (`services/database-import`).

## 5. api
- **Purpose**: Expose unified HTTP API for frontend (health, timeline, triggers).
- **Tech**: FastAPI/Express (decision pending).
- **Dependencies**: Ingestion services, object store metadata.

## 6. frontend
- **Purpose**: React/MapLibre client served locally.
- **Tech**: Vite + React 18.
- **Dependencies**: API + tile endpoints; use environment config from `config/.env`.

## 7. monitoring
- **Purpose**: Prometheus, Grafana, Loki for metrics/logging.
- **Notes**: Optional first iteration; include compose profiles for toggling.

## 8. backup
- **Purpose**: Scheduled jobs to snapshot Postgres, object store, configs.
- **Implementation**: Bash + `restic` or `rsync` scripts under `scripts/`.

Each service lives under `services/<name>` with:
- `Dockerfile`
- `README.md`
- `src/` or equivalent code directory
- `config/` (service-specific)
- `tests/`

Document interfaces and environment variables inside each service before writing code.
