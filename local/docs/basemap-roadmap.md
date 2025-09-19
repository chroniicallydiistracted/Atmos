# Basemap Roadmap – CyclOSM Parity

This note captures where the local basemap stands today, plus the concrete steps
we still need to take to deliver a 1:1 replica of the official CyclOSM style.

## Current State (2025-09-19)

* **Frontend shell** – UI trimmed down to `TopBar + BasemapView` so the map is
the primary focus (`local/services/frontend/src/pages/App.tsx`). All layer,
timeline, and alert controls have been removed until those data products exist.
* **Style adjustments** – `src/styles/cyclosm-style.json` now applies the core
CyclOSM palette to the OpenMapTiles planet archive: beige land background,
park/forest/scrub/heath fills, farmland, water, and building tones match the
reference color table from `CyclOSM-CSS`. The top bar still uses the health
indicator + coordinate jump.
* **Self-hosted data** – MapLibre is reading our local
`planet.z15.pmtiles` (47 GB). No external tile services are hit. A Puppeteer
smoke script (`scripts/check-basemap.cjs`) runs against `http://localhost:4173`
so we can validate rendering after style tweaks.

## Gaps vs. CyclOSM Reference

1. **Bicycle network overlays** – The official style expects a
`bicycle_routes` layer with LCN/RCN/NCN/ICN geometries. The stock OpenMapTiles
planet archive does **not** ship this layer, so our map lacks the blue corridor
network and route shields.
2. **Relief / hillshade** – Raster shading and contour emphasis that give the
CyclOSM raster tiles their 3D feel are absent. Our current vector-only style
looks flat in mountainous terrain (Phoenix screenshot highlights this gap).
3. **Auxiliary landcover** – Items such as orchards, vineyards, protected
areas, or farmland variants appear in the raster flavor thanks to custom SQL.
We have the basic fills but still need to audit whether additional classes are
missing from OpenMapTiles vs. CyclOSM CartoCSS.
4. **Fonts / sprites** – We are already serving the CyclOSM sprite sheet, but
we should double-check the glyph stack (they ship a curated subset of Noto).
5. **Style synchronization** – Our JSON is now close to the upstream GL style
but diverges as we add local overrides. Long term we should ingest the upstream
style verbatim and only patch the `sources`/URLs.

## Path to 1:1 Parity

### 1. Generate Vector Overlays (bicycle network & optional landcover extras)

* Extract cycle routes from the planet PBF:
  ```bash
  osmium tags-filter planet-latest.osm.pbf r/highway=cycleway \
    w/network=icn,rcn,lcn,ncn -o bicycle_routes.osm.pbf
  ```
* Convert to PMTiles with the expected layer name:
  ```bash
  tippecanoe -o local/data/basemaps/cyclosm-bicycles.pmtiles \
    --layer=bicycle_routes --no-tile-compression \
    --simplification=4 --maximum-zoom=14 bicycle_routes.osm.pbf
  ```
  *For CONUS-only builds, filter on a bounding box to keep the file small.*
* (Optional) run additional extracts for landcover tags that are missing in
  OpenMapTiles (orchard, vineyard, recreation_ground, etc.) and expose them as
  `landuse_overlay_*` layers if needed.
* Update `cyclusm-style.json` to add a second vector source:
  ```json
  "sources": {
    "osm": { ... },
    "cyclosm-bicycle": {
      "type": "vector",
      "url": "pmtiles://./basemaps/cyclosm-bicycles.pmtiles"
    }
  }
  ```
  Then repoint the four `bicycleroutes-*` layers to `cyclosm-bicycle`.

### 2. Hillshade / Relief Tiles

* Use the helper under `services/cyclosm/hillshade/generate-hillshade.sh` to
  bake SRTM/AW3D DEM data into raster tiles. Suggested workflow:
  1. Download DEM for the region (e.g. USGS 1 arc-second).
  2. Run the script to produce Cloud-Optimized GeoTIFFs or WebP tiles.
  3. Convert to PMTiles (`pmtiles convert` for raster) and store as
     `local/data/basemaps/hillshade.pmtiles`.
* Add a raster source to the style:
  ```json
  "hillshade": {
    "type": "raster",
    "url": "pmtiles://./basemaps/hillshade.pmtiles",
    "tileSize": 256,
    "maxzoom": 15
  }
  ```
  Recreate CyclOSM’s `hillshade` layer definition (blend mode multiply).

### 3. Contours (optional but matches raster flavor)

CyclOSM overlays contour lines on the raster style. If we want the same look,
produce contour vector tiles (e.g. via `gdal_contour` + tippecanoe) and add a
`contours` source/layer pair. This is optional but improves terrain legibility.

### 4. Sync with Upstream Style

* Mirror `cyclosm-basic-gl-style/style.json` into our repo and keep it pristine.
* Maintain a small TypeScript/Node script that patches only the `sources`
  section (point to our PMTiles) and writes the runtime style MapLibre consumes.
  That way future upstream updates are a simple rebase.

### 5. Font Audit

Ensure the glyphs we’re fetching (`demotiles.maplibre.org`) include all font
families the style references. Long term we should host the CyclOSM font PBFs
ourselves (see `services/cyclosm/fonts` for the subset manifest).

## Worklog Reference

| Date       | Change                                                                                 |
|------------|----------------------------------------------------------------------------------------|
| 2025-09-17 | Initial MapLibre shell & PMTiles wiring (`BasemapView`, `MapStateProvider`)            |
| 2025-09-18 | UI trimmed to basemap-only experience; sprites copied to `public/sprites/cyclosm/`    |
| 2025-09-19 | Style palette aligned with CyclOSM colors; farmland / parks / forests / water tuned    |
| 2025-09-19 | Added Puppeteer smoke script (`scripts/check-basemap.cjs`) for automated screenshots    |

Keep this document updated as we add overlays and hillshade so we always know
how far we are from true CyclOSM parity.
