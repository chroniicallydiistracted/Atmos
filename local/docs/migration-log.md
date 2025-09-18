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
