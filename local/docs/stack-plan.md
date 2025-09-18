# Local Stack Implementation Plan

This plan breaks the rebuild into incremental milestones. Each milestone delivers a cohesive slice of functionality that can be verified before moving on.

## Milestone 0 – Environment Bootstrap
- [ ] Finalize hardware audit (specs, network, UPS, backup target).
- [ ] Create `.env` from example and populate initial secrets.
- [ ] Bring up base infrastructure services only (`object-store`, `postgres`, `reverse-proxy`).
- [ ] Verify MinIO and Postgres are reachable via proxy/subnets.

## Milestone 1 – Storage & Data Layer
- [ ] Implement MinIO bucket bootstrap script (`local/scripts/bootstrap.sh`).
- [ ] Define bucket structure (`raw/`, `derived/`, `tiles/`, `logs/`).
- [ ] Set up PostGIS extensions and placeholder schemas.
- [ ] Document backup strategy (restic/rsync) and smoke-test manual snapshot.

## Milestone 2 – Ingestion Foundation
- [ ] Scaffold FastAPI-based ingestion service with shared FetchWithRetry.
- [ ] Implement GOES pipeline end-to-end (download ➜ COG ➜ MinIO ➜ metadata).
- [ ] Add scheduling via APScheduler; confirm idempotency.
- [ ] Write unit/integration tests against MinIO (compose profile `ingestion`).

## Milestone 3 – Basemap Pipeline
- [ ] Create PostGIS import workflow (`services/database-import`).
- [ ] Port CyclOSM renderer into `services/basemap` with local font bundle.
- [ ] Add tile caching strategy (filesystem → MinIO optional).
- [ ] Expose renderer health + metrics endpoints.

## Milestone 4 – API Gateway
- [ ] Decide stack (FastAPI vs. NestJS). Prototype minimal `/healthz` endpoint.
- [ ] Implement timeline endpoints reading from MinIO/Postgres.
- [ ] Add trigger endpoints secured via API key or mTLS.
- [ ] Define OpenAPI spec and publish to `docs/api-contract.md`.

## Milestone 5 – Frontend Refresh
- [ ] Scaffold Vite project, integrate MapLibre with local basemap + PMTiles protocol.
- [ ] Connect to new API endpoints for timeline/state.
- [ ] Implement playback UI, layer toggles, and stale-data indicators.
- [ ] Add Playwright/Cypress smoke tests.

## Milestone 6 – Observability & Operations
- [ ] Introduce Prometheus/Grafana/Loki compose profile.
- [ ] Instrument services with metrics/log formats.
- [ ] Configure alert rules for data freshness, ingest failures.
- [ ] Finalize backup automation (`scripts/backup.sh`) and restoration runbook.

## Milestone 7 – Domain & Security
- [ ] Configure Caddy for HTTPS + authentication.
- [ ] Integrate Cloudflare DNS for external access (if required).
- [ ] Lock down firewall rules and VPN access.
- [ ] Conduct security review and load tests.

## Milestone 8 – Cutover Readiness
- [ ] Run full end-to-end validation (ingestion ➜ storage ➜ API ➜ frontend).
- [ ] Prepare migration checklist for DNS cutover, disable AWS pipelines.
- [ ] Schedule go-live and rollback plan.
- [ ] Post-cutover monitoring and documentation updates.

Use this plan as the canonical roadmap. Update checkboxes and notes as milestones progress.

