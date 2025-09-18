# COMPREHENSIVE REPOSITORY SCAN - ISSUES LOG

## Scan Strategy
- Line-by-line, file-by-file analysis
- Flag issues without attempting fixes
- Track issue interdependencies and compound effects
- Document context for each issue

## Issues Discovered

### ISSUE #1: Font System (RESOLVED)
**Status:** ✅ RESOLVED
**Files:** `services/cyclosm/renderer/server.js`, `generate-mapnik-xml.js`
**Issue:** Font registration targeting parent directories failed
**Context:** ROOT CAUSE identified and fixed
**Dependencies:** None - isolated issue

---

### ISSUE #2: Missing GIS Shapefiles
**Status:** 🔍 IDENTIFIED
**File:** `services/cyclosm/renderer/mapnik.xml` (generated from CyclOSM project.mml)
**Issue:** Server fails with "shapefile 'http://osmdata.openstreetmap.de/download/simplified-land-polygons-complete-3857.zip.shp' does not exist"
**Context:** Font loading successful (2,425 fonts), now failing on missing Natural Earth data
**Error:** `Shape Plugin: shapefile '/home/andre/Atmos/services/cyclosm/renderer/http://osmdata.openstreetmap.de/download/simplified-land-polygons-complete-3857.zip.shp' does not exist`
**Dependencies:** 
- Renderer can't start without shapefiles
- Compound effect: Working fonts + Missing data = Non-functional renderer
**Severity:** HIGH - Blocks renderer functionality

---

### ISSUE #3: Missing Natural Earth Shapefiles
**Status:** 🔍 IDENTIFIED  
**Files:** `CyclOSM-CSS-Master/project.mml` (lines 55-72)
**Issue:** CyclOSM configuration references remote shapefile URLs that are downloaded but not locally available
**Context:** 
- Line 58: `file: http://osmdata.openstreetmap.de/download/simplified-land-polygons-complete-3857.zip`
- Line 67: `file: http://osmdata.openstreetmap.de/download/land-polygons-split-3857.zip`
- These are Natural Earth coastline/land polygon data required for base map rendering
**Dependencies:** 
- COMPOUND EFFECT: Font loading works → Natural Earth data missing → Renderer fails to start
- Blocks entire map rendering functionality
- Relates to Issue #2 (server shapefile error is caused by this configuration)
**Severity:** HIGH - Critical for map rendering

### ISSUE #4: Multiple Database Dependencies
**Status:** 🔍 IDENTIFIED
**Files:** `CyclOSM-CSS-Master/project.mml` (throughout)
**Issue:** Configuration expects multiple specialized databases
**Context:**
- Line 32: `dbname: "osm"` (main OSM database)
- Line 203: `dbname: "contours"` (elevation contours database)
- Lines 485, 548, 688: References to `cyclosm_ways` table (custom processed view)
- Lines 1405, 1414: References to `cyclosm_amenities_poly`, `cyclosm_amenities_point` tables
**Dependencies:**
- Requires OSM data import and processing 
- Requires elevation data processing for contours
- Requires custom CyclOSM-specific database views/tables
- COMPOUND EFFECT: Missing specialized tables will cause selective layer failures
**Severity:** HIGH - Multiple rendering layers will fail

### ISSUE #5: DEM/Elevation Data Dependencies
**Status:** 🔍 IDENTIFIED
**Files:** `CyclOSM-CSS-Master/project.mml` (lines 190-269)
**Issue:** Configuration expects Digital Elevation Model (DEM) files
**Context:**
- Line 194: `file: dem/shade.vrt` (hillshade raster)
- Lines 198-269: Multiple contour layers (100m, 50m, 20m, 10m intervals)
- All marked as `status: off` (disabled by default)
**Dependencies:**
- Requires DEM processing pipeline
- Currently disabled but infrastructure expects these files
**Severity:** MEDIUM - Currently disabled, but incomplete infrastructure

---

### ISSUE #6: Missing CyclOSM Custom Database Views/Tables
**Status:** 🔍 IDENTIFIED
**Files:** `services/cyclosm/importer/post_import.sql`, `CyclOSM-CSS-Master/project.mml`
**Issue:** CyclOSM expects custom database views but post-import SQL is incomplete
**Context:**
- `project.mml` references: `cyclosm_ways`, `cyclosm_amenities_poly`, `cyclosm_amenities_point` tables
- `post_import.sql` only has commented-out index placeholders and `VACUUM ANALYZE`
- Missing the actual SQL to create the `cyclosm_*` views/tables from raw OSM data
**Dependencies:**
- COMPOUND EFFECT: OSM import runs → Custom views missing → Layer-specific rendering failures
- Multiple map layers will fail silently or return no data
- Requires CyclOSM-specific data processing logic
**Severity:** HIGH - Core CyclOSM functionality missing

### ISSUE #7: Natural Earth Data URLs Changed/Broken
**Status:** 🔍 IDENTIFIED  
**Files:** `services/cyclosm/importer/import.sh` (lines 30-52)
**Issue:** Import script fetches from old Natural Earth S3 bucket
**Context:**
- Line 30: `NE_BASE=${NE_BASE:-https://naturalearth.s3.amazonaws.com}` (old URL)
- Lines 32-38: Hardcoded Natural Earth layer paths that may have changed
- Import script tries to fetch countries, states, lakes, oceans, rivers data
- Error handling shows warnings but doesn't fail the build
**Dependencies:**
- Links to Issue #3 (project.mml references different URLs)
- COMPOUND EFFECT: Import gets some data → project.mml expects different data → Mismatched data sources
**Severity:** MEDIUM - Has fallback handling but incomplete data

### ISSUE #8: Docker Container Deployment Architecture Issues
**Status:** 🔍 IDENTIFIED
**Files:** `CyclOSM-CSS-Master/Dockerfile.import`, `infra/terraform/main.tf`
**Issue:** Inconsistent container architecture and deployment approach
**Context:**
- `Dockerfile.import` uses Ubuntu 18.04 (bionic - EOL April 2023)
- Uses deprecated PPA key server approach (`apt-key adv`)
- References missing startup script: `sh scripts/docker-startup.sh import`
- Terraform infrastructure doesn't include CyclOSM service deployment
**Dependencies:**
- Security risk from EOL Ubuntu version
- Missing integration between import containers and main infrastructure
- Terraform only defines static site, API, events - no map rendering service
**Severity:** HIGH - Security + deployment architecture gaps

---

### ISSUE #9: Weather Service Incomplete Implementation
**Status:** 🔍 IDENTIFIED
**Files:** `services/tiler/app.py` (lines 67-75), `services/radar-prepare/handler.py`
**Issue:** Sophisticated weather processing system with incomplete tiler integration
**Context:**
- `radar-prepare/handler.py`: Complete 327-line NEXRAD Level II processing with Py-ART
- `tiler/app.py`: Weather tile endpoint exists but temperature conversion logic missing (lines 70, 73: "# Implement temperature conversion logic")
- Frontend expects weather tiles: `/tiles/goes/`, `/tiles/mosaic/`, `/tiles/weather/`
**Dependencies:**
- Weather data processing works but tile serving incomplete
- Frontend will receive empty/broken weather tiles
- Missing color palette and rescaling logic for weather visualization
**Severity:** MEDIUM - Weather system functional but user-facing tiles broken

### ISSUE #10: Frontend Style Mismatch
**Status:** 🔍 IDENTIFIED
**Files:** `web/src/components/MapView.tsx` (lines 7, 88)
**Issue:** Frontend expects different tile endpoints than backend provides
**Context:**
- Line 7: `VITE_STYLE_URL || '/styles/cyclosm.json'` expects static CyclOSM style
- Line 88: `VITE_TILE_BASE || 'https://weather.westfam.media'` hardcoded domain
- Frontend expects: `/tiles/goes/abi/c13/conus/{timestamp}/kelvin/{z}/{x}/{y}.png`
- Backend provides: `/tiles/cyclosm/{z}/{x}/{y}.png` (different structure)
**Dependencies:**
- COMPOUND EFFECT: CyclOSM renderer works → Frontend expects different API → UI-backend mismatch
- Links to Issue #9 (weather tiles incomplete)
- Hardcoded domain doesn't match development environment
**Severity:** HIGH - Complete UI-backend disconnect

---

## COMPREHENSIVE SCAN COMPLETE

## Files Scanned
- ✅ `services/cyclosm/renderer/server.js`
- ✅ `services/cyclosm/renderer/generate-mapnik-xml.js` 
- ✅ `CyclOSM-CSS-Master/project.mml` 
- ✅ `services/cyclosm/importer/import.sh`
- ✅ `services/cyclosm/importer/post_import.sql`
- ✅ `CyclOSM-CSS-Master/Dockerfile.import`
- ✅ `init-db.sql`
- ✅ `infra/terraform/main.tf`
- ✅ `services/radar-prepare/handler.py`
- ✅ `services/tiler/app.py`
- ✅ `web/src/App.tsx`
- ✅ `web/src/components/MapView.tsx`

## SYSTEM ARCHITECTURE IDENTIFIED

**AtmosInsight** is a sophisticated weather visualization system with:

1. **Base Map System (CyclOSM)**: Custom OSM map renderer with bicycle-focused styling
2. **Weather Data Processing**: NEXRAD Level II radar, GOES satellite, MRMS data processing 
3. **Tile Serving**: Custom TiTiler-based weather tile server
4. **Frontend**: React/TypeScript MapLibre GL JS application
5. **Infrastructure**: AWS Lambda, S3, CloudFront, Terraform managed

## CRITICAL ISSUE INTERDEPENDENCIES

**Primary Issue Chain:**
1. ✅ Font system resolved
2. 🔴 Natural Earth shapefiles missing → CyclOSM base map fails
3. 🔴 Custom database views missing → CyclOSM layers fail
4. 🔴 Frontend API mismatch → Weather tiles fail
5. 🔴 Incomplete tiler logic → Weather visualization fails

**Result:** System has sophisticated weather processing but broken user interface

---

## 🚨 **CRITICAL DEPENDENCY ALERT**

### ISSUE #11: Missing Planet PMTiles File
**Status:** ⏸️ **BLOCKING** 
**Files:** `web/src/components/MapView.tsx` (line 19), `web/web-static/styles/cyclosm.json` (empty)
**Issue:** Frontend expects PMTiles basemap that is currently downloading
**Context:**
- Line 19: `maplibregl.addProtocol('pmtiles', protocol.tile)` - Frontend uses PMTiles protocol
- `/web/web-static/styles/cyclosm.json` is **empty** (0 bytes) - Missing MapLibre style definition
- User mentioned `planet.z15.pmtiles` is currently downloading
- Generated `mapnik.xml` references `planet_osm_*` database tables (67 references found)
**Dependencies:**
- **BLOCKS ALL MAP RENDERING**: Without PMTiles file, frontend map cannot display anything
- **DOUBLE DEPENDENCY**: Missing both PMTiles file AND MapLibre style JSON 
- **SUPERSEDES OTHER ISSUES**: Most other map rendering issues cannot be tested until this resolves
**Severity:** **CRITICAL - BLOCKING**

## 📋 **RECOMMENDED FIX PRIORITY ORDER**

**WAIT FOR PMTILES DOWNLOAD:**
1. ⏸️ **#11** - Wait for `planet.z15.pmtiles` download completion
2. ⏸️ **Generate MapLibre style JSON** from CyclOSM → `/web/web-static/styles/cyclosm.json`
3. ⏸️ **Verify PMTiles → CyclOSM tile endpoint mapping**

**THEN PROCEED WITH:**
4. 🔴 **#2/#3** - Natural Earth shapefiles (CyclOSM base map)
5. 🔴 **#6** - Custom database views (CyclOSM layers)
6. 🔴 **#10** - Frontend-backend API alignment

**Result:** All CyclOSM/map-related fixes should be **deferred** until PMTiles infrastructure is in place.

## Next Files to Scan
1. `CyclOSM-CSS-Master/project.mml` - Root configuration
2. `services/cyclosm/importer/` - Data import system
3. `infra/terraform/` - Infrastructure configuration
4. `scripts/` - Deployment and utility scripts
5. Root configuration files

## Issue Tracking Template
**ISSUE #X: [Title]**
**Status:** 🔍 IDENTIFIED / ⚠️ FLAGGED / ✅ RESOLVED
**Files:** [file paths]
**Issue:** [description]
**Context:** [surrounding context]
**Dependencies:** [related issues]
**Severity:** [LOW/MEDIUM/HIGH/CRITICAL]

---

*Scan in progress...*