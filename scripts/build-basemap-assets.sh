#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'HELP'
Usage: ./local/scripts/build-basemap-assets.sh [options]

Options:
  --bicycle-pbf PATH       Path to an OSM PBF file used to extract bicycle routes.
  --hillshade-dem PATH     Path to a DEM GeoTIFF (or directory of tiles) used for hillshade generation.
  --output-dir PATH        Directory where resulting PMTiles files will be written (default: local/data/basemaps).
  --work-dir PATH          Temporary working directory (default: system temp dir).
  --bbox WEST,SOUTH,EAST,NORTH
                           Optional bounding box (degrees) applied when extracting bicycle data.
  --simplification VALUE   Tippecanoe simplification value for bicycle routes (default: 4).
  --max-zoom VALUE         Maximum zoom for generated bicycle routes (default: 14).
  --hillshade-zoom VALUE   Maximum zoom for hillshade PMTiles (default: 15).
  --dry-run                Print the commands that would run without executing them.
  -h, --help               Show this help message.

The script produces the mandatory bicycle overlay and hillshade PMTiles the
basemap expects. `osmium`, `tippecanoe`, and `pmtiles` must be available for the
vector steps; hillshade generation additionally requires GDAL utilities
(`gdal_translate`, `gdaldem`, `gdalbuildvrt`). Commands are run in a staging
directory so intermediate artefacts can be inspected between steps.
HELP
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_command() {
  if ! command_exists "$1"; then
    echo "Error: required command '$1' not found in PATH" >&2
    exit 2
  fi
}

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] $*"
  else
    echo "[run] $*"
    "$@"
  fi
}

BICYCLE_PBF=""
HILLSHADE_DEM=""
OUTPUT_DIR="local/data/basemaps"
WORK_DIR=""
BBOX=""
SIMPLIFICATION="4"
MAX_ZOOM="14"
HILLSHADE_MAX_ZOOM="15"
DRY_RUN="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bicycle-pbf)
      BICYCLE_PBF="$2"
      shift 2
      ;;
    --hillshade-dem)
      HILLSHADE_DEM="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --work-dir)
      WORK_DIR="$2"
      shift 2
      ;;
    --bbox)
      BBOX="$2"
      shift 2
      ;;
    --simplification)
      SIMPLIFICATION="$2"
      shift 2
      ;;
    --max-zoom)
      MAX_ZOOM="$2"
      shift 2
      ;;
    --hillshade-zoom)
      HILLSHADE_MAX_ZOOM="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="1"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$WORK_DIR" ]]; then
  WORK_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t basemap-build)"
  trap 'rm -rf "$WORK_DIR"' EXIT
else
  mkdir -p "$WORK_DIR"
fi

mkdir -p "$OUTPUT_DIR"

extract_bicycle_routes() {
  ensure_command osmium
  ensure_command tippecanoe

  if [[ ! -f "$BICYCLE_PBF" ]]; then
    echo "Error: bicycle PBF '$BICYCLE_PBF' not found" >&2
    exit 1
  fi

  local filtered_pbf="$WORK_DIR/bicycle_routes.osm.pbf"
  local tippecanoe_output="$OUTPUT_DIR/cyclosm-bicycles.pmtiles"

  echo "Generating bicycle routes PMTiles at $tippecanoe_output"

  if [[ -n "$BBOX" ]]; then
    local bbox_file="$WORK_DIR/bbox_extract.osm.pbf"
    echo "Clipping to bounding box $BBOX"
    run osmium extract --bbox "$BBOX" "$BICYCLE_PBF" -o "$bbox_file"
    BICYCLE_PBF="$bbox_file"
  fi

  run osmium tags-filter "$BICYCLE_PBF" \
    r/highway=cycleway \
    w/network=icn,rcn,lcn,ncn \
    -o "$filtered_pbf"

  run tippecanoe \
    --layer=bicycle_routes \
    --no-tile-compression \
    --simplification="$SIMPLIFICATION" \
    --maximum-zoom="$MAX_ZOOM" \
    --force \
    -o "$tippecanoe_output" \
    "$filtered_pbf"
}

generate_hillshade() {
  ensure_command gdal_translate
  ensure_command gdaldem
  ensure_command pmtiles

  local hillshade_tif="$WORK_DIR/hillshade.tif"
  local hillshade_pmtiles="$OUTPUT_DIR/hillshade.pmtiles"

  echo "Generating hillshade PMTiles at $hillshade_pmtiles"

  if [[ -d "$HILLSHADE_DEM" ]]; then
    echo "Mosaicking DEM tiles under $HILLSHADE_DEM"
    local vrt="$WORK_DIR/dem.vrt"
    ensure_command gdalbuildvrt
    run gdalbuildvrt "$vrt" "$HILLSHADE_DEM"/*.tif
    HILLSHADE_DEM="$vrt"
  fi

  run gdal_translate -co TILED=YES -co COMPRESS=DEFLATE "$HILLSHADE_DEM" "$WORK_DIR/dem-tiled.tif"

  run gdaldem hillshade "$WORK_DIR/dem-tiled.tif" "$hillshade_tif" -compute_edges -multidirectional

  run pmtiles convert "$hillshade_tif" "$hillshade_pmtiles" --maxzoom "$HILLSHADE_MAX_ZOOM"
}

if [[ -n "$BICYCLE_PBF" ]]; then
  extract_bicycle_routes
elif [[ ! -f "$OUTPUT_DIR/cyclosm-bicycles.pmtiles" ]]; then
  echo "WARNING: bicycle overlay PMTiles missing at $OUTPUT_DIR/cyclosm-bicycles.pmtiles" >&2
  echo "         Run this script with --bicycle-pbf or supply the file manually." >&2
fi

if [[ -n "$HILLSHADE_DEM" ]]; then
  generate_hillshade
elif [[ ! -f "$OUTPUT_DIR/hillshade.pmtiles" ]]; then
  echo "WARNING: hillshade PMTiles missing at $OUTPUT_DIR/hillshade.pmtiles" >&2
  echo "         Run this script with --hillshade-dem or supply the file manually." >&2
fi

echo "Basemap asset generation checks complete."
