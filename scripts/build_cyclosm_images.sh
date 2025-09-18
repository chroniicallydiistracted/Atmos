#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "== Building images =="
# Renderer (use repo root as build context so CyclOSM-CSS-Master is available to COPY)
docker build -f ./services/cyclosm/renderer/Dockerfile -t cyclosm-renderer:local .
# Importer
docker build -t cyclosm-importer:local ./services/cyclosm/importer
# Hillshade
docker build -t cyclosm-hillshade:local ./services/cyclosm/hillshade
# Fonts
docker build -f ./services/cyclosm/fonts/Dockerfile.fonts -t cyclosm-fonts:local ./services/cyclosm/fonts

echo "Built: cyclosm-renderer, cyclosm-importer, cyclosm-hillshade, cyclosm-fonts"
