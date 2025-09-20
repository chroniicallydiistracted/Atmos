# NEXRAD Ingestion Validation Guide

This document provides a concise end-to-end manual validation workflow for the local NEXRAD ingestion → storage → tiling → legend metadata path.

## 1. Preconditions
- Stack running with profiles: `core,ingestion,frontend`.
- Environment contains:
  - `NEXRAD_ENABLED=true`
  - `API_CORS_ORIGINS` includes `http://localhost` and `http://localhost:4173`.
- Services healthy: `reverse-proxy`, `api`, `ingestion`, `tiler`, `frontend`, `object-store`.

## 2. Trigger Ingestion (Via API Proxy)
```bash
curl -s -X POST http://localhost/api/v1/trigger/nexrad \
  -H 'Content-Type: application/json' \
  -d '{"parameters":{"site":"KTLX"}}' | jq
```
Expected JSON fields:
- `job: "nexrad"`
- `status: "ok"`
- `detail.site`, `detail.cog_key`, `detail.meta_key`, `detail.tile_template`, `detail.timestamp_key`.

Export useful variables:
```bash
RESP=$(curl -s -X POST http://localhost/api/v1/trigger/nexrad -H 'Content-Type: application/json' -d '{"parameters":{"site":"KTLX"}}')
TS_KEY=$(echo "$RESP" | jq -r '.detail.timestamp_key')
SITE=$(echo "$RESP" | jq -r '.detail.site')
META_URL=$(echo "$RESP" | jq -r '.detail.meta_url')
TILE_TEMPLATE=$(echo "$RESP" | jq -r '.detail.tile_template')
echo TS_KEY=$TS_KEY SITE=$SITE META_URL=$META_URL TILE_TEMPLATE=$TILE_TEMPLATE
```

## 3. Inspect Stored Objects (MinIO)
List derived objects for this run:
```bash
mc alias set local http://localhost:9000 localminio change-me-now >/dev/null 2>&1 || true
mc ls local/derived/nexrad/${SITE}/${TS_KEY}/
```
Expect at least:
- `tilt0_reflectivity.tif`
- `meta.json`

## 4. Fetch Metadata Directly
```bash
curl -s "http://localhost${META_URL}" | jq '.units, .rescale'
```
Expect: `"dBZ"` then `[-30, 80]`.

## 5. Legend Endpoint
```bash
curl -s http://localhost/api/v1/legend/nexrad/${SITE}/${TS_KEY} | jq
```
Expect top-level `legend` object with `units`, `rescale`, `palette`.

## 6. Fetch a Sample Tile
Derive z/x/y (use small zoom first, e.g. z=4). Example path:
```bash
curl -o /tmp/sample.png \
  "http://localhost/tiles/weather/nexrad-${SITE}/${TS_KEY}/4/2/5.png"
file /tmp/sample.png
```
`file` should report PNG image data; size likely small if mostly transparent.

## 7. Frontend Verification
- Open `http://localhost/`.
- Toggle "Show Radar" → Network tab shows POST to `/api/v1/trigger/nexrad` (200) then tile GETs under `/tiles/weather/...`.
- (Optional) After tiles load, call legend endpoint in DevTools console:
```js
fetch(`/api/v1/legend/nexrad/${SITE}/${TS_KEY}`).then(r=>r.json()).then(console.log)
```

## 8. Common Issues & Remedies
| Symptom | Cause | Fix |
|---------|-------|-----|
| 404 legend | Wrong timestamp key or site case | Use uppercase site; confirm directory exists in MinIO |
| 502 trigger | Ingestion internal error | Check `docker logs ingestion` for stack trace |
| 500 trigger with CORS miss | Direct call to backend port (8081) without proper origin | Use `/api` proxy or ensure origin in `API_CORS_ORIGINS` |
| Transparent tiles only | Low reflectivity or area outside radar range | Try different site (e.g. KTLX, KDMX) or smaller lookback |
| Slow tile responses | First-time raster reads & internal caching | Subsequent requests faster; consider adding caching layer later |

## 9. Cleanup (Optional)
Remove generated run to re-test fresh:
```bash
mc rm -r --force local/derived/nexrad/${SITE}/${TS_KEY}
```

---
Validation complete when all steps succeed without errors.
