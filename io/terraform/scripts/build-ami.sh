#!/bin/bash
set -e

echo "=== Building AMI with Packer ==="

cd "$(dirname "$0")/../.."

# Navigate to packer directory
cd packer

# Initialize Packer
packer init app.pkr.hcl

# Validate template
packer validate app.pkr.hcl

# Build AMI
packer build app.pkr.hcl

echo "AMI build complete!"
