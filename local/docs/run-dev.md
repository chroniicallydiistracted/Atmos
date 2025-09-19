# Run the Full Development Stack

This guide brings up the API gateway, ingestion service, and frontend so you can
exercise triggers end-to-end while layering new features.

## Prerequisites
- Docker + Docker Compose
- Local `.env` file (`cp local/config/.env.example local/config/.env`)
- Python deps installed (`python -m venv .venv && .venv/bin/pip install -r local/services/api/requirements.txt -r local/services/ingestion/requirements.txt`)
- Frontend deps installed (`cd local/services/frontend && npm install`)

## Commands

```bash
# from repo root
./local/scripts/dev-stack.sh up

# optional: tail logs
./local/scripts/dev-stack.sh logs api frontend ingestion

# seed MinIO + Postgres with placeholder data
./local/scripts/dev-stack.sh seed
```

Services exposed (the frontend `.env` now targets these localhost ports by default):
- API: http://localhost:8081/v1/healthz
- Ingestion: http://localhost:8084/healthz (manual triggers)
- Frontend: http://localhost:4173 (Vite dev server through container)
- Basemap PMTiles: http://localhost:8082/pmtiles
- MinIO Console: http://localhost:9090 (user/password from `.env`)

Copy PMTiles into `local/data/basemaps/` before starting the stack. With the
default configuration the frontend should reference:

```
pmtiles://http://localhost:8082/pmtiles/planet.z15.pmtiles
```

### Teardown
```bash
./local/scripts/dev-stack.sh down          # removes containers + volumes
./local/scripts/dev-stack.sh down --keep-data  # keep MinIO/Postgres volumes
```

### Tips
- The seed command writes sample timeline entries under `indices/goes/sample/`
  so the frontend timeline explorer has data even before real ingestion runs.
- `API_HTTP_TIMEOUT_SECONDS` in `.env` controls trigger timeout budgeting.
- For iterative backend/frontend changes the compose setup mounts `src/` so
  changes hot-reload without rebuilding images.
