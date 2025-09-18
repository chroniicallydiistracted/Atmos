# CyclOSM Raster Tile Pipeline (CONUS, AWS, Production Fonts)

## 1. Goals
- Authentic CyclOSM visual parity for CONUS region (zooms 0–20; initial focus 0–19 if z20 not critical) using upstream CartoCSS.
- Raster tile delivery via CloudFront under /tiles/cyclosm/{z}/{x}/{y}.png (or /v1/tiles/ if aligning with API stage) with long-cache immutable semantics.
- Authoritative data pipeline: import OSM CONUS extract, required shapefiles, DEM for hillshade/contours.
- Zero placeholder assets: full font glyph coverage for required scripts (prioritized subset for CONUS + core Latin/Emoji, but plan allows expansion).
- Cost-aware: leverage on-demand ephemeral batch for heavy preprocessing (import, contour generation) and lean always-on rendering service.

## 2. High-Level Architecture
1. Data Acquisition Batch (ECS Fargate task or Spot EC2) -> Downloads OSM PBF extract + external shapefiles + DEM.
2. PostGIS Import Layer (Container) -> Uses osm2pgsql flex style (CyclOSM expects classic schema similar to OSM Carto) to populate RDS/Postgres (with PostGIS) or self-managed PostGIS on EC2. (Decision: Start with RDS for durability & maintenance simplicity.)
3. Preprocessing: Generalized tables? CyclOSM relies mostly on queries with ST_Simplify & scale-dependent conditions; no custom generalized tables needed initially (verify project.mml). Contours & Hillshade generated into GeoTIFFs -> gdal2tiles? Actually Mapnik raster symbolization: Provide hillshade raster(s) in filesystem or S3 and mount via vsicurl / local copy.
4. Font Preparation: Fontnik glyph generation -> S3 prefix /fonts/{fontstack}/{range}.pbf served via CloudFront (MapLibre parity and potential future vector fallback). For Mapnik, system fonts installed inside render container; PBF glyphs optional if later vector style added.
5. Rendering Service: Mapnik (via `tilelive-mapnik` or simple node-express + `@mapbox/tilelive` or renderd/mod_tile). Simpler: Use `openstreetmap-tiles` rendering stack? To keep tight control, build custom Node service:
   - Load CartoCSS with `carto` -> generate Mapnik XML at container start.
   - Use `mapnik` bindings to render tiles on request.
   - Caching: In-memory LRU + write-through to S3 ("render once then cache").
6. Cache Layer: S3 bucket prefix /cache/cyclosm/{z}/{x}/{y}.png with Cache-Control: public,max-age=31536000,immutable. CloudFront behavior points to S3 first; if MISS -> origin request Lambda or route to render service? Alternative simpler: CloudFront behavior to render service; service checks S3 before rendering. (Selected: Service-first for conditional logic.)
7. Distribution: CloudFront behavior /tiles/cyclosm/* -> origin = render service ALB (or API Gateway HTTP) with Origin Shield; service handles conditional S3 check.

## 3. Data Sources
- OSM Extract (CONUS): Geofabrik North America -> Extract USA + optional bordering Canada/Mexico trimming? Start with Geofabrik `north-america/us-latest.osm.pbf` and potentially subset via osmium if needed.
- Land polygons / coastlines: https://osmdata.openstreetmap.de/download/land-polygons-complete-4326.zip and simplified version if required.
- Water polygons (optional if project.mml expects them) from the same osmdata site: `water-polygons-split-4326.zip`.
- Natural Earth shapefiles (admin boundaries, lakes) if referenced (verify project.mml). Add NE 10m admin, lakes.
- DEM: USGS 3DEP (1 arc-second) mosaic; process with GDAL to hillshade GeoTIFF (gdalwarp -> gdaldem hillshade). Contours (optional phase 2) using `gdal_contour` at 10m/20m intervals depending on zoom policy.

## 4. Containers
- importer: Base image (debian-slim + osm2pgsql + osmium-tool + gdal). Entrypoint script orchestrates download and import.
- renderer: Node 20 + mapnik bindings + carto + caching layer + AWS SDK. Includes fonts installed to `/usr/share/fonts`.
- hillshade (batch): gdal (gdaldem) precompute hillshade & optionally contours; outputs to S3 (/raster/hillshade/, /raster/contours/).

## 5. PostGIS
- Amazon RDS PostgreSQL 15 + PostGIS 3.x. Instance class: db.m6g.large initial. Storage: gp3 200GB auto-scale.
- Extensions: postgis, hstore.
- Parameter group: work_mem tuned (64MB), shared_buffers default 25% instance memory.
- osm2pgsql command (classic schema):
  osm2pgsql --create --slim --number-processes=8 \
    --cache=4000 --hstore --multi-geometry \
    --style openstreetmap-carto.style (derive from upstream if needed) \
    --database $DB --username $USER --host $HOST --port 5432 \
    us-latest.osm.pbf
- Re-import strategy: Full refresh weekly (ephemeral task + new DB load + swap)? Phase 2.

## 6. Rendering Flow
1. Request /tiles/cyclosm/z/x/y.png at CloudFront.
2. CloudFront forwards to ALB -> ECS service (renderer) (path unchanged).
3. Renderer constructs S3 key; HEAD request to S3. If exists, 302 redirect to CloudFront signed S3 URL OR stream body (decide). Simpler: Fetch and return body with long cache headers (drawback: double transfer). Prefer: On MISS render -> store -> return with headers. On HIT optionally redirect 301 to S3 path to offload CPU.
4. Rendering: mapnik.Map(xml).render(z,x,y, callback) with metatile optimization (e.g., 8x8) and slice into tiles, writing all 64 to S3.

## 7. Fonts Strategy
- Required families (subset for CONUS multilingual coverage): Noto Sans Regular/Bold/Italic + Noto Sans CJK JP Regular/Bold, Noto Sans Hebrew Regular, Noto Sans Arabic UI Regular/Bold, Noto Naskh Arabic UI Regular (fallback), Noto Sans Devanagari UI Regular, Noto Sans Bengali UI Regular, Noto Sans Gurmukhi UI Regular, Noto Sans Tamil UI Regular, Noto Sans Telugu UI Regular, Noto Sans Kannada UI Regular, Noto Sans Thai UI Regular, Noto Sans Georgian Regular, Noto Sans Ethiopic Regular, Noto Sans Cherokee Regular, Noto Emoji Regular. (Can expand gradually.)
- System install: Use apt packages where available (fonts-noto-core, fonts-noto-cjk, fonts-noto-color-emoji, etc.) plus manual fetch for UI variants not packaged (download from Google fonts repo).
- Mapnik consumption: Just needs system font files present at container startup; rebuild image to add more.
- PBF Glyphs (future vector style compatibility): fontnik per TTF -> create shards.

### 7.1 Glyph Generation Commands (Example)
Assume working directory /workspace/fonts-src and output /workspace/fonts-pbf

Prepare font list file fonts.txt containing absolute paths to selected .ttf/.otf.

Node fontnik CLI (using @mapbox/fontnik via small script):

create file generate-font-pbfs.js:

```
const fs = require('fs');
const path = require('path');
const fontnik = require('@mapbox/fontnik');

const ranges = [
  [0,255],[256,511],[512,767],[768,1023],[1024,1279],
  [1280,1535],[1536,1791],[1792,2047],[2048,2303],[2304,2559],
  [2560,2815],[2816,3071],[3072,3327],[3328,3583],[3584,3839],
  [3840,4095],[4096,4351],[4352,4607],[4608,4863],[4864,5119],
  [5120,5375],[5376,5631] // extend as needed
];

const fonts = fs.readFileSync('fonts.txt','utf8').trim().split(/\n+/);

fonts.forEach(fontPath => {
  const family = path.basename(fontPath).replace(/\.(ttf|otf)$/,'');
  const outDir = path.join('fonts-pbf', family);
  fs.mkdirSync(outDir,{recursive:true});
  ranges.forEach(([start,end]) => {
    const buf = fs.readFileSync(fontPath);
    fontnik.range({ font: buf, start, end }, (err, res) => {
      if (err) { console.error('ERR', family, start, err); return; }
      fs.writeFileSync(path.join(outDir, `${start}-${end}.pbf`), res);
    });
  });
});
```

Run inside a container with node + @mapbox/fontnik installed. Validate no zero-byte outputs:

```
find fonts-pbf -type f -size 0 -print && echo "ERROR: empty glyphs" && exit 1
```

Sync to S3 (NO delete):

```
aws s3 sync fonts-pbf s3://<static-bucket>/fonts --size-only
```

### 7.2 Automation Script Outline
- Dockerfile.stage 'fonts-builder' with node + font packages.
- Entrypoint: gather font paths -> generate pbfs -> verify counts -> output manifest JSON listing families and ranges.
- Manifest path: /fonts/manifest.json (list families, lastUpdated ISO timestamp, sha256 of each pbf for integrity check).
- CloudFront: Add behavior /fonts/* to S3 direct origin (already existing static bucket).

## 8. Terraform Additions (Outline)
- ecr_repos: cyclosm-importer, cyclosm-renderer, cyclosm-hillshade.
- rds module: new Postgres + security group (ingress 5432 from ECS tasks only).
- ecs_cluster: shared cluster or dedicated.
- task_definitions: importer (ephemeral), renderer (service), hillshade (ephemeral on demand or scheduled).
- s3 paths: reuse static bucket for fonts & cached tiles, add bucket policy for GetObject.
- cloudfront behavior: /tiles/cyclosm/* -> origin = ALB (renderer). (Optional second behavior /raster/hillshade/* to S3 direct.)
- iam roles: renderer task role (S3 GetObject/PutObject on cache prefix), importer (S3 read/write, RDS connect), hillshade (S3 write raster assets).
- alarms: Renderer 5XX > threshold, RDS CPU > 80%, disk usage.

## 9. Phased Execution
Phase 0 (Design Validation): Approve this document. Output: Signed-off plan.
Phase 1 (Data & Fonts Prep): Build importer image, generate fonts, upload fonts to S3. Acceptance: Fonts accessible, importer container passes dry run (no DB yet). Rollback: Remove ECR repos.
Phase 2 (RDS + Import): Provision RDS, run importer with small state subset (e.g., single state extract) for smoke test. Acceptance: Sample tile renders locally (docker compose).
Phase 3 (Renderer Service MVP): Deploy ECS renderer with metatile=1 (no caching) hitting RDS. Acceptance: Tile returns 200 for z=5 CONUS tile in staging.
Phase 4 (Caching + Metatiles): Implement metatile 8, S3 write-through. Acceptance: Rendering log shows batch writes; repeated request served from cache <50ms.
Phase 5 (Hillshade & Contours): Generate hillshade/contours, integrate into style (update project.mml raster layer paths). Acceptance: Mountain shading visible.
Phase 6 (Production Scale & Alarms): Increase task count, enable CloudFront behavior, add alarms. Acceptance: <300ms p95 for cached tiles at edge, error rate <0.1%.
Phase 7 (Refresh Automation): Weekly importer run replacing DB (blue/green RDS or logical replication). Acceptance: Cutover with <10 min tile stale window.

## 10. Risk & Mitigations
- Font bloat: Limit initial set; lazy-add others if missing glyph alerts appear (log missing glyph events).
- RDS performance: Mitigate via proper osm2pgsql flags and instance scaling; consider partitioning or using r5g class.
- Hillshade size: Pre-cut to zoom <= 14 resolution to cap storage.
- Cold render latency: Use small warm-up script requesting key zoom/region tiles on deploy.
- Metatile memory: Monitor container RSS; adjust metatile down if >75% memory.

## 11. Open Decisions
- Use ALB vs API Gateway for renderer (leaning ALB for binary + websockets unnecessary).
- Redirect vs proxy for cached tiles (measure after MVP).
- Extent clipping: Keep full USA or buffered bounding box to avoid coastal artifacts.

## 12. Next Actions (Immediate)
1. Confirm font subset list. (DONE: see services/cyclosm/fonts/subset.json)
2. Add automation script for fontnik generation. (DONE: Dockerfile.fonts + generate-font-pbfs.js)
3. Scaffold Dockerfiles (importer, renderer) locally. (DONE: services/cyclosm/*)
4. Draft Terraform modules skeleton (no apply yet). (DONE: infra/terraform/services/cyclosm)
5. Integrate hillshade generator placeholder. (DONE: services/cyclosm/hillshade)
6. Implement S3 cache + metatile strategy (PENDING)
7. ECS Service + ALB + CloudFront behavior wiring (PENDING)
8. S3 cache write-through logic in renderer (PENDING)

-- END --
