#!/usr/bin/env bash
set -euo pipefail

MBTILES=${1:-planet.mbtiles}
OUT=${2:-planet.z15.pmtiles}

command -v pmtiles >/dev/null 2>&1 || { 
  echo "Install pmtiles: https://github.com/protomaps/PMTiles"; 
  exit 1; 
}

pmtiles convert "$MBTILES" "$OUT"
echo "Wrote $OUT"