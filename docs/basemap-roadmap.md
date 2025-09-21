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
* **Overlay integration** – `BasemapView` now requires dedicated bicycle and
  hillshade PMTiles (`VITE_BASEMAP_BICYCLE_PM`, `VITE_BASEMAP_HILLSHADE_PM`);
  startup fails fast if they are missing so we cannot ship an incomplete style.
* **Self-hosted data** – MapLibre is reading our local
`planet.z15.pmtiles` (47 GB). No external tile services are hit. A Puppeteer
smoke script (`scripts/check-basemap.cjs`) runs against `http://localhost:4173`
so we can validate rendering after style tweaks.

### Hosted Tile Shortcut (for exploration only)

When you need a quick preview without the full PMTiles pipeline, you can point
the frontend at CyclOSM’s public raster tiles. Set the following in
`local/config/.env`:

```
VITE_CYCLOSM_TILE_TEMPLATE=https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png
VITE_CYCLOSM_TILE_SUBDOMAINS=a,b,c
```

The map will switch to a hosted raster source, add the required
“© OpenStreetMap contributors · CyclOSM” attribution, and keep the URL
configurable (per the OpenStreetMap tile usage policy). This mode is for light
development use only—disable it before shipping to production and fall back to
our self-hosted PMTiles.

## Gaps vs. CyclOSM Reference

1. **Bicycle network overlays** – The style wiring now mandates a
`bicycle_routes` PMTiles overlay. We still need a repeatable extract pipeline so
the dataset stays fresh and covers the desired extent.
2. **Relief / hillshade** – Hillshade PMTiles are required in the style, but we
need to finalize the DEM sourcing/processing workflow to keep the raster up to
date and aligned with CyclOSM’s tonal balance.
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

* Extract cycle routes from the planet PBF (see
  `local/scripts/build-basemap-assets.sh --help` for automation):
  ```bash
  osmium tags-filter planet-latest.osm.pbf r/highway=cycleway \
    w/network=icn,rcn,lcn,ncn -o bicycle_routes.osm.pbf
  ```
* Convert to PMTiles with the expected layer name (the frontend already targets
  `cyclosm-bicycles.pmtiles`):
  ```bash
  tippecanoe -o local/data/basemaps/cyclosm-bicycle.pmtiles \
    --layer=bicycle_routes --no-tile-compression \
    --simplification=4 --maximum-zoom=14 bicycle_routes.osm.pbf
  # Docker-based pipeline (filters + tiles + convert)
  ./local/scripts/build-cyclosm-bicycle.sh --planet /path/to/planet.osm.pbf
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
      "url": "pmtiles://./basemaps/cyclosm-bicycle.pmtiles"
    }
  }
  ```
  Then repoint the four `bicycleroutes-*` layers to `cyclosm-bicycle`.
  
### 2. Hillshade / Relief Tiles

* Use `local/scripts/build-basemap-assets.sh --hillshade-dem <path>` to
  orchestrate GDAL hillshade generation. Suggested workflow:
  1. Download DEM for the region (e.g. USGS 1 arc-second).
  2. Run the script to produce Cloud-Optimized GeoTIFFs or WebP tiles.
  3. Convert to PMTiles (`pmtiles convert` for raster) and store as
     `local/data/basemaps/hillshade.pmtiles`.
* Add a raster source to the style (handled automatically; the frontend requires
  `hillshade.pmtiles` to exist):
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
  That way future upstream updates are a simple rebase. (Plumbing now exists via
  `BasemapView` helpers, which require all PMTiles; we still need automation to
  sync upstream JSON.)

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
| 2025-09-19 | Added automated bicycle overlay builder + frontend integration (build-cyclosm-bicycle.sh) |
| 2025-09-19 | Added Puppeteer smoke script (`scripts/check-basemap.cjs`) for automated screenshots    |
| 2025-09-20 | Overlay/hillshade PMTiles plumbing added; `build-basemap-assets.sh` scaffolds artefacts |

Keep this document updated as we add overlays and hillshade so we always know
how far we are from true CyclOSM parity.
