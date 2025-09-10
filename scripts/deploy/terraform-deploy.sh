#!/usr/bin/env bash
set -euo pipefail

# Deploy AtmosInsight infrastructure using Terraform

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(cd "$SCRIPT_DIR/../../infra/terraform" && pwd)"
ENV=${1:-us-east-1}

echo "Deploying AtmosInsight infrastructure..."
echo "Environment: $ENV"

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Validate configuration
echo "🔍 Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -var-file="env/$ENV.tfvars" -out="tfplan-$ENV"

echo ""
echo "Terraform plan created: tfplan-$ENV"
echo ""
echo "Review the plan above. To apply:"
echo "  cd $TERRAFORM_DIR"
echo "  terraform apply tfplan-$ENV"
echo ""
echo "To destroy (when done):"
echo "  terraform destroy -var-file=env/$ENV.tfvars"