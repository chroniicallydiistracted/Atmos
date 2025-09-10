#!/usr/bin/env bash
set -euo pipefail

# Build and package Lambda functions for deployment

SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/services"
BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/build"

echo "Building Lambda functions..."

# Create build directory
mkdir -p "$BUILD_DIR"

# Function to build zip-based Lambda
build_zip_lambda() {
  local service=$1
  echo "Building $service (zip)..."
  
  cd "$SERVICES_DIR/$service"
  
  # Create virtual environment and install dependencies
  python3 -m venv venv
  source venv/bin/activate
  
  if [ -f requirements.txt ]; then
    pip install -r requirements.txt -t ./package/
  fi
  
  # Copy handler
  cp handler.py ./package/
  
  # Create zip
  cd package
  zip -r "$BUILD_DIR/$service.zip" .
  
  # Cleanup
  cd "$SERVICES_DIR/$service"
  rm -rf venv package
  
  echo "✓ Built $service.zip"
}

# Function to build container-based Lambda
build_container_lambda() {
  local service=$1
  echo "Building $service (container)..."
  
  cd "$SERVICES_DIR/$service"
  
  if [ ! -f Dockerfile ]; then
    echo "⚠ No Dockerfile found for $service, skipping"
    return
  fi
  
  # Build container image
  docker build -t "atmosinsight-$service:latest" .
  
  echo "✓ Built $service container image"
}

# Build healthz as zip (simple function)
if [ -d "$SERVICES_DIR/healthz" ]; then
  build_zip_lambda "healthz"
fi

# Build other services as containers (if Docker is available)
if command -v docker >/dev/null 2>&1; then
  for service in tiler radar-prepare goes-prepare mrms-prepare alerts-bake; do
    if [ -d "$SERVICES_DIR/$service" ]; then
      build_container_lambda "$service"
    fi
  done
else
  echo "⚠ Docker not available, container builds skipped"
  echo "  Install Docker to build container-based Lambda functions"
fi

echo ""
echo "Lambda build complete!"
echo "Zip files available in: $BUILD_DIR"
echo "Container images tagged with: atmosinsight-*:latest"