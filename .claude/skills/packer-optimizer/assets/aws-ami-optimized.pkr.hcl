// Optimized AWS AMI Builder Template
// This template demonstrates best practices for building optimized AWS AMIs with Packer

packer {
  required_plugins {
    amazon = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for building"
  default     = "t3.medium"  // Balanced for most builds
}

variable "app_version" {
  type        = string
  description = "Application version"
  default     = "1.0.0"
}

variable "environment" {
  type        = string
  description = "Environment tag"
  default     = "production"
}

// Data source to get latest Ubuntu AMI
data "amazon-ami" "ubuntu" {
  filters = {
    name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-*-server-*"
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = ["099720109477"]  // Canonical
  most_recent = true
  region      = var.region
}

// Optional: Use HCP Packer for base image
// data "hcp-packer-image" "base" {
//   bucket_name    = "golden-base"
//   channel        = "production"
//   cloud_provider = "aws"
//   region         = var.region
// }

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
  ami_name  = "optimized-app-${var.app_version}-${local.timestamp}"
}

source "amazon-ebs" "optimized" {
  // Build configuration
  region        = var.region
  source_ami    = data.amazon-ami.ubuntu.id  // Or: data.hcp-packer-image.base.id
  instance_type = var.instance_type
  ssh_username  = "ubuntu"
  ami_name      = local.ami_name
  
  // Performance optimizations
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 20  // Adjust based on needs
    volume_type           = "gp3"
    iops                  = 3000  // gp3 baseline, increase for I/O heavy workloads
    throughput            = 125   // gp3 baseline, increase for throughput needs
    delete_on_termination = true
    encrypted             = true  // Best practice + provides compression
  }
  
  // Optional: Add ephemeral storage for build cache
  // launch_block_device_mappings {
  //   device_name  = "/dev/sdb"
  //   virtual_name = "ephemeral0"
  // }
  
  // Enhanced networking
  ena_support       = true
  sriov_support     = true
  
  // AMI configuration
  ami_description = "Optimized ${var.environment} AMI - v${var.app_version}"
  ami_regions     = [var.region]  // Add additional regions as needed
  
  // Resource tagging
  tags = {
    Name        = local.ami_name
    Version     = var.app_version
    Environment = var.environment
    BuildDate   = local.timestamp
    BuildTool   = "Packer"
    ManagedBy   = "Packer"
  }
  
  // Snapshot tagging
  snapshot_tags = {
    Name        = "${local.ami_name}-snapshot"
    Version     = var.app_version
    Environment = var.environment
  }
  
  // AMI sharing (optional)
  // ami_users = ["123456789012"]  // Share with other accounts
  
  // Run tags for build instance
  run_tags = {
    Name      = "packer-builder-${local.ami_name}"
    Temporary = "true"
  }
}

build {
  name = "optimized-ami"
  
  // Optional: HCP Packer integration
  // hcp_packer_registry {
  //   bucket_name = "golden-images"
  //   description = "Optimized production AMI v${var.app_version}"
  //   bucket_labels = {
  //     "version"     = var.app_version
  //     "environment" = var.environment
  //     "os"          = "ubuntu-22.04"
  //   }
  // }
  
  sources = ["source.amazon-ebs.optimized"]
  
  ////////////////////////////////////////////////////////////////////////////////
  // PROVISIONING - Ordered by change frequency (stable → volatile)
  ////////////////////////////////////////////////////////////////////////////////
  
  // 1. System updates and base packages (rarely change)
  provisioner "shell" {
    inline = [
      "set -e",
      "echo 'Waiting for cloud-init to complete...'",
      "cloud-init status --wait",
      "echo 'Updating system packages...'",
      // Use apt-fast or configure local mirror for faster downloads
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'",
    ]
  }
  
  // 2. Install system dependencies (change occasionally)
  provisioner "shell" {
    inline = [
      "set -e",
      "echo 'Installing system dependencies...'",
      // Use --no-install-recommends to minimize size
      "sudo apt-get install -y --no-install-recommends \\",
      "  ca-certificates \\",
      "  curl \\",
      "  wget \\",
      "  unzip \\",
      "  python3 \\",
      "  python3-pip",
      // Clean up immediately to reduce image size
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
    ]
  }
  
  // 3. Install and configure application runtime (change occasionally)
  provisioner "shell" {
    script = "scripts/install-runtime.sh"
  }
  
  // 4. Deploy application (changes frequently)
  provisioner "file" {
    source      = "app/"
    destination = "/tmp/app/"
  }
  
  provisioner "shell" {
    inline = [
      "set -e",
      "sudo mkdir -p /opt/app",
      "sudo mv /tmp/app/* /opt/app/",
      "sudo chown -R ubuntu:ubuntu /opt/app",
    ]
  }
  
  // 5. Application configuration (changes frequently)
  provisioner "shell" {
    script = "scripts/configure-app.sh"
  }
  
  ////////////////////////////////////////////////////////////////////////////////
  // CLEANUP AND OPTIMIZATION
  ////////////////////////////////////////////////////////////////////////////////
  
  provisioner "shell" {
    inline = [
      "set -e",
      "echo 'Cleaning up for optimization...'",
      
      // Remove package caches
      "sudo apt-get autoremove -y",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /var/cache/apt/archives/*",
      
      // Clean logs
      "sudo find /var/log -type f -delete",
      "sudo touch /var/log/lastlog",
      "sudo chown root:utmp /var/log/lastlog",
      "sudo chmod 664 /var/log/lastlog",
      
      // Remove temporary files
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*",
      
      // Clear bash history
      "history -c",
      "cat /dev/null > ~/.bash_history",
      
      // Remove SSH host keys (will be regenerated on first boot)
      "sudo rm -f /etc/ssh/ssh_host_*",
      
      // Clear cloud-init artifacts
      "sudo cloud-init clean --logs --seed",
      
      // Remove machine-id (will be regenerated)
      "sudo truncate -s 0 /etc/machine-id",
      
      // Zero out free space for better compression (optional, takes time)
      // "sudo dd if=/dev/zero of=/EMPTY bs=1M || true",
      // "sudo rm -f /EMPTY",
    ]
  }
  
  // Optional: Validate the AMI after creation
  // provisioner "shell-local" {
  //   inline = [
  //     "echo 'Running post-build validation...'",
  //     "./scripts/validate-ami.sh ${build.ID}",
  //   ]
  // }
}

// Alternative build: Use HCP Packer base image
build {
  name = "from-hcp-base"
  
  sources = ["source.amazon-ebs.optimized"]
  
  // This build assumes most setup is in the base image
  // Only application-specific provisioning here
  
  provisioner "shell" {
    inline = [
      "echo 'Deploying application to HCP base image...'",
    ]
  }
  
  provisioner "file" {
    source      = "app/"
    destination = "/tmp/app/"
  }
  
  provisioner "shell" {
    script = "scripts/deploy-only.sh"
  }
  
  // Minimal cleanup (base already optimized)
  provisioner "shell" {
    inline = [
      "sudo cloud-init clean",
      "history -c",
    ]
  }
}
