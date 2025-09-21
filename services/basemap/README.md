# Basemap Service

Serves PMTiles basemap artifacts (CyclOSM vector tiles) to the local frontend
with proper HTTP range support.

## Features
- `GET /healthz` – reports available PMTiles and default dataset
- `GET /pmtiles` – lists discovered `.pmtiles` in the data directory
- `GET /pmtiles/:name` – streams a PMTiles file with HTTP range responses

## Configuration
Environment variables (see `local/config/.env`):

- `BASEMAP_PORT` – listening port (default `8082`)
- `BASEMAP_DATA_DIR` – where PMTiles files are mounted (`/app/data` in Docker)
- `BASEMAP_PMTILES_DEFAULT` – filename that frontend should request by default
- `BASEMAP_CORS_ORIGINS` – comma separated origins allowed for cross-origin access

## Running locally

```bash
cd local/services/basemap
npm install
npm run dev
```

With the Docker compose stack:

```bash
./local/scripts/dev-stack.sh up      # builds and starts the basemap service
```

Place your `.pmtiles` datasets under `local/data/basemaps/` before starting the
stack. The frontend expects to fetch `http://localhost:8082/pmtiles/planet.pmtiles`
and uses the pmtiles protocol for MapLibre. The bicycle network overlay and
hillshade raster PMTiles **must** exist alongside the base dataset; generate them
via `./local/scripts/build-basemap-assets.sh` which emits
`cyclosm-bicycles.pmtiles` and `hillshade.pmtiles` into the same directory.
