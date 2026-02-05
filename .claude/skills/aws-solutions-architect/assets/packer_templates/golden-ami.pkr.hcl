packer {
  required_version = ">= 1.10.0"
  
  required_plugins {
    amazon = {
      version = ">= 1.3.0"
      source  = "github.com/hashicorp/amazon"
    }
    ansible = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

# Variables
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for AMI build"
}

variable "instance_type" {
  type        = string
  default     = "t3.medium"
  description = "Instance type for building"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment (dev, staging, production)"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "ami_prefix" {
  type        = string
  default     = "golden-ami"
  description = "Prefix for AMI name"
}

variable "vpc_id" {
  type        = string
  default     = ""
  description = "VPC ID for build instance (optional)"
}

variable "subnet_id" {
  type        = string
  default     = ""
  description = "Subnet ID for build instance (optional)"
}

variable "git_commit_sha" {
  type        = string
  default     = "unknown"
  description = "Git commit SHA for tracking"
}

variable "git_ref" {
  type        = string
  default     = "unknown"
  description = "Git ref for tracking"
}

variable "app_version" {
  type        = string
  default     = "1.0.0"
  description = "Application version to install"
}

# Locals
locals {
  timestamp = formatdate("YYYY-MM-DD-hhmm", timestamp())
  ami_name  = "${var.ami_prefix}-${var.environment}-${local.timestamp}"
  
  common_tags = {
    Name        = local.ami_name
    Environment = var.environment
    BuildDate   = timestamp()
    BuildSource = "packer"
    ManagedBy   = "terraform"
    GitCommit   = var.git_commit_sha
    GitRef      = var.git_ref
  }
}

# Data sources
data "amazon-ami" "ubuntu" {
  filters = {
    name                = "ubuntu/images/*ubuntu-jammy-22.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["099720109477"] # Canonical
  region      = var.aws_region
}

# HCP Packer configuration
hcp_packer_registry {
  bucket_name = "golden-ami"
  description = "Ubuntu 22.04 golden AMI for application servers"
  
  bucket_labels = {
    "os"          = "ubuntu-22.04"
    "team"        = "platform"
    "compliance"  = "cis-level-1"
  }
  
  build_labels = {
    "build-source" = "github-actions"
    "git-commit"   = var.git_commit_sha
    "environment"  = var.environment
  }
}

# Source configuration
source "amazon-ebs" "ubuntu" {
  # Naming
  ami_name        = local.ami_name
  ami_description = "Golden AMI for ${var.environment} - Built from ${var.git_commit_sha}"
  
  # Instance configuration
  instance_type = var.instance_type
  region        = var.aws_region
  source_ami    = data.amazon-ami.ubuntu.id
  
  # Network configuration
  vpc_id                      = var.vpc_id
  subnet_id                   = var.subnet_id
  associate_public_ip_address = true
  
  # SSH configuration
  ssh_username = "ubuntu"
  ssh_timeout  = "10m"
  
  # IAM configuration
  iam_instance_profile = "PackerBuilder"
  
  # AMI distribution
  ami_regions = [
    var.aws_region,
    # Add additional regions as needed
    # "us-west-2",
    # "eu-west-1",
  ]
  
  # Encryption
  encrypt_boot = true
  # kms_key_id = "arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID"
  
  # AMI permissions
  ami_users = []
  # ami_groups = ["all"] # Make AMI public (not recommended for production)
  
  # Tags
  tags          = local.common_tags
  snapshot_tags = merge(local.common_tags, { Type = "snapshot" })
  
  # Cleanup
  force_deregister      = false
  force_delete_snapshot = false
  
  # Performance
  aws_polling {
    delay_seconds = 15
    max_attempts  = 120
  }
  
  # Launch template
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 30
    volume_type           = "gp3"
    iops                  = 3000
    throughput            = 125
    delete_on_termination = true
    encrypted             = true
  }
  
  # User data for cloud-init
  user_data_file = "scripts/user-data.sh"
  
  # Run tags for cost allocation
  run_tags = {
    Name      = "packer-build-${var.environment}"
    Purpose   = "AMI Build"
    ManagedBy = "packer"
  }
}

# Build configuration
build {
  name    = "golden-ami"
  sources = ["source.amazon-ebs.ubuntu"]
  
  # Wait for cloud-init to complete
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "cloud-init status --wait",
      "echo 'Cloud-init complete'"
    ]
  }
  
  # System updates
  provisioner "shell" {
    inline = [
      "echo 'Updating system packages...'",
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'",
      "sudo apt-get install -y curl wget unzip jq git build-essential"
    ]
    pause_before = "10s"
  }
  
  # Install AWS tools
  provisioner "shell" {
    script = "scripts/install-aws-tools.sh"
  }
  
  # Copy configuration files
  provisioner "file" {
    source      = "configs/"
    destination = "/tmp/configs"
  }
  
  # Install application dependencies
  provisioner "shell" {
    script = "scripts/install-dependencies.sh"
    environment_vars = [
      "APP_VERSION=${var.app_version}",
      "ENVIRONMENT=${var.environment}"
    ]
  }
  
  # Configure with Ansible
  provisioner "ansible" {
    playbook_file = "ansible/playbook.yml"
    user          = "ubuntu"
    
    extra_arguments = [
      "--extra-vars",
      "environment=${var.environment} app_version=${var.app_version}",
      "--tags",
      "install,configure"
    ]
    
    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_STDOUT_CALLBACK=yaml"
    ]
  }
  
  # Security hardening
  provisioner "shell" {
    scripts = [
      "scripts/security-hardening.sh",
      "scripts/cis-benchmark.sh"
    ]
    execute_command = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
  }
  
  # Install monitoring agents
  provisioner "shell" {
    script          = "scripts/install-monitoring.sh"
    execute_command = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
  }
  
  # System cleanup
  provisioner "shell" {
    inline = [
      "echo 'Cleaning up...'",
      "sudo apt-get autoremove -y",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*",
      "sudo rm -f /root/.bash_history",
      "sudo rm -f /home/ubuntu/.bash_history",
      "history -c",
      "echo 'Cleanup complete'"
    ]
  }
  
  # Validate installation
  provisioner "shell" {
    script = "scripts/validate.sh"
  }
  
  # Post-processors
  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
    
    custom_data = {
      ami_name    = local.ami_name
      environment = var.environment
      timestamp   = local.timestamp
    }
  }
  
  post-processor "shell-local" {
    inline = [
      "echo '==================================='",
      "echo 'AMI Build Complete!'",
      "echo 'AMI ID: '$(jq -r '.builds[-1].artifact_id' manifest.json | cut -d':' -f2)",
      "echo 'AMI Name: ${local.ami_name}'",
      "echo 'Environment: ${var.environment}'",
      "echo '==================================='",
    ]
  }
}
