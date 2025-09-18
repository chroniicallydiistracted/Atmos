# Local Architecture Overview

This document explains the target architecture for the local-first AtmosInsight stack. It replaces the AWS-centric design with services that can run entirely on self-managed infrastructure.

## High-Level Components

```
┌──────────────────────────┐
│        Frontend          │  React + MapLibre
└───────────┬──────────────┘
            │ REST/WebSockets
┌───────────▼──────────────┐
│        API Gateway       │  Express/FastAPI
└───────────┬──────────────┘
            │ Internal RPC
┌───────────▼──────────────┐     ┌──────────────────┐
│   Data Services Layer    │◀────│  Job Scheduler    │ cron/Temporal
│ - GOES ingest            │     └──────────────────┘
│ - MRMS ingest            │
│ - NEXRAD ingest          │
│ - Alerts baking          │
└───────────┬──────────────┘
            │ Object-store API / Filesystem
┌───────────▼──────────────┐
│   Object Store (MinIO)   │
└───────────┬──────────────┘
            │ Raster/vector data
┌───────────▼──────────────┐
│ Basemap Renderer (CyclOSM│  Mapnik/PostGIS
└───────────┬──────────────┘
            │ Tiles/PMTiles
┌───────────▼──────────────┐
│ Reverse Proxy (Caddy)    │  TLS termination, auth, caching
└──────────────────────────┘
```

## Core Principles

1. **Local-first** – All stateful services (Postgres, object store, scheduler) run on local hardware.
2. **Modularity** – Each service runs in its own container with clearly defined interfaces.
3. **Observability** – Metrics, logs, and traces feed into a local Prometheus/Loki stack.
4. **Security** – Secrets managed via local vault (`config/secrets/` with sops or Vault). TLS enforced at proxy.
5. **Reproducibility** – Everything deploys with `docker compose` and scripted setup.

## Service Breakdown

See `docs/services.md` for responsibilities, configs, and dependencies of each service.

## Legacy Mapping

| Legacy Component (root repo) | Status | Local Replacement |
| --- | --- | --- |
| AWS Lambda ingest functions | Legacy reference | Python-based ingestion workers under `services/ingestion/` |
| CloudFront + S3 | Legacy | Caddy/Traefik + MinIO |
| Terraform modules | Legacy | Docker Compose + Ansible (future) |
| CyclOSM renderer | Keep logic, refactor to local service | `services/basemap/` |

## Next Steps

1. Build object store abstraction and ingestion workers.
2. Port CyclOSM renderer into new layout.
3. Implement API gateway and frontend to use new endpoints.
4. Establish monitoring and backup scripts.
