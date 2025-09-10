#!/usr/bin/env bash
set -euo pipefail

# Upload static assets to S3 and invalidate CloudFront

BUCKET_NAME=${1:-}
DISTRIBUTION_ID=${2:-}

if [ -z "$BUCKET_NAME" ]; then
  echo "Usage: $0 <bucket-name> [distribution-id]"
  echo "Example: $0 atmosinsight-static-abc123 E1234567890ABC"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Uploading static assets to $BUCKET_NAME..."

# Build frontend
echo "🔨 Building frontend..."
cd "$PROJECT_ROOT/web"
npm run build

# Upload SPA files
echo "📤 Uploading SPA files..."
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
  --exclude "*.map" \
  --cache-control "public, max-age=86400" \
  --metadata-directive REPLACE

# Upload static assets with longer cache
echo "📤 Uploading static assets..."
if [ -d "$PROJECT_ROOT/web-static" ]; then
  aws s3 sync "$PROJECT_ROOT/web-static/" "s3://$BUCKET_NAME/" \
    --cache-control "public, max-age=31536000" \
    --metadata-directive REPLACE
fi

# Set proper content types for specific files
echo "🏷️ Setting content types..."

# PMTiles
aws s3 cp "s3://$BUCKET_NAME/basemaps/" "s3://$BUCKET_NAME/basemaps/" \
  --recursive \
  --exclude "*" \
  --include "*.pmtiles" \
  --content-type "application/octet-stream" \
  --metadata-directive REPLACE \
  || echo "No PMTiles found"

# Vector fonts
aws s3 cp "s3://$BUCKET_NAME/fonts/" "s3://$BUCKET_NAME/fonts/" \
  --recursive \
  --exclude "*" \
  --include "*.pbf" \
  --content-type "application/x-protobuf" \
  --metadata-directive REPLACE \
  || echo "No fonts found"

# Style JSON
aws s3 cp "s3://$BUCKET_NAME/styles/" "s3://$BUCKET_NAME/styles/" \
  --recursive \
  --exclude "*" \
  --include "*.json" \
  --content-type "application/json" \
  --metadata-directive REPLACE \
  || echo "No styles found"

# Invalidate CloudFront
if [ -n "$DISTRIBUTION_ID" ]; then
  echo "🔄 Invalidating CloudFront..."
  aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.{Id:Id,Status:Status}' \
    --output table
else
  echo "⚠️ No distribution ID provided, skipping CloudFront invalidation"
fi

echo "✅ Static assets uploaded successfully!"