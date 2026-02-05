#!/bin/bash
set -e

echo "=== Deploying Infrastructure ==="

cd "$(dirname "$0")/.."

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=tfplan

# Ask for confirmation
read -p "Apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply changes
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo "Deployment complete!"
terraform output
