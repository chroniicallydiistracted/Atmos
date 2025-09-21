# Migration Log

Purpose: Track all changes during the AWS → local migration. Each entry includes date, summary, files changed, and rationale.

## 2025-09-16

### Core slice scaffolding
- Added a minimal API service (FastAPI) with `/healthz` probing MinIO and Postgres.
  - Files:
    - `local/services/api/Dockerfile`
    - `local/services/api/requirements.txt`
    - `local/services/api/src/main.py`
    - `local/services/api/.dockerignore`
  - Rationale: Establish a simple, testable endpoint to validate core dependencies.

- Updated `local/docker-compose.yml` to define a `core` profile and a MinIO init job.
  - Changes:
    - Marked `reverse-proxy`, `object-store`, `object-store-init`, `postgres`, `basemap`, `api`, `frontend` with profile `core`.
    - Added `object-store-init` using `minio/mc` to create buckets: `raw`, `derived`, `tiles`, `logs`.
    - `api` now depends on `postgres` (instead of `basemap`).
  - Rationale: Allow bringing up a minimal working stack and ensure object store buckets exist.

- Extended `local/config/.env.example` with additional variables.
  - Additions: `MINIO_ENDPOINT`, `S3_BUCKET_*`, `POSTGRES_HOST`, `DATABASE_URL`, `API_HOST`.
  - Rationale: Centralize configuration and simplify service connectivity.

- Created `local/scripts/bootstrap.sh` helper.
  - Rationale: Optional local convenience to initialize buckets when running without compose job.

### Next up
- Bring the core profile up and verify `/healthz` returns ok for both MinIO and Postgres.
- Decide whether to expose MinIO via Caddy under `/object-store` (already proxied) for UI access.
- Begin refactoring ingestion services to target MinIO endpoint instead of AWS S3.

### No-AWS policy + API refactor
- Policy: Created `local/docs/no-aws-policy.md` declaring no AWS services or SDKs moving forward; list of forbidden items and allowed local alternatives.
- API: Removed `boto3` dependency and switched to MinIO Python SDK in `/healthz` connectivity check.
  - Files:
    - `local/services/api/requirements.txt` (replace `boto3` with `minio`)
    - `local/services/api/src/main.py` (use `Minio` client for `list_buckets`)
  - Rationale: Align with local-first policy and remove AWS SDK usage.

## 2025-09-18

### Repository assessment and prioritization
- Completed repo-wide review of the local stack: `local/services/ingestion` runs the NEXRAD job via the legacy handler with injected MinIO/S3 clients, and `local/services/api` now exposes `/healthz` plus `/timeline/{layer}` sourcing MinIO indices.
- Confirmed `local/docker-compose.yml` brings up the core slice (Caddy, MinIO, Postgres, API) but basemap, frontend, and monitoring directories remain scaffolds without runnable code.
- Identified Milestone 2 blockers in `docs/stack-plan.md`: GOES ingestion, automated scheduling, and MinIO-backed tests are still missing; timeline indices will stay empty until additional jobs publish metadata.

### Implementation
- Added `GoesIngestion` job under `local/services/ingestion/src/atmos_ingestion/jobs/goes.py`, exposing `/trigger/goes` with configurable band/sector handling and unit coverage.
- Refactored `services/goes-prepare/handler.py` to accept injected S3 clients/bucket names so the pipeline can target MinIO instead of AWS directly.
- Updated ingestion FastAPI models, docs (`local/docs/api-contract.md`), and stack plan to reflect GOES support; extended tests to ensure the API delegates to the new job.
- Rebuilt the API gateway as a modular FastAPI app with versioned routes (`/v1/healthz`, `/v1/timeline/{layer}`, `/v1/trigger/*`), shared services, and pytest coverage in `local/services/api/tests`.
- Scaffolded a Vite + React frontend (`local/services/frontend`) with health, timeline, and trigger consoles plus Vitest smoke coverage.
- Added shared tooling: compose hot-reload for API/frontend, MinIO/Postgres seed scripts (`local/scripts/seed_*`), and a `local/scripts/test.sh` helper to run unit tests.
- Introduced `local/scripts/dev-stack.sh` and `local/docs/run-dev.md` so the API, ingestion, and frontend services can be launched together with one command; compose now exposes ingestion on `8084` for manual testing.
- Replaced the basemap placeholder with a PMTiles-serving Express service (`local/services/basemap`) that offers `/healthz`, `/pmtiles`, and byte-range streaming; compose mounts `local/data/basemaps` and exposes port `8082` for the frontend.
- Rebuilt the frontend experience around a full-screen MapLibre basemap with layer controls, timeline scrubber, location search, and alert panel; removed the card dashboard in favor of an operational-style overlay UI.

### Next up
- Expand the ingestion catalogue with MRMS and Alerts jobs following the same client-injection pattern.
- Introduce APScheduler wiring for automated cadences and validate idempotent behaviour.
- Add MinIO-backed integration tests (compose `ingestion` profile) to exercise GOES/NEXRAD pipelines end-to-end.
