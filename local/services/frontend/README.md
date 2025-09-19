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
npm run dev        # starts Vite dev server on http://localhost:5173
npm run build      # emits production assets to dist/
npm run preview    # serves the built assets on http://localhost:4173
npm test           # run vitest suite
```

Environment variables (`VITE_API_BASE`, `VITE_TILE_BASE`) are injected via
`local/config/.env`. The Docker image runs `npm run preview` by default.

## Next steps
- Re-introduce weather overlays (radar, satellite, alerts, lightning) once their data services are ready.
- Add timeline controls after ingestion backfills expose usable frame sequences.
- Layer on Playwright/puppeteer checks for end-to-end validation against the running local stack.
