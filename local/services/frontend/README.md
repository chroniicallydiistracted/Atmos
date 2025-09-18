# Frontend (Local)

New Vite + React frontend configured for local APIs and tiles. Do not reuse the production-oriented configuration from the legacy repo directly.

## Goals
- Use environment variables from `config/.env` (VITE_API_BASE, VITE_TILE_BASE).
- Incorporate MapLibre + PMTiles protocol with local basemap.
- Provide development server (`npm run dev`) and static build served via `docker compose`.

## TODO
- Scaffold fresh Vite project inside `src/`.
- Copy validated UI components only after they are refit to the new API contract.
- Add integration tests with Playwright or Cypress targeting local stack.
