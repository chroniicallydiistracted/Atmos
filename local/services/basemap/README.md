# Basemap Renderer (CyclOSM)

Goal: port the CyclOSM renderer into the new local stack, removing AWS-specific startup steps.

## Key Tasks
- Containerize Mapnik + Node renderer with local font bundle.
- Connect to PostGIS (`postgres` service) for data.
- Support metatile rendering and cache tiles in MinIO or local disk.
- Provide health endpoint for proxy monitoring.

## Data Requirements
- OSM import handled by `services/database-import` (to be added).
- Font assets from `fonts/` directory in repo; mount read-only.
- Raster hillshade/contours generated locally.

## Notes
The legacy renderer code under `services/cyclosm/` is a reference; port pieces incrementally and add tests.
