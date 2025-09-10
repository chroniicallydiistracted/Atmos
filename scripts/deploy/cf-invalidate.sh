#!/usr/bin/env bash
set -euo pipefail

DISTRIBUTION_ID=${1:-}
PATHS=${2:-"/*"}

if [ -z "$DISTRIBUTION_ID" ]; then
  echo "Usage: $0 <distribution-id> [paths]"
  echo "Example: $0 E1234567890ABC '/styles/* /sprites/*'"
  exit 1
fi

echo "Creating CloudFront invalidation for distribution: $DISTRIBUTION_ID"
echo "Paths: $PATHS"

aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths $PATHS \
  --query 'Invalidation.{Id:Id,Status:Status,CreateTime:CreateTime}' \
  --output table

echo "Invalidation created successfully"