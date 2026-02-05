#!/bin/bash
set -e

# Manual Build and Deploy Script
# This script uses Packer and Terraform binaries directly (no Python wrappers)
# to build a fresh AMI and deploy it to AWS.

echo "========================================="
echo "Manual AMI Build and Deploy"
echo "========================================="
echo ""

# Configuration
REPO_ROOT="{{REPO_PATH}}"
PACKER_DIR="$REPO_ROOT/io/packer"
TERRAFORM_DIR="$REPO_ROOT/io/terraform"
APP_DIR="$REPO_ROOT/app"
AMI_NAME="{{PROJECT_SLUG}}-dev-v0.1.0"
VERSION="v0.1.0"
ENVIRONMENT="dev"

echo "Step 1: Clean local build artifacts"
echo "========================================="
cd "$APP_DIR"
rm -rf out .next node_modules/.cache .DS_Store
echo "✓ Cleaned build artifacts"
echo ""

echo "Step 2: Initialize Packer"
echo "========================================="
cd "$PACKER_DIR"
packer init app.pkr.hcl
echo "✓ Packer initialized"
echo ""

echo "Step 3: Validate Packer template"
echo "========================================="
packer validate app.pkr.hcl
echo "✓ Packer template validated"
echo ""

echo "Step 4: Build AMI with Packer (this takes 5-10 minutes)"
echo "========================================="
export PACKER_LOG=1
packer build \
  -var "ami_name=$AMI_NAME" \
  -var "version=$VERSION" \
  -var "environment=$ENVIRONMENT" \
  -var "app_source_path=$APP_DIR/" \
  app.pkr.hcl 2>&1 | tee /tmp/packer-build.log

# Extract AMI ID from Packer output
AMI_ID=$(grep "us-east-1: ami-" /tmp/packer-build.log | tail -1 | awk '{print $NF}')
echo ""
echo "✓ AMI built successfully: $AMI_ID"
echo ""

echo "Step 5: Create Terraform override file"
echo "========================================="
cd "$TERRAFORM_DIR"

# Create override file with app_version and SSH key
cat > override.auto.tfvars <<EOF
# Auto-generated override for custom AMI deployment
app_version = "dev-v0.1.0"
ssh_public_key = "$(cat ~/.ssh/id_rsa_aws.pub)"
EOF

echo "✓ Created override.auto.tfvars"
echo ""

echo "Step 6: Initialize Terraform"
echo "========================================="
terraform init
echo "✓ Terraform initialized"
echo ""

echo "Step 7: Validate Terraform configuration"
echo "========================================="
terraform validate
echo "✓ Terraform configuration validated"
echo ""

echo "Step 8: Generate Terraform plan"
echo "========================================="
terraform plan -out=tfplan
echo "✓ Terraform plan generated"
echo ""

echo "Step 9: Apply Terraform plan"
echo "========================================="
terraform apply tfplan 2>&1 | tee /tmp/terraform-apply.log
echo "✓ Terraform applied successfully"
echo ""

echo "Step 10: Get deployment outputs"
echo "========================================="
WEBSITE_URL=$(terraform output -raw website_url)
PUBLIC_IP=$(terraform output -raw public_ip)
SSH_COMMAND=$(terraform output -raw ssh_command)

echo "Deployment complete!"
echo ""
echo "Website URL: $WEBSITE_URL"
echo "Public IP: $PUBLIC_IP"
echo "SSH Command: $SSH_COMMAND"
echo "AMI ID: $AMI_ID"
echo ""

echo "Step 11: Verify deployment (wait 10 seconds for instance to stabilize)"
echo "========================================="
sleep 10

# Check for correct email
CORRECT_EMAIL_COUNT=$(curl -s "$WEBSITE_URL" | grep -o "{{ADMIN_EMAIL}}" | wc -l | tr -d ' ')
OLD_EMAIL_COUNT=$(curl -s "$WEBSITE_URL" | grep -o "{{OLD_EMAIL}}" | wc -l | tr -d ' ')

echo "Email verification:"
echo "  {{ADMIN_EMAIL}}: $CORRECT_EMAIL_COUNT occurrences ✓"
echo "  {{OLD_EMAIL}}: $OLD_EMAIL_COUNT occurrences (should be 0)"

if [ "$OLD_EMAIL_COUNT" -eq 0 ] && [ "$CORRECT_EMAIL_COUNT" -gt 0 ]; then
  echo ""
  echo "✅ Deployment successful! Email has been corrected."
else
  echo ""
  echo "⚠️  Warning: Email verification failed"
  exit 1
fi

echo ""
echo "Step 12: Cleanup"
echo "========================================="
rm -f override.auto.tfvars
echo "✓ Removed override file"
echo ""

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  AMI ID: $AMI_ID"
echo "  Website: $WEBSITE_URL"
echo "  Instance: $(terraform output -raw instance_id)"
echo ""
echo "Logs:"
echo "  Packer build: /tmp/packer-build.log"
echo "  Terraform apply: /tmp/terraform-apply.log"
echo ""
