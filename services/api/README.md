# API Gateway Service

This service will expose the unified HTTP API for the frontend and automation tools. It replaces the AWS API Gateway + Lambda combination.

## Responsibilities
- Health and status endpoints
- Timeline queries (reading metadata from MinIO/postgres)
- Trigger endpoints to invoke ingestion jobs
- Authentication/authorization (future)

## Proposed Stack
- FastAPI + Uvicorn (Python) or NestJS (TypeScript). Decision pending after prototyping.
- Shared client library for object-store and job queue interactions.

## Next Steps
- Decide on language/runtime.
- Define API contract in `docs/api-contract.md`.
- Implement minimal health endpoint + integration test.
