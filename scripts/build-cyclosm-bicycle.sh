#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 --planet PATH [--output PATH] [--bbox minLon,minLat,maxLon,maxLat] [--networks list]

Required arguments:
  --planet PATH           Path to a planet or regional OSM PBF extract

Optional:
  --output PATH           Output PMTiles path (default: local/data/basemaps/cyclosm-bicycle.pmtiles)
  --bbox lon1,lat1,lon2,lat2  Restrict input to a bounding box before processing
  --networks list         Comma-separated set of network codes to keep (default: lcn,rcn,ncn,icn)

This script builds CyclOSM-style bicycle route overlays using Dockerized
osmium-tool, tippecanoe, and go-pmtiles. It requires Docker Engine.
USAGE
}

PLANET=""
OUTPUT="local/data/basemaps/cyclosm-bicycle.pmtiles"
BBOX=""
NETWORKS="lcn,rcn,ncn,icn"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --planet)
      PLANET=${2:-}
      shift 2
      ;;
    --output)
      OUTPUT=${2:-}
      shift 2
      ;;
    --bbox)
      BBOX=${2:-}
      shift 2
      ;;
    --networks)
      NETWORKS=${2:-}
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$PLANET" ]]; then
  echo "--planet argument is required" >&2
  usage
  exit 1
fi

if [[ ! -f "$PLANET" ]]; then
  echo "Planet extract not found: $PLANET" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run this script." >&2
  exit 1
fi

ABS_OUTPUT=$(python3 - <<'PY'
import os, sys
print(os.path.abspath(sys.argv[1]))
PY
"$OUTPUT")
OUTPUT_DIR=$(dirname "$ABS_OUTPUT")
OUTPUT_FILE=$(basename "$ABS_OUTPUT")
mkdir -p "$OUTPUT_DIR"

WORKDIR=$(mktemp -d 2>/dev/null || mktemp -d -t cyclosm-bicycle)
cleanup() {
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

PLANET_DIR=$(python3 - <<'PY'
import os, sys
print(os.path.abspath(os.path.dirname(sys.argv[1])))
PY
"$PLANET")
PLANET_FILE=$(basename "$PLANET")

FILTERED_INPUT="/input/$PLANET_FILE"

if [[ -n "$BBOX" ]]; then
  echo "== Extracting bbox $BBOX =="
  docker run --rm \
    -v "$PLANET_DIR":/input:ro \
    -v "$WORKDIR":/work \
    mschilde/osmium-tool \
    osmium extract --overwrite -b "$BBOX" -o /work/extract.pbf "$FILTERED_INPUT"
  FILTERED_INPUT="/work/extract.pbf"
fi

echo "== Filtering bicycle relations =="
docker run --rm \
  -v "$PLANET_DIR":/input:ro \
  -v "$WORKDIR":/work \
  mschilde/osmium-tool \
  osmium tags-filter --overwrite -R "$FILTERED_INPUT" \
    r/route=bicycle -o /work/bicycle_routes_raw.pbf

NETWORK_ARGS=()
IFS=',' read -ra NETLIST <<<"$NETWORKS"
for net in "${NETLIST[@]}"; do
  net=$(echo "$net" | xargs)
  [[ -z "$net" ]] && continue
  NETWORK_ARGS+=("r/network=$net")
done

if [[ ${#NETWORK_ARGS[@]} -gt 0 ]]; then
  echo "== Restricting networks: ${NETWORK_ARGS[*]} =="
  docker run --rm \
    -v "$WORKDIR":/work \
    mschilde/osmium-tool \
    osmium tags-filter --overwrite -R /work/bicycle_routes_raw.pbf \
      "${NETWORK_ARGS[@]}" -o /work/bicycle_routes_net.pbf
  INPUT_PBF="/work/bicycle_routes_net.pbf"
else
  INPUT_PBF="/work/bicycle_routes_raw.pbf"
fi

echo "== Exporting GeoJSON sequence =="
docker run --rm \
  -v "$WORKDIR":/work \
  mschilde/osmium-tool \
  osmium export --geometry-type=linestring --output-format=geojsonseq \
    "$INPUT_PBF" -o /work/bicycle_routes.geojsonl

echo "== Filtering features by network =="
python3 - <<'PY'
import json
import pathlib
import sys

work = pathlib.Path(sys.argv[1])
networks = {n.strip().lower() for n in sys.argv[2].split(',') if n.strip()}
input_path = work / "bicycle_routes.geojsonl"
output_path = work / "bicycle_routes.filtered.geojsonl"
count_in = 0
count_out = 0
with input_path.open('r', encoding='utf-8') as src, output_path.open('w', encoding='utf-8') as dst:
    for line in src:
        if not line.strip():
            continue
        count_in += 1
        feature = json.loads(line)
        props = feature.get('properties') or {}
        network = str(props.get('network', '')).lower()
        if networks and network not in networks:
            continue
        geom = feature.get('geometry') or {}
        if geom.get('type') not in {'LineString', 'MultiLineString'}:
            continue
        dst.write(json.dumps(feature, ensure_ascii=False) + '\n')
        count_out += 1
print(f"Filtered features: {count_out}/{count_in}")
if count_out == 0:
    print("ERROR: No bicycle features matched the filters.", file=sys.stderr)
    sys.exit(1)
PY
"$WORKDIR" "$NETWORKS"

echo "== Building MBTiles with tippecanoe =="
docker run --rm \
  -v "$WORKDIR":/work \
  klokantech/tippecanoe \
  tippecanoe --force --read-parallel \
    --layer=bicycle_routes \
    --no-tile-compression \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    --simplification=4 \
    --minimum-zoom=6 \
    --maximum-zoom=14 \
    -o /work/bicycle_routes.mbtiles \
    /work/bicycle_routes.filtered.geojsonl

echo "== Converting to PMTiles =="
docker run --rm \
  -v "$WORKDIR":/work \
  -v "$OUTPUT_DIR":/out \
  protomaps/go-pmtiles \
  go-pmtiles convert /work/bicycle_routes.mbtiles /out/"$OUTPUT_FILE"

echo "Wrote $ABS_OUTPUT"
