# Example: Optimized Packer Configuration
# This file demonstrates best practices for Packer builds

#==============================================================================
# Packer Configuration
#==============================================================================

packer {
  required_version = ">= 1.9.0"

  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

#==============================================================================
# Variables
#==============================================================================

variable "aws_region" {
  description = "AWS region for AMI build"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "app_version" {
  description = "Application version (e.g., v1.2.3)"
  type        = string

  validation {
    condition     = can(regex("^v[0-9]+\\.[0-9]+\\.[0-9]+$", var.app_version))
    error_message = "Version must follow semantic versioning (vX.Y.Z)."
  }
}

variable "git_commit" {
  description = "Git commit SHA"
  type        = string
  default     = env("GIT_COMMIT")
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "myapp"
}

variable "build_instance_type" {
  description = "EC2 instance type for Packer build"
  type        = string
  default     = "c6i.large" # Compute-optimized for faster builds
}

variable "runtime_instance_type" {
  description = "Expected runtime instance type (for testing)"
  type        = string
  default     = "t3.medium"
}

variable "kms_key_id" {
  description = "KMS key ID for AMI encryption"
  type        = string
  default     = ""
}

variable "allowed_build_cidrs" {
  description = "CIDR blocks allowed to access build instance"
  type        = list(string)
  default     = ["10.0.0.0/8"] # Corporate network
}

variable "vpc_id" {
  description = "VPC ID for build (leave empty for default VPC)"
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Subnet ID for build (leave empty for default subnet)"
  type        = string
  default     = ""
}

#==============================================================================
# Locals
#==============================================================================

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
  ami_name  = "${var.project_name}-${var.environment}-${var.app_version}-${local.timestamp}"

  # Git commit short SHA
  git_commit_short = var.git_commit != "" ? substr(var.git_commit, 0, 7) : "unknown"

  # Common tags
  common_tags = {
    Name        = local.ami_name
    Project     = var.project_name
    Environment = var.environment
    Version     = var.app_version
    GitCommit   = local.git_commit_short
    BuildDate   = local.timestamp
    ManagedBy   = "packer"
    BaseOS      = "ubuntu-22.04"
  }
}

#==============================================================================
# Source Configuration
#==============================================================================

source "amazon-ebs" "ubuntu" {
  ami_name      = local.ami_name
  instance_type = var.build_instance_type
  region        = var.aws_region

  # Dynamic AMI selection (not hardcoded)
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"] # Canonical
  }

  # SSH configuration
  ssh_username = "ubuntu"
  ssh_timeout  = "15m"
  ssh_interface = var.vpc_id != "" ? "private_ip" : "public_ip"

  # Network configuration
  vpc_id    = var.vpc_id != "" ? var.vpc_id : null
  subnet_id = var.subnet_id != "" ? var.subnet_id : null

  associate_public_ip_address = var.vpc_id == "" ? true : false

  # Security - restrict access to build instance
  temporary_security_group_source_cidrs = var.allowed_build_cidrs

  # Build optimizations
  ebs_optimized = true
  ena_support   = true
  sriov_support = true

  # EBS volume configuration
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_type           = "gp3"
    volume_size           = 20
    iops                  = 3000
    throughput            = 125
    delete_on_termination = true
    encrypted             = true
    kms_key_id            = var.kms_key_id != "" ? var.kms_key_id : null
  }

  # Enforce IMDSv2 in resulting AMI
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # Encryption for AMI
  encrypt_boot = true
  kms_key_id   = var.kms_key_id != "" ? var.kms_key_id : null

  # AMI distribution (if multi-region)
  # ami_regions = ["us-east-1", "us-west-2"]

  # Regional KMS keys (if distributing to multiple regions)
  # region_kms_key_ids = {
  #   "us-west-2" = "arn:aws:kms:us-west-2:..."
  # }

  # AMI lifecycle
  force_deregister      = var.environment == "dev" # Allow overwrite in dev
  force_delete_snapshot = var.environment == "dev"

  # Timeouts
  aws_polling {
    delay_seconds = 15
    max_attempts  = 120 # 30 minutes
  }

  snapshot_timeout = "30m"

  # Tags for AMI and snapshots
  tags          = local.common_tags
  snapshot_tags = merge(local.common_tags, { Type = "ami-snapshot" })

  # Run tags for build instance
  run_tags = {
    Name      = "packer-build-${local.ami_name}"
    Temporary = "true"
  }
}

#==============================================================================
# Build
#==============================================================================

build {
  name    = "ubuntu-app"
  sources = ["source.amazon-ebs.ubuntu"]

  # Wait for cloud-init to complete
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "cloud-init status --wait",
      "echo 'Cloud-init complete'"
    ]
  }

  # System updates and base packages
  provisioner "shell" {
    inline = [
      "set -euo pipefail",
      "export DEBIAN_FRONTEND=noninteractive",
      "",
      "echo 'Updating package lists...'",
      "sudo apt-get update",
      "",
      "echo 'Upgrading packages...'",
      "sudo apt-get upgrade -y",
      "",
      "echo 'Installing base packages...'",
      "sudo apt-get install -y --no-install-recommends \\",
      "  curl \\",
      "  wget \\",
      "  ca-certificates \\",
      "  gnupg \\",
      "  lsb-release \\",
      "  unattended-upgrades \\",
      "  fail2ban \\",
      "  ufw",
      "",
      "echo 'Base packages installed'"
    ]
    timeout = "10m"
  }

  # Application installation
  provisioner "shell" {
    script = "${path.root}/scripts/install_app.sh"
    environment_vars = [
      "APP_VERSION=${var.app_version}",
      "ENVIRONMENT=${var.environment}"
    ]
    timeout = "15m"
  }

  # Upload application files
  provisioner "file" {
    source      = "${path.root}/../../app/"
    destination = "/tmp/app"
  }

  # Configure application
  provisioner "shell" {
    inline = [
      "sudo mkdir -p /opt/app",
      "sudo mv /tmp/app/* /opt/app/",
      "sudo chown -R ubuntu:ubuntu /opt/app",
      "sudo chmod -R 755 /opt/app"
    ]
  }

  # Security hardening
  provisioner "shell" {
    script  = "${path.root}/scripts/security_hardening.sh"
    timeout = "10m"
  }

  # Cleanup before AMI creation
  provisioner "shell" {
    script  = "${path.root}/scripts/cleanup.sh"
    timeout = "5m"
  }

  # Manifest post-processor - track AMI metadata
  post-processor "manifest" {
    output     = "packer-manifest.json"
    strip_path = true

    custom_data = {
      project        = var.project_name
      version        = var.app_version
      environment    = var.environment
      git_commit     = var.git_commit
      git_commit_short = local.git_commit_short
      build_date     = local.timestamp
      base_ami       = "{{ .SourceAMI }}"
      base_ami_name  = "{{ .SourceAMIName }}"
      region         = var.aws_region
      build_instance = var.build_instance_type
    }
  }

  # Checksum post-processor
  post-processor "checksum" {
    checksum_types = ["sha256"]
    output         = "packer-checksums.txt"
  }
}

#==============================================================================
# Notes
#==============================================================================

# Usage Examples:
#
# Development build:
#   packer build \
#     -var environment=dev \
#     -var app_version=v1.0.0 \
#     .
#
# Production build with all metadata:
#   packer build \
#     -var environment=prod \
#     -var app_version=v1.2.3 \
#     -var git_commit=$(git rev-parse HEAD) \
#     -var kms_key_id=arn:aws:kms:... \
#     .
#
# Private VPC build:
#   packer build \
#     -var vpc_id=vpc-12345 \
#     -var subnet_id=subnet-67890 \
#     -var allowed_build_cidrs='["10.0.0.0/8"]' \
#     .

# Validation:
#   packer init .
#   packer validate .
#   packer fmt -check .

# Testing built AMI:
#   AMI_ID=$(jq -r '.builds[0].artifact_id' packer-manifest.json | cut -d: -f2)
#   aws ec2 run-instances --image-id $AMI_ID --instance-type t3.micro
