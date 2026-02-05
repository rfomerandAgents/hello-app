#!/bin/bash

# AMI Management Script
# Purpose: Create and delete Packer AMIs for {{PROJECT_NAME}}
# Usage: ./scripts/manage-ami.sh <command> <ami_name> <version> [repo_root] [packer_dir] [terraform_dir] [app_dir] [environment]

# Error handling
set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "========================================="
        echo "Script failed with exit code: $exit_code"
        echo "========================================="
        echo "Check logs for details:"
        echo "  /tmp/packer-build.log"
    fi
}

trap cleanup EXIT

# Usage/help function
usage() {
    cat <<EOF
AMI Management Script - Create and Delete Packer AMIs

Usage:
  $0 <command> <ami_name> <version> [repo_root] [packer_dir] [terraform_dir] [app_dir] [environment]

Commands:
  build    Build new AMI with Packer
  delete   Delete existing AMI and snapshots

Required Parameters:
  ami_name        Full AMI name (e.g., {{PROJECT_SLUG}}-dev-v0.1.0)
  version         Version tag (e.g., v0.1.0)

Optional Parameters:
  repo_root       Repository root (default: {{REPO_PATH}})
  packer_dir      Packer directory (default: \$repo_root/io/packer)
  terraform_dir   Terraform directory (default: \$repo_root/io/terraform)
  app_dir         Application directory (default: \$repo_root/app)
  environment     Environment: dev/staging/prod (default: dev)

Examples:
  # Build AMI with defaults
  $0 build {{PROJECT_SLUG}}-dev-v0.2.0 v0.2.0

  # Build for production
  $0 build {{PROJECT_SLUG}}-prod-v1.0.0 v1.0.0 "" "" "" "" prod

  # Delete AMI
  $0 delete {{PROJECT_SLUG}}-dev-v0.1.0 v0.1.0
EOF
    exit 0
}

# Command is first argument
COMMAND="${1:-}"

if [ "$COMMAND" = "-h" ] || [ "$COMMAND" = "--help" ] || [ -z "$COMMAND" ]; then
    usage
fi

# Shift so remaining args are positional parameters
shift

# Parse parameters (after shift, AMI_NAME is now $1)
AMI_NAME="${1:?Error: AMI_NAME is required (arg 1)}"
VERSION="${2:?Error: VERSION is required (arg 2)}"

# Optional parameters with defaults
REPO_ROOT="${3:-{{REPO_PATH}}}"
PACKER_DIR="${4:-$REPO_ROOT/io/packer}"
TERRAFORM_DIR="${5:-$REPO_ROOT/io/terraform}"
APP_DIR="${6:-$REPO_ROOT/app}"
ENVIRONMENT="${7:-dev}"

# Validate directories
if [ ! -d "$REPO_ROOT" ]; then
    echo "Error: REPO_ROOT does not exist: $REPO_ROOT"
    exit 1
fi

if [ ! -d "$APP_DIR" ]; then
    echo "Error: APP_DIR does not exist: $APP_DIR"
    exit 1
fi

if [ ! -f "$PACKER_DIR/app.pkr.hcl" ]; then
    echo "Error: Packer template not found: $PACKER_DIR/app.pkr.hcl"
    exit 1
fi

# Validate environment
case "$ENVIRONMENT" in
    dev|staging|prod) ;;
    *)
        echo "Error: ENVIRONMENT must be dev, staging, or prod (got: $ENVIRONMENT)"
        exit 1
        ;;
esac

# ========================================
# AMI Build Functions
# ========================================

# clean_build_artifacts - Remove build artifacts from app directory
#
# Cleans: out, .next, node_modules/.cache, .DS_Store
clean_build_artifacts() {
    echo "========================================="
    echo "Step 1: Clean local build artifacts"
    echo "========================================="
    cd "$APP_DIR"
    rm -rf out .next node_modules/.cache .DS_Store
    echo "✓ Cleaned build artifacts"
    echo ""
}

# initialize_packer - Initialize Packer plugins
#
# Downloads required Packer plugins specified in app.pkr.hcl
initialize_packer() {
    echo "========================================="
    echo "Step 2: Initialize Packer"
    echo "========================================="
    cd "$PACKER_DIR"
    packer init app.pkr.hcl
    echo "✓ Packer initialized"
    echo ""
}

# validate_packer_template - Validate Packer template syntax
#
# Checks app.pkr.hcl for syntax errors before building
validate_packer_template() {
    echo "========================================="
    echo "Step 3: Validate Packer template"
    echo "========================================="
    cd "$PACKER_DIR"
    packer validate app.pkr.hcl
    echo "✓ Packer template validated"
    echo ""
}

# build_ami - Build AMI with Packer
#
# Creates Amazon Machine Image with application code
# Exports AMI_ID variable for use after build
build_ami() {
    echo "========================================="
    echo "Step 4: Build AMI with Packer (5-10 minutes)"
    echo "========================================="
    cd "$PACKER_DIR"

    # Enable Packer debug logging
    export PACKER_LOG=1

    # Build AMI with variables
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

    # Export for use in main script
    export AMI_ID
}

# build_ami_workflow - Orchestrate AMI build process
#
# Runs: clean → init → validate → build
build_ami_workflow() {
    echo "========================================="
    echo "AMI Build Workflow"
    echo "========================================="
    echo "AMI Name: $AMI_NAME"
    echo "Version: $VERSION"
    echo "Environment: $ENVIRONMENT"
    echo "App Directory: $APP_DIR"
    echo ""

    clean_build_artifacts
    initialize_packer
    validate_packer_template
    build_ami

    echo "========================================="
    echo "Build Complete!"
    echo "========================================="
    echo "AMI ID: $AMI_ID"
    echo "AMI Name: $AMI_NAME"
    echo "Version: $VERSION"
    echo "Environment: $ENVIRONMENT"
    echo "Build Log: /tmp/packer-build.log"
    echo ""
}

# ========================================
# AMI Deletion Functions
# ========================================

# verify_aws_cli - Verify AWS CLI is installed and configured
#
# Checks for:
# - AWS CLI binary
# - AWS_ACCESS_KEY_ID environment variable
# - AWS_SECRET_ACCESS_KEY environment variable
verify_aws_cli() {
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo "Error: AWS CLI not installed"
        echo "Install with: brew install awscli"
        exit 1
    fi

    # Check for AWS credentials
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        echo "Error: AWS_ACCESS_KEY_ID not set"
        echo "Load from .env file or set environment variable"
        exit 1
    fi

    if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "Error: AWS_SECRET_ACCESS_KEY not set"
        echo "Load from .env file or set environment variable"
        exit 1
    fi

    echo "✓ AWS CLI configured"
}

# find_ami_by_name - Find AMI ID from AMI name
#
# Args:
#   $1 - AMI name to search for
#
# Returns:
#   AMI ID if found, exits with error if not found
#
# Example:
#   ami_id=$(find_ami_by_name "{{PROJECT_SLUG}}-dev-v1.0.0")
find_ami_by_name() {
    local ami_name="$1"
    local region="${AWS_REGION:-us-east-1}"

    echo "Searching for AMI: $ami_name"

    # Query AWS for AMI by name
    local ami_id=$(aws ec2 describe-images \
        --region "$region" \
        --owners self \
        --filters "Name=name,Values=$ami_name" \
        --query 'Images[0].ImageId' \
        --output text)

    if [ "$ami_id" = "None" ] || [ -z "$ami_id" ]; then
        echo "Error: AMI not found: $ami_name"
        return 1
    fi

    echo "✓ Found AMI: $ami_id"
    echo "$ami_id"
}

# check_ami_in_use - Check if AMI is being used by any instances
#
# Args:
#   $1 - AMI ID to check
#
# Returns:
#   0 if AMI is not in use, 1 if in use
check_ami_in_use() {
    local ami_id="$1"
    local region="${AWS_REGION:-us-east-1}"

    echo "Checking if AMI is in use: $ami_id"

    # Find instances using this AMI
    local instances=$(aws ec2 describe-instances \
        --region "$region" \
        --filters "Name=image-id,Values=$ami_id" "Name=instance-state-name,Values=running,stopped,stopping,pending" \
        --query 'Reservations[*].Instances[*].InstanceId' \
        --output text)

    if [ -n "$instances" ]; then
        echo "Error: AMI is in use by instances:"
        echo "$instances"
        echo ""
        echo "Cannot delete AMI while instances are using it."
        echo "Terminate instances first, then retry."
        return 1
    fi

    echo "✓ AMI is not in use"
    return 0
}

# delete_ami_and_snapshots - Deregister AMI and delete snapshots
#
# Args:
#   $1 - AMI ID to delete
#
# Deletes:
#   - AMI registration
#   - Associated EBS snapshots
delete_ami_and_snapshots() {
    local ami_id="$1"
    local region="${AWS_REGION:-us-east-1}"

    echo "========================================="
    echo "Deleting AMI: $ami_id"
    echo "========================================="

    # Get snapshot IDs associated with AMI
    local snapshots=$(aws ec2 describe-images \
        --region "$region" \
        --image-ids "$ami_id" \
        --query 'Images[0].BlockDeviceMappings[*].Ebs.SnapshotId' \
        --output text)

    echo "Associated snapshots: $snapshots"

    # Deregister AMI
    echo "Deregistering AMI..."
    aws ec2 deregister-image \
        --region "$region" \
        --image-id "$ami_id"

    echo "✓ AMI deregistered: $ami_id"

    # Delete snapshots
    if [ -n "$snapshots" ]; then
        for snapshot in $snapshots; do
            echo "Deleting snapshot: $snapshot"
            aws ec2 delete-snapshot \
                --region "$region" \
                --snapshot-id "$snapshot"
            echo "✓ Snapshot deleted: $snapshot"
        done
    fi

    echo ""
    echo "✓ AMI and snapshots deleted successfully"
}

# delete_ami_workflow - Orchestrate AMI deletion process
#
# Workflow:
# 1. Verify AWS CLI and credentials
# 2. Find AMI by name
# 3. Check if AMI is in use
# 4. Prompt for confirmation
# 5. Delete AMI and snapshots
delete_ami_workflow() {
    echo "========================================="
    echo "AMI Deletion Workflow"
    echo "========================================="
    echo "AMI Name: $AMI_NAME"
    echo ""

    verify_aws_cli

    # Find AMI
    AMI_ID=$(find_ami_by_name "$AMI_NAME")
    if [ $? -ne 0 ]; then
        exit 1
    fi

    echo ""

    # Check if in use
    check_ami_in_use "$AMI_ID"
    if [ $? -ne 0 ]; then
        exit 1
    fi

    echo ""
    echo "⚠️  WARNING: This will permanently delete the AMI and snapshots!"
    echo ""
    read -p "Type 'yes' to confirm deletion: " confirmation

    if [ "$confirmation" != "yes" ]; then
        echo "Deletion cancelled"
        exit 0
    fi

    echo ""
    delete_ami_and_snapshots "$AMI_ID"

    echo ""
    echo "========================================="
    echo "Deletion Complete!"
    echo "========================================="
}

# ========================================
# Main Script Logic
# ========================================

# Load environment variables from .env if it exists
if [ -f "$REPO_ROOT/.env" ]; then
    export $(grep -v '^#' "$REPO_ROOT/.env" | xargs) 2>/dev/null || true
    echo "✓ Loaded environment from .env"
    echo ""
fi

# Dispatch command
case "$COMMAND" in
    build)
        build_ami_workflow
        ;;
    delete)
        delete_ami_workflow
        ;;
    *)
        echo "Error: Unknown command: $COMMAND"
        echo ""
        echo "Valid commands: build, delete"
        echo "Run '$0 --help' for usage information"
        exit 1
        ;;
esac
