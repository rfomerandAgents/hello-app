#!/bin/bash
set -e

echo "=== Destroying Infrastructure ==="
echo "WARNING: This will destroy all infrastructure resources!"

cd "$(dirname "$0")/.."

# Ask for confirmation
read -p "Type 'DESTROY' to confirm: " confirm
if [ "$confirm" != "DESTROY" ]; then
    echo "Destruction cancelled"
    exit 0
fi

# Destroy infrastructure
terraform destroy

echo "Infrastructure destroyed"
