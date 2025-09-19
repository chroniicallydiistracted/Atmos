# API Contract (Draft)

This document will define the HTTP interface exposed by the new API service. Populate with OpenAPI definitions as endpoints are implemented.

## Frontend API Gateway (FastAPI)

| Endpoint | Method | Description | Status |
| --- | --- | --- | --- |
| `/v1/healthz` | GET | Reports dependency health (MinIO, Postgres) via structured response. | ✅ Implemented (`local/services/api/src/atmos_api/routers/health.py`). |
| `/v1/timeline/{layer}` | GET | Lists indices beneath `indices/{layer}/` in the derived bucket. | ✅ Implemented; returns sorted keys without pagination. |
| `/v1/trigger` | GET | Enumerates registered ingestion jobs and descriptions. | ✅ Implemented; jobs sourced from in-process registry. |
| `/v1/trigger/{job}` | POST | Proxies trigger requests to the ingestion service (`/trigger/{job}`). | ✅ Implemented with downstream error handling. |
| `/tiles/...` | GET | Optional proxy to static/derived tiles for same-origin convenience. | ⏳ Pending. |

### `/v1/trigger/{job}` Payload

```json
{
  "parameters": { /* forwarded JSON payload */ }
}
```

### `/v1/trigger/{job}` Response

```json
{
  "job": "nexrad",
  "status": "ok",
  "detail": { /* ingestion response body */ }
}
```

## Ingestion Service API (FastAPI)

| Endpoint | Method | Description | Status |
| --- | --- | --- | --- |
| `/` | GET | Returns basic metadata pointing to docs. | ✅ Implemented. |
| `/healthz` | GET | Exposes configured MinIO and source bucket info for monitoring. | ✅ Implemented. |
| `/trigger/nexrad` | POST | Executes the Level II processing pipeline for the requested site/time. | ✅ Implemented (reuses legacy handler, writes to MinIO). |
| `/trigger/goes` | POST | Runs the GOES ABI ingestion pipeline for a specific band/sector or the latest scan. | ✅ Implemented, proxies to `GoesIngestion`. |

### Notes

- The ingestion service currently shells out CPU-intensive work on a local thread pool. For
  higher throughput consider migrating to a task queue or leveraging xradar's Dask support.
- Future triggers (MRMS, Alerts) will follow the same pattern and the gateway `/v1/trigger`
  endpoints will orchestrate them with authentication once access controls are in place.
