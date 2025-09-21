# Zero-Cost Weather & Planetary Data: Public S3 Access Cookbook
**Scope:** Only sources that are free to read over HTTPS/S3 with **no credentials** and **no Requester Pays**.  
**Out of scope:** Any dataset that requires billing, credentials, API keys, sign-in, or "requester pays".

---

## Universal access rules (read before wiring code)

- **Anonymous S3 over HTTPS is allowed.** You can hit `https://<bucket>.s3.amazonaws.com/<key>` directly or use `aws s3` with `--no-sign-request`.
- **Prefer byte-range** or tiled/COG reads to avoid downloading whole files. GDAL `/vsicurl/` and tools like `rasterio` stream fine.
- **Directory listings:** `aws s3 ls --no-sign-request s3://bucket/prefix/` is the simplest way to discover keys.
- **Zarr/GRIB/NetCDF:** Many products are chunked for cloud; open lazily with xarray/zarr or use GRIB index sidecars when present.
- **Rate-limit your client** and add retries with backoff. Public buckets are shared infrastructure.
- **Stay compliant:** Only access data intentionally made public. Do not probe or brute-force keys.

---

## REAL-TIME / NEAR-REAL-TIME

### GOES (Geostationary satellites)
- **Buckets:**  
  - `s3://noaa-goes19/` (GOES-East since 2025-04-04)  
  - `s3://noaa-goes18/` (GOES-West)  
  - Legacy: `noaa-goes16/`, `noaa-goes17/` (may be static/offline)
- **Browse:**  
  - https://noaa-goes19.s3.amazonaws.com/  
  - https://noaa-goes18.s3.amazonaws.com/
- **Path pattern:** `ABI-L2-<PRODUCT>/YYYY/DDD/HH/...` (GLM lightning and SUVI products live alongside ABI)
- **CLI (anonymous):**  
  `aws s3 ls --no-sign-request s3://noaa-goes19/ABI-L2-MCMIPC/2025/09/20/`
- **HTTPS direct:**  
  `https://noaa-goes19.s3.amazonaws.com/ABI-L2-MCMIPC/2025/263/18/<file.nc>`

### JPSS (Polar orbiters: NOAA-20, NOAA-21, SNPP)
- **Buckets:**  
  - `s3://noaa-nesdis-n20-pds/`  
  - `s3://noaa-nesdis-n21-pds/`  
  - `s3://noaa-nesdis-snpp-pds/`
- **Browse:** `https://noaa-nesdis-n21-pds.s3.amazonaws.com/` (and similarly for N20, SNPP)
- **Path pattern:** `<PRODUCT>/<YYYY>/<DDD>/<HH>/...`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-nesdis-n21-pds/VIIRS-AOD/2025/250/18/`
- **HTTPS direct:** `https://noaa-nesdis-n21-pds.s3.amazonaws.com/VIIRS-AOD/2025/250/18/<file.nc>`

### NEXRAD (U.S. weather radar)
- **Buckets (Unidata):**  
  - Archive Level II: `s3://unidata-nexrad-level2/`  
  - Real-time Level II chunks: `s3://unidata-nexrad-level2-chunks/`  
  - Level III (selected products): `s3://unidata-nexrad-level3/`
- **Important:** The old `noaa-nexrad-level2` is deprecated; use `unidata-nexrad-level2`.
- **Path pattern:** `YYYY/MM/DD/<RADARID>/...`
- **CLI:** `aws s3 ls --no-sign-request s3://unidata-nexrad-level2/2025/09/20/KTLX/`
- **HTTPS direct:** `https://unidata-nexrad-level2.s3.amazonaws.com/2025/09/20/KTLX/<file>`

### MRMS (Multi-Radar/Multi-Sensor mosaics)
- **Bucket:** `s3://noaa-mrms-pds/`
- **Browse:** https://noaa-mrms-pds.s3.amazonaws.com/
- **Path pattern:** `<ProductName>/<YYYYMMDD>-<HHMM>-...` (2‑min cadence)
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-mrms-pds/PrecipRate/`
- **HTTPS direct:** `https://noaa-mrms-pds.s3.amazonaws.com/PrecipRate/MRMS_PrecipRate_YYYYMMDD-HHMM.grib2`

### GFS (Global Forecast System, operational)
- **Bucket:** `s3://noaa-gfs-bdp-pds/`
- **Browse:** https://noaa-gfs-bdp-pds.s3.amazonaws.com/index.html
- **Path pattern:** `gfs.YYYYMMDD/HH/atmos/gfs.t<HH>z.pgrb2.0p25.f<FFF>`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-gfs-bdp-pds/gfs.20250920/18/atmos/`
- **HTTPS direct:** `https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250920/18/atmos/gfs.t18z.pgrb2.0p25.f006`

### HRRR (High-Resolution Rapid Refresh)
- **Bucket:** `s3://noaa-hrrr-bdp-pds/`
- **Browse:** https://noaa-hrrr-bdp-pds.s3.amazonaws.com/
- **Path pattern:** `hrrr.YYYYMMDD/<domain>/hrrr.t<HH>z.<product>f<FF>.grib2`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-hrrr-bdp-pds/hrrr.20250920/conus/`

### RAP (Rapid Refresh)
- **Bucket:** `s3://noaa-rap-pds/`
- **Path pattern:** `rap.YYYYMMDD/rap.t<HH>z.<grid>.pgrbf<FF>.grib2`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-rap-pds/rap.20250920/12/`

### NAM (North American Mesoscale)
- **Bucket:** `s3://noaa-nam-pds/`
- **Browse:** https://noaa-nam-pds.s3.amazonaws.com/
- **Path pattern:** `nam.YYYYMMDD/nam.t<HH>z.<domain>.hiresf<FF>.tm00.grib2`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-nam-pds/nam.20250920/12/`

### RTMA/URMA (Surface analyses)
- **Bucket:** `s3://noaa-rtma-pds/`
- **Path pattern:** `rtma2p5.YYYYMMDD/rtma2p5.t<HH>z.*`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-rtma-pds/rtma2p5.20250920/`

---

## HISTORICAL / ARCHIVES & OPEN IMAGERY

### Sentinel-2 COGs (global optical imagery; non‑Requester‑Pays mirror)
- **HTTP base:** `https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/`
- **Discovery:** Use STAC: `https://earth-search.aws.element84.com/v1/`
- **Example HTTP asset:**  
  `https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/R/VU/2025/3/S2C_36RVU_20250313_0_L2A/TCI.tif`
- **GDAL (streaming):**  
  `gdalinfo /vsicurl/https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/R/VU/2025/3/S2C_36RVU_20250313_0_L2A/TCI.tif`
- **Note:** Avoid `sentinel-s2-l1c` and `sentinel-s2-l2a` buckets (Requester Pays).

### MODIS (Terra/Aqua) archive
- **Bucket:** `s3://modis-pds/`
- **Browse:** https://modis-pds.s3.amazonaws.com/
- **Path pattern:** `<Collection>/<Version>/<YYYY.MM.DD>/...` (HDF/GeoTIFF/COG depending on product)
- **CLI:** `aws s3 ls --no-sign-request s3://modis-pds/MCD43A4/`

### ISD Global Hourly / GHCN-Daily (station histories)
- **ISD bucket:** `s3://noaa-global-hourly-pds/`
- **Path pattern:** `YYYY/` followed by WMO station files (CSV/ish or fixed-width, plus inventories)
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-global-hourly-pds/2025/`
- **GHCN-D mirrors:** Use official NOAA mirrors when present; structure varies.

### MYRORSS (Reanalyzed radar storms)
- **Bucket:** `s3://noaa-oar-myrorss-pds/`
- **CLI:** `aws s3 ls --no-sign-request s3://noaa-oar-myrorss-pds/`
- **Use:** 3‑D reflectivity grids and derived severe metrics for research.

### HiRISE (Mars) — USGS/NASA cloud-optimized datasets
- **Controlled DTMs:** `s3://astrogeo-ard/mars/mro/hirise/controlled/dtm/`
- **Uncontrolled RDRs:** `s3://astrogeo-ard/mars/mro/hirise/uncontrolled_rdr_observations/`
- **CLI:**  
  `aws s3 ls --no-sign-request s3://astrogeo-ard/mars/mro/hirise/controlled/dtm/`

### World Ocean Database (WOD)
- **Bucket:** `s3://noaa-wod-pds/`
- **Browse:** https://noaa-wod-pds.s3.amazonaws.com/
- **Use:** Historical ocean temperature/salinity profiles (multi-century).

---

## EXACT ACCESS METHODS (copy/paste)

### AWS CLI (anonymous)
```bash
# List a bucket/prefix
aws s3 ls --no-sign-request s3://noaa-goes19/ABI-L2-MCMIPC/2025/09/20/

# Download a single object
aws s3 cp --no-sign-request s3://noaa-hrrr-bdp-pds/hrrr.20250920/conus/hrrr.t12z.wrfsfcf00.grib2 .

# Recursively sync a small subset (be selective)
aws s3 sync --no-sign-request s3://unidata-nexrad-level2/2025/09/20/KTLX/ ./radar/KTLX/ --exclude "*" --include "*210000*"
```

### Plain HTTP(S)
```bash
# Direct file download
curl -L -O "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250920/18/atmos/gfs.t18z.pgrb2.0p25.f006"

# Sentinel-2 COG (streams with range requests)
wget "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/R/VU/2025/3/S2C_36RVU_20250313_0_L2A/TCI.tif"
```

### GDAL / Rasterio (stream without download)
```bash
# Inspect a COG over HTTP
gdalinfo /vsicurl/https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/R/VU/2025/3/S2C_36RVU_20250313_0_L2A/TCI.tif

# Translate a subwindow from a NetCDF over HTTPS (example: GOES ABI L2 MCMIPC)
gdal_translate -srcwin 0 0 2048 2048 \
  /vsicurl/https://noaa-goes18.s3.amazonaws.com/ABI-L2-MCMIPC/2025/263/12/OR_ABI-L2-MCMIPC-M6_G18_s20252631200200_e20252631209518_c20252631210001.nc \
  goes18_mcmipc_crop.tif
```

### STAC (Earth Search v1 — unauthenticated)
```bash
# Example Sentinel-2 L2A COG search (GeoJSON)
curl -s "https://earth-search.aws.element84.com/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
        "collections":["sentinel-2-l2a"],
        "bbox":[34.9,31.1,35.1,31.3],
        "datetime":"2025-03-10/2025-03-15",
        "limit":5,
        "query":{"eo:cloud_cover":{"lt":20}}
      }' | jq '.features[].assets.TCI.href'
```

---

## DO NOT USE (violates zero-cost constraint)
- **USGS Landsat Collection-2 buckets** (`usgs-landsat*`, `usgs-landsat/collection02/*`) — Requester Pays.
- **Sentinel-2 core buckets** (`sentinel-s2-l1c`, `sentinel-s2-l2a`, `*-zips`) — Requester Pays.
- Any dataset that demands credentials, tokens, sign-in, or paid egress.

---

## Minimal provider index (for agents/tools)
- GOES: `noaa-goes19`, `noaa-goes18`  
- JPSS: `noaa-nesdis-n20-pds`, `noaa-nesdis-n21-pds`, `noaa-nesdis-snpp-pds`  
- NEXRAD: `unidata-nexrad-level2`, `unidata-nexrad-level2-chunks`, `unidata-nexrad-level3`  
- MRMS: `noaa-mrms-pds`  
- GFS: `noaa-gfs-bdp-pds`  
- HRRR: `noaa-hrrr-bdp-pds`  
- RAP: `noaa-rap-pds`  
- NAM: `noaa-nam-pds`  
- RTMA/URMA: `noaa-rtma-pds`  
- ISD Global Hourly: `noaa-global-hourly-pds`  
- Sentinel-2 COGs (non‑RP): `sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/...`

