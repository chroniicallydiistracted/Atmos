# Frontend (Local)

New Vite + React frontend configured for local APIs and tiles. Do not reuse the production-oriented configuration from the legacy repo directly.

## Current capabilities
- Vite + React 18 scaffold with React Query, React Router, and typed API hooks.
- Single-screen basemap experience powered by MapLibre + CyclOSM, loading tiles from the local PMTiles service.
- Top bar with health indicator and coordinate-based recenter control for quick navigation.
- Vitest + Testing Library smoke test that verifies the basemap shell renders (MapLibre mocked for unit tests).

## Usage

```bash
cd local/services/frontend
npm install
npm run dev        # starts Vite dev server (see 'Dev Access Modes' below)
npm run build      # emits production assets to dist/
npm run preview    # serves the built assets (same port as dev in container config)
npm test           # run vitest suite
```

Environment variables (`VITE_API_BASE`, `VITE_TILE_BASE`) are injected via
`local/config/.env`. The Docker image runs `npm run preview` by default.

## Dev Access Modes

There are two equivalent ways to reach the frontend + API during local development:

1. Through Caddy reverse proxy (recommended full-stack simulation):
	- Frontend: `http://localhost` (Caddy forwards to the Vite server)
	- API: `http://localhost/api/...` (Caddy `handle_path` strips the `/api` prefix before hitting FastAPI so backend sees `/v1/...`)
	- Tiles: `http://localhost/tiles/...` (prefix preserved)

2. Direct Vite dev server (bypassing Caddy):
	- Frontend: `http://localhost:4173`
	- API: `http://localhost:4173/api/...` (Vite dev proxy is configured with a rewrite that strips `/api` to mimic Caddy)
	- Tiles: `http://localhost:4173/tiles/...` (forwarded to tiler with prefix preserved)

Both paths are supported. If you remove or alter the proxy rewrite in `vite.config.ts`, direct access via port 4173 will break (`/api/v1/...` 404) because the backend does not expose `/api/v1`—only `/v1`. Keep the rewrite in sync with any Caddy behavior changes.

`VITE_API_BASE` defaults to `/api`; do not hardcode protocol+host for local usage. In production-like deployments behind a different origin, that value can be overridden accordingly.

## Next steps
- Re-introduce weather overlays (radar, satellite, alerts, lightning) once their data services are ready.
- Add timeline controls after ingestion backfills expose usable frame sequences.
- Layer on Playwright/puppeteer checks for end-to-end validation against the running local stack.
