# Run the Core Slice

This brings up: Caddy (reverse-proxy), MinIO, Postgres, API. Buckets are auto-created by `object-store-init`.
For the full stack including ingestion + frontend see `local/docs/run-dev.md`.

## Prereqs
- Docker + Docker Compose
- Populate `local/config/.env` (copy from `.env.example`)

## Commands

```bash
# from repo root
cp -n local/config/.env.example local/config/.env

# bring up the core stack
docker compose -f local/docker-compose.yml --profile core up -d --build

# follow logs
docker compose -f local/docker-compose.yml --profile core logs -f api object-store postgres reverse-proxy object-store-init

# test healthz
curl -s http://localhost/api/v1/healthz | jq .
# alternatively direct port:
curl -s http://localhost:8081/v1/healthz | jq .

# MinIO console
# http://localhost:9090  (user=localminio, pass=change-me-now)
```

## Expected
- `/healthz` returns:
  - `{"service":"api","minio":"ok","postgres":"ok","ok":"true", ...}`
- MinIO buckets: `raw`, `derived`, `tiles`, `logs` exist.

## Tear down
```bash
docker compose -f local/docker-compose.yml --profile core down -v
```
