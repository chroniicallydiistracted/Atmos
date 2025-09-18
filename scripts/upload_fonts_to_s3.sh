#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <fonts-pbf-dir> <s3://bucket/path>" >&2
  exit 2
fi

SRC_DIR="$1"
DEST_S3="$2"

if [ ! -d "$SRC_DIR" ]; then
  echo "Source directory not found: $SRC_DIR" >&2
  exit 1
fi

echo "Uploading fonts from $SRC_DIR to $DEST_S3 (safe sync, no delete)"
aws s3 sync "$SRC_DIR/" "$DEST_S3/" \
  --exclude "*" --include "**/*.pbf" --exact-timestamps

echo "Done."
