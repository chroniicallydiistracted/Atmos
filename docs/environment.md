# Environment Variable Reference

This document enumerates environment variables consumed by the current local stack. It consolidates settings used by API, ingestion, tiler, and related scripts. Variables are typically loaded via `docker-compose` `env_file: ./config/.env`.

Legend: `(deprecated)` means accepted for backward compatibility but should be migrated off.

## Core Object Store / MinIO
| Variable | Service(s) | Default | Notes |
|----------|------------|---------|-------|
| `MINIO_ENDPOINT` | api, ingestion, tiler | `http://object-store:9000` | Full URL w/ scheme. |
| `MINIO_ROOT_USER` | api, ingestion, tiler | `localminio` | Access key. |
| `MINIO_ROOT_PASSWORD` | api, ingestion, tiler | `change-me-now` | Secret key; change in non-dev. |
| `MINIO_SECURE` | api, ingestion | `false` | Forces HTTPS if true. |
| `S3_BUCKET_DERIVED` | api, ingestion, tiler, scripts | `derived` | Canonical derived outputs bucket. |
| `DERIVED_BUCKET_NAME` | api (radar router), ingestion job, tiler | (none) | (deprecated alias) Triggers deprecation warning if used. |
| `S3_BUCKET_RAW` | ingestion | `raw` | Created by bootstrap (compose init). |
| `S3_BUCKET_TILES` | potential future | `tiles` | Reserved. |
| `S3_BUCKET_LOGS` | potential future | `logs` | Reserved. |

## Database
| Variable | Service | Default | Notes |
|----------|---------|---------|-------|
| `DATABASE_URL` | api | `postgresql://osm:change-me-too@postgres:5432/osm` | Connection string. |
| `POSTGRES_USER` | postgres container | `osm` | Ref in health checks. |
| `POSTGRES_PASSWORD` | postgres container | (set in .env) | Required. |
| `POSTGRES_DB` | postgres container | `osm` | Database name. |
| `POSTGRES_PORT` | postgres container | `5432` | Port. |

## API Service
| Variable | Default | Notes |
|----------|---------|-------|
| `API_TITLE` | `Atmos API` | UI metadata. |
| `API_VERSION` | `0.2.0` | Reported via OpenAPI. |
| `INGESTION_BASE_URL` | `http://ingestion:8084` | Downstream trigger target. |
| `API_HTTP_TIMEOUT_SECONDS` | `30.0` | httpx client timeout. |
| `API_CORS_ORIGINS` | `http://localhost:4173` | Comma-separated list. |

## Ingestion Service
| Variable | Default | Notes |
|----------|---------|-------|
| `NEXRAD_BUCKET_NAME` | `unidata-nexrad-level2` | Public source bucket. |
| `NEXRAD_SOURCE_REGION` | `us-east-1` | AWS region for source bucket. |
| `NEXRAD_DEFAULT_SITE` | `KTLX` | Fallback site. |
| `NEXRAD_DEFAULT_MINUTES_LOOKBACK` | `10` | Lookback when timestamp omitted. |
| `GOES_SOURCE_BUCKET` | `noaa-goes16` | Public GOES bucket. |
| `GOES_DEFAULT_BAND` | `13` | Default ABI band. |
| `GOES_DEFAULT_SECTOR` | `CONUS` | Default sector. |
| `INGESTION_ENABLE_SCHEDULER` | `false` | Future scheduling. |
| `INGESTION_SCHEDULER_INTERVAL_MINUTES` | `6` | Interval for scheduler. |
| `INGESTION_MAX_WORKERS` | `2` | Concurrency limit. |

## Tiler
| Variable | Default | Notes |
|----------|---------|-------|
| `MINIO_ENDPOINT` | see above | Used to sign presigned URLs. |
| `MINIO_ROOT_USER` | see above |  |
| `MINIO_ROOT_PASSWORD` | see above |  |
| `S3_BUCKET_DERIVED` | `derived` | Bucket for COG assets. |

## Frontend (Vite)
Variables are prefixed with `VITE_` to be exposed to client code.
| Variable | Description |
|----------|-------------|
| `VITE_API_BASE` | Override API base path (default `/api` proxied). |
| `VITE_NEXRAD_SITE` | Default radar site if user hasn't selected one. |
| `VITE_BASEMAP_PM` | PMTiles archive URL for base map. |
| `VITE_BICYCLE_PM` | Optional PMTiles URL for bicycle layer. |
| `VITE_CYCLOSM_TILE_TEMPLATE` | Hosted CyclOSM raster tile template (e.g., `https://{s}.example.com/tiles/cyclosm/{z}/{x}/{y}.png`). |
| `VITE_CYCLOSM_TILE_SUBDOMAINS` | Comma-separated list like `a,b,c`. |
| `VITE_TILE_BASE` | Override base URL for tiler (default `http://localhost:8083`). |

## Deprecated / Aliases
| Alias | Canonical | Action |
|-------|-----------|--------|
| `DERIVED_BUCKET_NAME` | `S3_BUCKET_DERIVED` | Will log warning; migrate to canonical. |

## Not Implemented (Removed From README)
The earlier README referenced variables controlling frame counts and grid resolution (`NEXRAD_MAX_FRAMES`, etc.). These are not currently implemented in code. Add them only after introducing corresponding logic.

## Usage Notes
1. Compose already injects variables via `env_file: ./config/.env`. The internal autodiscovery only matters for non-compose execution.
2. When switching buckets or endpoints, restart all dependent services (ingestion, api, tiler, frontend).
3. For production, rotate `MINIO_ROOT_PASSWORD` and consider enabling TLS + `MINIO_SECURE=true`.

---
Generated during remediation pass to unify environment configuration.
