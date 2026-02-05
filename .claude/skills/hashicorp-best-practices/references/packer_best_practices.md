# Packer Best Practices - Comprehensive Guide

This guide provides in-depth best practices for building secure, optimized, and maintainable machine images with Packer.

## Table of Contents

1. [Source Configuration](#source-configuration)
2. [Build Configuration](#build-configuration)
3. [Provisioner Patterns](#provisioner-patterns)
4. [Post-Processors](#post-processors)
5. [Security Best Practices](#security-best-practices)
6. [Build Optimization](#build-optimization)
7. [CI/CD Integration](#cicd-integration)
8. [Testing and Validation](#testing-and-validation)

---

## Source Configuration

### AMI Selection

**NEVER hardcode AMI IDs:**

```hcl
# BAD - Will break when AMI is deprecated
source "amazon-ebs" "app" {
  source_ami = "ami-0123456789abcdef0"
}

# GOOD - Dynamic lookup
source "amazon-ebs" "app" {
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]  # Canonical
  }
}
```

### Common Base Image Filters

**Ubuntu:**

```hcl
source_ami_filter {
  filters = {
    name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["099720109477"]  # Canonical
}
```

**Amazon Linux 2023:**

```hcl
source_ami_filter {
  filters = {
    name                = "al2023-ami-*-x86_64"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["amazon"]
}
```

**RHEL:**

```hcl
source_ami_filter {
  filters = {
    name                = "RHEL-9*_HVM-*-x86_64-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["309956199498"]  # Red Hat
}
```

### Instance Configuration

**Use appropriate instance types:**

```hcl
source "amazon-ebs" "app" {
  # Build instance (not runtime instance)
  instance_type = "c6i.large"  # Compute-optimized for faster builds

  # Runtime instance would be different (e.g., t3.medium)
  # Builds run faster with more CPU
}
```

**Enable EBS optimization:**

```hcl
source "amazon-ebs" "app" {
  ebs_optimized = true
  ena_support   = true
  sriov_support = true

  # These improve runtime performance of resulting AMI
}
```

### Networking

**Public IP for builds:**

```hcl
source "amazon-ebs" "app" {
  associate_public_ip_address = true
  ssh_interface               = "public_ip"

  # Alternative for private builds in VPC:
  # subnet_id    = "subnet-12345"
  # ssh_interface = "private_ip"
}
```

**VPC configuration for private builds:**

```hcl
source "amazon-ebs" "app" {
  vpc_id    = var.vpc_id
  subnet_id = var.subnet_id

  # Use existing security group
  security_group_ids = [var.build_security_group_id]

  # Or let Packer create temporary SG
  temporary_security_group_source_cidrs = var.allowed_cidrs

  ssh_interface = "private_ip"
}
```

### SSH Configuration

**Optimize SSH connection:**

```hcl
source "amazon-ebs" "app" {
  ssh_username = "ubuntu"  # Depends on base AMI
  ssh_timeout  = "15m"     # Allow time for instance to boot

  # For slow-starting instances
  ssh_handshake_attempts = 20

  # Use SSH agent
  ssh_agent_auth = true
}
```

---

## Build Configuration

### Parallel Builds

**Build multiple variants simultaneously:**

```hcl
variable "ubuntu_versions" {
  type = map(string)
  default = {
    "20.04" = "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"
    "22.04" = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
  }
}

source "amazon-ebs" "ubuntu" {
  for_each = var.ubuntu_versions

  ami_name = "myapp-${each.key}-{{timestamp}}"

  source_ami_filter {
    filters = {
      name = each.value
    }
    most_recent = true
    owners      = ["099720109477"]
  }
}

build {
  sources = [
    "source.amazon-ebs.ubuntu"
  ]

  # Single provisioner runs for all builds in parallel
  provisioner "shell" {
    inline = ["echo Building for multiple Ubuntu versions"]
  }
}
```

### AMI Naming

**Use descriptive, versioned names:**

```hcl
variable "app_version" {
  type        = string
  description = "Application version"
}

variable "git_commit" {
  type        = string
  description = "Git commit SHA"
  default     = ""
}

source "amazon-ebs" "app" {
  # Include version, timestamp, and commit
  ami_name = "myapp-${var.app_version}-{{timestamp}}-${substr(var.git_commit, 0, 7)}"

  # Add searchable tags
  tags = {
    Name        = "myapp"
    Version     = var.app_version
    GitCommit   = var.git_commit
    BuildDate   = "{{timestamp}}"
    Environment = var.environment
  }

  # Prevent name conflicts
  force_deregister      = false  # Don't auto-delete existing AMI
  force_delete_snapshot = false
}
```

### AMI Distribution

**Share across regions:**

```hcl
source "amazon-ebs" "app" {
  region = "us-east-1"

  # Copy to additional regions
  ami_regions = [
    "us-east-1",
    "us-west-2",
    "eu-west-1"
  ]

  # Encrypt in all regions
  encrypt_boot = true
  kms_key_id  = var.kms_key_id

  # Regional KMS keys
  region_kms_key_ids = {
    "us-west-2" = var.kms_key_id_west
    "eu-west-1" = var.kms_key_id_eu
  }
}
```

---

## Provisioner Patterns

### Shell Provisioner Best Practices

**Consolidate commands:**

```hcl
# BAD - Multiple SSH sessions, slow
provisioner "shell" {
  inline = ["apt-get update"]
}
provisioner "shell" {
  inline = ["apt-get install -y nginx"]
}
provisioner "shell" {
  inline = ["systemctl enable nginx"]
}

# GOOD - Single session, atomic
provisioner "shell" {
  inline = [
    "export DEBIAN_FRONTEND=noninteractive",
    "sudo apt-get update",
    "sudo apt-get install -y nginx",
    "sudo systemctl enable nginx"
  ]
}

# EVEN BETTER - Use script file
provisioner "shell" {
  script = "scripts/install_nginx.sh"
}
```

### Error Handling

**Use proper error handling in scripts:**

```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Log output
exec > >(tee /var/log/packer-build.log)
exec 2>&1

echo "Starting provisioning..."

# Retry logic for apt
retry_count=0
max_retries=3
until sudo apt-get update || [ $retry_count -eq $max_retries ]; do
  retry_count=$((retry_count+1))
  echo "apt-get update failed, retrying ($retry_count/$max_retries)..."
  sleep 5
done

# Install packages
sudo apt-get install -y \
  nginx \
  certbot \
  python3-certbot-nginx

# Verify installation
nginx -v || exit 1

echo "Provisioning complete"
```

### Ansible Provisioner

**For complex provisioning, use Ansible:**

```hcl
provisioner "ansible" {
  playbook_file = "./ansible/playbook.yml"
  user          = "ubuntu"

  extra_arguments = [
    "--extra-vars",
    "environment=${var.environment} version=${var.app_version}"
  ]

  # Ansible configuration
  ansible_env_vars = [
    "ANSIBLE_HOST_KEY_CHECKING=False",
    "ANSIBLE_SSH_ARGS='-o ForwardAgent=yes -o ControlMaster=auto -o ControlPersist=60s'"
  ]
}
```

### File Provisioner

**Upload files efficiently:**

```hcl
# Upload directory
provisioner "file" {
  source      = "app/"
  destination = "/tmp/app"
}

# Upload with specific permissions
provisioner "shell" {
  inline = [
    "sudo mv /tmp/app /opt/app",
    "sudo chown -R app:app /opt/app",
    "sudo chmod -R 755 /opt/app"
  ]
}
```

### Provisioner Order

**Order matters - clean up after provisioning:**

```hcl
build {
  sources = ["source.amazon-ebs.app"]

  # 1. System updates
  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get upgrade -y"
    ]
  }

  # 2. Install dependencies
  provisioner "shell" {
    script = "scripts/install_dependencies.sh"
  }

  # 3. Configure application
  provisioner "ansible" {
    playbook_file = "ansible/configure.yml"
  }

  # 4. Clean up
  provisioner "shell" {
    script = "scripts/cleanup.sh"
  }
}
```

### Cleanup Script

**Always clean up before AMI creation:**

```bash
#!/bin/bash
# scripts/cleanup.sh

set -euo pipefail

echo "Cleaning up for AMI creation..."

# Stop services
sudo systemctl stop rsyslog || true

# Clear logs
sudo truncate -s 0 /var/log/*log
sudo truncate -s 0 /var/log/**/*log 2>/dev/null || true
sudo rm -f /var/log/*.gz
sudo rm -f /var/log/*.1

# Clear package cache
sudo apt-get clean
sudo rm -rf /var/cache/apt/*

# Clear bash history
history -c
cat /dev/null > ~/.bash_history

# Remove SSH host keys (will be regenerated on first boot)
sudo rm -f /etc/ssh/ssh_host_*

# Clear cloud-init
sudo cloud-init clean --logs --seed

# Remove temp files
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Clear machine-id (will be regenerated)
sudo truncate -s 0 /etc/machine-id

echo "Cleanup complete"
```

---

## Post-Processors

### Manifest Post-Processor

**Always track AMI metadata:**

```hcl
post-processor "manifest" {
  output     = "packer-manifest.json"
  strip_path = true

  custom_data = {
    app_version = var.app_version
    environment = var.environment
    git_commit  = var.git_commit
    build_date  = timestamp()
    base_ami    = "{{ .SourceAMI }}"
  }
}
```

**Example manifest output:**

```json
{
  "builds": [
    {
      "name": "amazon-ebs",
      "builder_type": "amazon-ebs",
      "build_time": 1701360000,
      "files": null,
      "artifact_id": "us-east-1:ami-0123456789abcdef0",
      "packer_run_uuid": "uuid-here",
      "custom_data": {
        "app_version": "v1.2.3",
        "environment": "prod",
        "git_commit": "abc1234",
        "build_date": "2023-11-30T12:00:00Z"
      }
    }
  ]
}
```

### Checksum Post-Processor

**Generate checksums for verification:**

```hcl
post-processor "checksum" {
  checksum_types = ["sha256"]
  output         = "packer-checksums.txt"
}
```

---

## Security Best Practices

### IMDSv2 Enforcement

**Always require IMDSv2:**

```hcl
source "amazon-ebs" "app" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforces IMDSv2
    http_put_response_hop_limit = 1
  }
}
```

### Encryption

**Encrypt AMIs:**

```hcl
source "amazon-ebs" "app" {
  encrypt_boot = true
  kms_key_id   = var.kms_key_id

  # Encrypt snapshots too
  snapshot_tags = {
    Encrypted = "true"
  }
}
```

### Temporary Security Groups

**Restrict build access:**

```hcl
# BAD - Wide open
source "amazon-ebs" "app" {
  temporary_security_group_source_cidrs = ["0.0.0.0/0"]
}

# GOOD - Restricted to known CIDRs
source "amazon-ebs" "app" {
  temporary_security_group_source_cidrs = [
    "10.0.0.0/8",      # Corporate network
    "203.0.113.0/24"   # VPN
  ]
}

# EVEN BETTER - Use existing security group
source "amazon-ebs" "app" {
  security_group_ids = [var.build_security_group_id]
}
```

### IAM Permissions

**Use least-privilege IAM:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AttachVolume",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:CopyImage",
        "ec2:CreateImage",
        "ec2:CreateKeypair",
        "ec2:CreateSecurityGroup",
        "ec2:CreateSnapshot",
        "ec2:CreateTags",
        "ec2:CreateVolume",
        "ec2:DeleteKeyPair",
        "ec2:DeleteSecurityGroup",
        "ec2:DeleteSnapshot",
        "ec2:DeleteVolume",
        "ec2:DeregisterImage",
        "ec2:DescribeImageAttribute",
        "ec2:DescribeImages",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeRegions",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSnapshots",
        "ec2:DescribeSubnets",
        "ec2:DescribeTags",
        "ec2:DescribeVolumes",
        "ec2:DetachVolume",
        "ec2:GetPasswordData",
        "ec2:ModifyImageAttribute",
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifySnapshotAttribute",
        "ec2:RegisterImage",
        "ec2:RunInstances",
        "ec2:StopInstances",
        "ec2:TerminateInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Build Optimization

### Instance Type Selection

**Use compute-optimized instances for builds:**

```hcl
variable "build_instance_type" {
  type    = string
  default = "c6i.large"  # 2 vCPU, 4GB RAM, optimized for compute

  # Faster than t3.medium for compilation/builds
  # More expensive but builds complete faster
}

source "amazon-ebs" "app" {
  instance_type = var.build_instance_type
}
```

### EBS Volume Optimization

**Use faster EBS volumes for builds:**

```hcl
source "amazon-ebs" "app" {
  launch_block_device_mappings {
    device_name = "/dev/sda1"
    volume_type = "gp3"
    volume_size = 20
    iops        = 3000      # Higher IOPS for faster builds
    throughput  = 125
    delete_on_termination = true
  }
}
```

### Provisioner Caching

**Cache package downloads:**

```bash
#!/bin/bash
# Cache apt packages on separate volume

# Create cache directory
sudo mkdir -p /var/cache/apt/archives

# Install packages (downloads cached)
sudo apt-get update
sudo apt-get install -y nginx

# Packages remain in /var/cache/apt/archives for reuse
```

### Build Timeouts

**Set appropriate timeouts:**

```hcl
source "amazon-ebs" "app" {
  # Increase timeouts for large builds
  aws_polling {
    delay_seconds = 15
    max_attempts  = 120  # 30 minutes total
  }

  # Snapshot timeout
  snapshot_timeout = "30m"
}
```

---

## CI/CD Integration

### GitHub Actions Integration

**Complete Packer build workflow:**

```yaml
name: Build AMI

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  PACKER_VERSION: '1.9.0'

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Setup Packer
        uses: hashicorp/setup-packer@main
        with:
          version: ${{ env.PACKER_VERSION }}

      - name: Initialize Packer
        run: packer init .

      - name: Validate Packer template
        run: packer validate .

      - name: Build AMI
        run: |
          packer build \
            -var "app_version=${{ github.ref_name }}" \
            -var "git_commit=${{ github.sha }}" \
            -var "environment=prod" \
            .

      - name: Upload manifest
        uses: actions/upload-artifact@v3
        with:
          name: packer-manifest
          path: packer-manifest.json
```

### Variable Injection

**Pass build metadata:**

```hcl
variable "git_commit" {
  type    = string
  default = env("GIT_COMMIT")
}

variable "build_number" {
  type    = string
  default = env("BUILD_NUMBER")
}

variable "environment" {
  type    = string
  default = env("ENVIRONMENT")

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

---

## Testing and Validation

### Validation Commands

**Validate before building:**

```bash
# Initialize Packer plugins
packer init .

# Validate template syntax
packer validate .

# Validate with variables
packer validate -var-file=vars/prod.pkrvars.hcl .

# Format check
packer fmt -check .
```

### HCL2 Variables File

**prod.pkrvars.hcl:**

```hcl
environment     = "prod"
instance_type   = "t3.large"
app_version     = "v1.2.3"
encrypt_boot    = true
```

### Testing Built AMIs

**Verify AMI after build:**

```bash
#!/bin/bash
# test-ami.sh

AMI_ID=$(jq -r '.builds[0].artifact_id' packer-manifest.json | cut -d: -f2)

echo "Testing AMI: $AMI_ID"

# Launch test instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Launched instance: $INSTANCE_ID"

# Wait for instance
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# Get IP
IP=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# Test HTTP endpoint
curl -f "http://$IP" || exit 1

echo "AMI test passed"

# Cleanup
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID"
```

---

## Complete Example

**Optimized production Packer template:**

```hcl
packer {
  required_version = ">= 1.9.0"

  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "app_version" {
  type        = string
  description = "Application version"
}

variable "environment" {
  type        = string
  description = "Environment (dev/staging/prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "git_commit" {
  type    = string
  default = env("GIT_COMMIT")
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
  ami_name  = "myapp-${var.environment}-${var.app_version}-${local.timestamp}"
}

source "amazon-ebs" "app" {
  ami_name      = local.ami_name
  instance_type = var.environment == "prod" ? "c6i.large" : "t3.medium"
  region        = "us-east-1"

  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]
  }

  ssh_username = "ubuntu"
  ssh_timeout  = "15m"

  associate_public_ip_address = true

  encrypt_boot = true
  ebs_optimized = true
  ena_support   = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name        = local.ami_name
    Version     = var.app_version
    Environment = var.environment
    GitCommit   = var.git_commit
    BuildDate   = local.timestamp
    ManagedBy   = "packer"
  }

  run_tags = {
    Name = "packer-build-${local.ami_name}"
  }
}

build {
  sources = ["source.amazon-ebs.app"]

  provisioner "shell" {
    inline = [
      "cloud-init status --wait"  # Wait for cloud-init
    ]
  }

  provisioner "shell" {
    script = "scripts/install.sh"
  }

  provisioner "file" {
    source      = "app/"
    destination = "/tmp/app"
  }

  provisioner "shell" {
    inline = [
      "sudo mv /tmp/app /opt/app",
      "sudo chown -R app:app /opt/app"
    ]
  }

  provisioner "shell" {
    script = "scripts/cleanup.sh"
  }

  post-processor "manifest" {
    output = "packer-manifest.json"
    custom_data = {
      version     = var.app_version
      environment = var.environment
      git_commit  = var.git_commit
    }
  }
}
```

---

## Summary

Following these best practices ensures:

- **Reliable** builds that work consistently
- **Secure** AMIs with proper encryption and hardening
- **Fast** build times through optimization
- **Maintainable** templates that are easy to understand
- **Traceable** builds with proper metadata and manifests

Remember: AMIs are immutable artifacts. Build them right the first time.
