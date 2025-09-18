# Ingestion Service (Local)

Rebuild of the GOES/MRMS/NEXRAD ingestion pipelines. This service will replace the AWS Lambda functions.

## Planned Features
- Shared FetchWithRetry helper using `httpx`.
- Modular workers for GOES, MRMS, NEXRAD, Alerts.
- Schedules defined via APScheduler (cron-style).
- Manual trigger endpoints via FastAPI for ad-hoc processing.
- Writes outputs to MinIO buckets (`derived/`, `indices/`).

## TODO
- Design configuration schema (`config/ingestion.yml`).
- Port proven parsing logic from legacy handlers (after unit tests exist).
- Implement integration tests against MinIO (use docker compose profile).
