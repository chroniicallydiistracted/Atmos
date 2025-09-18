#!/usr/bin/env bash
set -euo pipefail

# Local MinIO-based MBTiles -> PMTiles conversion (no AWS)
# Requires pmtiles and MinIO client (mc). Uses env: MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, S3_BUCKET_DERIVED

# Inputs (can be overridden via env)
S3_BUCKET_DERIVED=${S3_BUCKET_DERIVED:-derived}
S3_PATH=${S3_PATH:-basemaps/maptiler-osm-2020-02-10-v3.11-planet.mbtiles}
MBTILES_FILE=${MBTILES_FILE:-maptiler-osm-2020-02-10-v3.11-planet.mbtiles}
PMTILES_FILE=${PMTILES_FILE:-maptiler-osm-2020-02-10-v3.11-planet.pmtiles}
MINIO_ENDPOINT=${MINIO_ENDPOINT:-http://localhost:9000}
MINIO_ALIAS=${MINIO_ALIAS:-local}

echo "🔍 Verifying setup..."
command -v pmtiles >/dev/null || { echo "pmtiles not found"; exit 1; }
command -v mc >/dev/null || { echo "MinIO client 'mc' not found"; exit 1; }
pmtiles --version
echo "✅ Ready to start conversion"

echo "🔐 Configuring MinIO alias ($MINIO_ALIAS -> $MINIO_ENDPOINT)"
mc alias set "$MINIO_ALIAS" "$MINIO_ENDPOINT" "${MINIO_ROOT_USER:-localminio}" "${MINIO_ROOT_PASSWORD:-change-me-now}" >/dev/null

echo "📋 Checking source in MinIO..."
mc ls "$MINIO_ALIAS/$S3_BUCKET_DERIVED/basemaps/" | grep -E "maptiler|$MBTILES_FILE" || true

echo "📥 Downloading from MinIO..."
echo "Source: $MINIO_ALIAS/$S3_BUCKET_DERIVED/$S3_PATH"
mc cp "$MINIO_ALIAS/$S3_BUCKET_DERIVED/$S3_PATH" "/data/$MBTILES_FILE"

echo "📊 File downloaded:"
ls -lh "/data/$MBTILES_FILE"

echo "🔄 Converting to PMTiles..."
mkdir -p /data/temp
time pmtiles convert "/data/$MBTILES_FILE" "/data/$PMTILES_FILE" --tmpdir /data/temp

echo "📊 Conversion complete:"
ls -lh "/data/$PMTILES_FILE"
pmtiles show "/data/$PMTILES_FILE" | head -n 20 || true

echo "📤 Uploading to MinIO..."
DEST_PATH="basemaps/$PMTILES_FILE"
echo "Destination: $MINIO_ALIAS/$S3_BUCKET_DERIVED/$DEST_PATH"
mc cp "/data/$PMTILES_FILE" "$MINIO_ALIAS/$S3_BUCKET_DERIVED/$DEST_PATH"

echo "✅ Upload complete! Verifying..."
mc ls "$MINIO_ALIAS/$S3_BUCKET_DERIVED/$DEST_PATH"

echo "📁 Files in basemaps folder:"
mc ls "$MINIO_ALIAS/$S3_BUCKET_DERIVED/basemaps/"

echo "🧹 Cleaning up local files..."
rm -f "/data/$MBTILES_FILE" "/data/$PMTILES_FILE"
rm -rf /data/temp

echo "🎉 CONVERSION COMPLETE!"
echo "📁 Original: $MINIO_ALIAS/$S3_BUCKET_DERIVED/$S3_PATH"
echo "📁 Converted: $MINIO_ALIAS/$S3_BUCKET_DERIVED/basemaps/$PMTILES_FILE"
