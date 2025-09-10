#!/usr/bin/env bash
set -euo pipefail

# Set up ECR repositories for AtmosInsight Lambda container images

REGION=${1:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Setting up ECR repositories in region: $REGION"
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# List of Lambda services that use container images
SERVICES=(
    "atmosinsight-tiler"
    "atmosinsight-radar-prepare" 
    "atmosinsight-goes-prepare"
    "atmosinsight-mrms-prepare"
    "atmosinsight-alerts-bake"
)

# Create ECR repositories
for SERVICE in "${SERVICES[@]}"; do
    echo "Creating ECR repository: $SERVICE"
    
    aws ecr create-repository \
        --repository-name "$SERVICE" \
        --region "$REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --output table \
        2>/dev/null || echo "Repository $SERVICE already exists"
        
    # Set lifecycle policy to keep only latest 10 images
    aws ecr put-lifecycle-policy \
        --repository-name "$SERVICE" \
        --region "$REGION" \
        --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "selection": {
                        "tagStatus": "untagged",
                        "countType": "sinceImagePushed",
                        "countUnit": "days",
                        "countNumber": 1
                    },
                    "action": {
                        "type": "expire"
                    }
                },
                {
                    "rulePriority": 2,
                    "selection": {
                        "tagStatus": "tagged",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }' > /dev/null
        
    echo "✅ Repository $SERVICE configured with lifecycle policy"
done

echo ""
echo "ECR Setup Complete!"
echo ""
echo "Repository URIs:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  $SERVICE: $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$SERVICE"
done

echo ""
echo "Next steps:"
echo "1. Build and push container images:"
echo "   ./scripts/deploy/build-and-push-containers.sh"
echo ""
echo "2. Update Terraform lambda_image_uri variables with these URIs"