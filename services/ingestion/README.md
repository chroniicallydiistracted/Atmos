# Ingestion Service (Local)

Rebuild of the GOES/MRMS/NEXRAD ingestion pipelines. This service will replace the AWS Lambda functions.

## What Exists Now

- FastAPI application (`src/main.py`) exposing `/trigger/nexrad` and `/healthz`.
- `NexradIngestion` job reusing the proven Level II processing logic from
  `services/radar-prepare/handler.py` with injectable S3 clients.
- `GoesIngestion` job that pulls the ABI handler from `services/goes-prepare/handler.py`
  and writes outputs to the local MinIO buckets.
- Environment-driven configuration via `pydantic-settings` (`IngestionSettings`).
- Thin boto3 client factory that talks to NOAA's Open Data bucket for source
  volumes and the local MinIO deployment for derived outputs.
- Thread-pooled execution so CPU intensive conversions run off the event loop.
- Smoke tests (`tests/test_app.py`) covering health endpoint wiring.

## Running Locally

```bash
cd /home/andre/Atmos
python -m uvicorn local.services.ingestion.src.main:app --host 0.0.0.0 --port 8084
```

Ensure MinIO is running (see `local/docker-compose.yml` core profile) and that
the `derived` bucket exists. The `/trigger/nexrad` endpoint accepts JSON payloads:

```json
{
  "site": "KTLX",
  "timestamp": "2024-07-12T18:05:00Z"
}
```

If `timestamp` is omitted the service looks back `10` minutes (configurable via
`NEXRAD_DEFAULT_MINUTES_LOOKBACK`).

## Next Steps

- Expand job catalogue to cover MRMS and Alerts using the same pattern.
- Introduce optional APScheduler wiring for fully automated cadences.
- Add MinIO integration tests behind a docker-compose profile.
- Evaluate lighter-weight alternatives such as consuming Level III mosaics when
  super-resolution detail is not required.

## Anonymous Public Data Access Policy

The local stack enforces a strict policy of **no embedded AWS credentials and no requester-pays flags** for
upstream public datasets (e.g. NEXRAD Level II). The radar job now:

- Always uses a single unsigned (anonymous) boto3 S3 client.
- Targets the public bucket `unidata-nexrad-level2`.
- Surfaces any `AccessDenied` or other S3 errors immediately as `RadarSourceAccessError` without attempting
  a signed retry.

Rationale:

1. Guarantees reproducible local development without cloud account coupling.
2. Fails fast if the upstream bucket policy ever changes, forcing an explicit decision to revise policy.
3. Avoids silent divergence between environments with and without credentials configured.

If future requirements mandate authenticated access, reintroduce a credential-aware client behind a clearly
documented feature flag (e.g. `NEXRAD_ALLOW_SIGNED=1`) so the default remains anonymous.
