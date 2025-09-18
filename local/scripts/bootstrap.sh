#!/usr/bin/env bash
set -euo pipefail

# Bootstrap helper for local stack
# - Creates MinIO buckets if mc is installed and MinIO reachable
# - Prints connection info for Postgres and MinIO

: "${MINIO_ENDPOINT:=http://localhost:9000}"
: "${MINIO_ROOT_USER:=localminio}"
: "${MINIO_ROOT_PASSWORD:=change-me-now}"
: "${S3_BUCKET_RAW:=raw}"
: "${S3_BUCKET_DERIVED:=derived}"
: "${S3_BUCKET_TILES:=tiles}"
: "${S3_BUCKET_LOGS:=logs}"

info() { echo "[bootstrap] $*"; }

if command -v mc >/dev/null 2>&1; then
  info "Configuring MinIO client alias 'local' -> ${MINIO_ENDPOINT}"
  mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" || true
  info "Ensuring buckets exist"
  mc mb -p "local/${S3_BUCKET_RAW}" || true
  mc mb -p "local/${S3_BUCKET_DERIVED}" || true
  mc mb -p "local/${S3_BUCKET_TILES}" || true
  mc mb -p "local/${S3_BUCKET_LOGS}" || true
else
  info "MinIO client (mc) not installed; skipping bucket creation"
fi

info "MinIO console: ${MINIO_ENDPOINT} (user=${MINIO_ROOT_USER})"
info "Postgres: postgresql://osm:***@localhost:5432/osm"
