#!/usr/bin/env bash
set -euo pipefail

# Build and push Lambda container images to ECR

REGION=${1:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/services"

echo "Building and pushing Lambda containers..."
echo "Region: $REGION"
echo "Account: $AWS_ACCOUNT_ID"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | \
    docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Services with container images
declare -A SERVICES=(
    ["tiler"]="atmosinsight-tiler"
    ["radar-prepare"]="atmosinsight-radar-prepare"
    ["goes-prepare"]="atmosinsight-goes-prepare"
    ["mrms-prepare"]="atmosinsight-mrms-prepare"
    ["alerts-bake"]="atmosinsight-alerts-bake"
)

# Build and push each service
for SERVICE_DIR in "${!SERVICES[@]}"; do
    SERVICE_NAME="${SERVICES[$SERVICE_DIR]}"
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$SERVICE_NAME"
    
    echo ""
    echo "🔨 Building $SERVICE_NAME..."
    
    cd "$SERVICES_DIR/$SERVICE_DIR"
    
    if [ ! -f Dockerfile ]; then
        echo "⚠️  No Dockerfile found for $SERVICE_DIR, skipping"
        continue
    fi
    
    # Build image with platform specification for Lambda
    docker build \
        --platform linux/amd64 \
        -t "$SERVICE_NAME:latest" \
        -t "$ECR_URI:latest" \
        -t "$ECR_URI:$(date +%Y%m%d-%H%M%S)" \
        .
    
    echo "📤 Pushing $SERVICE_NAME to ECR..."
    
    # Push all tags
    docker push "$ECR_URI:latest"
    docker push "$ECR_URI:$(date +%Y%m%d-%H%M%S)"
    
    echo "✅ $SERVICE_NAME pushed successfully"
    echo "   URI: $ECR_URI:latest"
done

echo ""
echo "🎉 All container images built and pushed successfully!"
echo ""
echo "Update your Terraform configuration with these URIs:"
echo ""

for SERVICE_DIR in "${!SERVICES[@]}"; do
    SERVICE_NAME="${SERVICES[$SERVICE_DIR]}"
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$SERVICE_NAME"
    echo "  $SERVICE_DIR: $ECR_URI:latest"
done

echo ""
echo "Then apply Terraform changes:"
echo "  cd infra/terraform"
echo "  terraform plan -var-file=env/us-east-1.tfvars"
echo "  terraform apply"