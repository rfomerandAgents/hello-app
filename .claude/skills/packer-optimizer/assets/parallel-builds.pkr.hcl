// Parallel Multi-Platform Build Template
// This template demonstrates best practices for building multiple platform variants in parallel

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

variable "app_version" {
  type        = string
  description = "Application version"
  default     = "1.0.0"
}

variable "build_number" {
  type        = string
  description = "Build number or commit SHA"
  default     = "local"
}

// Common configurations shared across all builds
locals {
  timestamp    = regex_replace(timestamp(), "[- TZ:]", "")
  common_tags = {
    Version    = var.app_version
    BuildDate  = local.timestamp
    BuildTool  = "Packer"
    ManagedBy  = "Packer"
  }
}

// Platform configurations
locals {
  platforms = {
    ubuntu2004 = {
      ami_filter = "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-*-server-*"
      ami_owner  = "099720109477"  // Canonical
      ssh_user   = "ubuntu"
    }
    ubuntu2204 = {
      ami_filter = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-*-server-*"
      ami_owner  = "099720109477"  // Canonical
      ssh_user   = "ubuntu"
    }
    debian11 = {
      ami_filter = "debian-11-*-amd64-*"
      ami_owner  = "136693071363"  // Debian
      ssh_user   = "admin"
    }
    amazonlinux2 = {
      ami_filter = "amzn2-ami-hvm-*-x86_64-gp2"
      ami_owner  = "137112412989"  // Amazon
      ssh_user   = "ec2-user"
    }
    rhel9 = {
      ami_filter = "RHEL-9.*_HVM-*-x86_64-*"
      ami_owner  = "309956199498"  // Red Hat
      ssh_user   = "ec2-user"
    }
  }
}

////////////////////////////////////////////////////////////////////////////////
// DATA SOURCES - Find latest AMIs for each platform
////////////////////////////////////////////////////////////////////////////////

data "amazon-ami" "ubuntu2004" {
  filters = {
    name                = local.platforms.ubuntu2004.ami_filter
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = [local.platforms.ubuntu2004.ami_owner]
  most_recent = true
  region      = var.region
}

data "amazon-ami" "ubuntu2204" {
  filters = {
    name                = local.platforms.ubuntu2204.ami_filter
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = [local.platforms.ubuntu2204.ami_owner]
  most_recent = true
  region      = var.region
}

data "amazon-ami" "debian11" {
  filters = {
    name                = local.platforms.debian11.ami_filter
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = [local.platforms.debian11.ami_owner]
  most_recent = true
  region      = var.region
}

data "amazon-ami" "amazonlinux2" {
  filters = {
    name                = local.platforms.amazonlinux2.ami_filter
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = [local.platforms.amazonlinux2.ami_owner]
  most_recent = true
  region      = var.region
}

data "amazon-ami" "rhel9" {
  filters = {
    name                = local.platforms.rhel9.ami_filter
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = [local.platforms.rhel9.ami_owner]
  most_recent = true
  region      = var.region
}

////////////////////////////////////////////////////////////////////////////////
// SOURCE DEFINITIONS - One per platform
////////////////////////////////////////////////////////////////////////////////

source "amazon-ebs" "ubuntu2004" {
  region        = var.region
  source_ami    = data.amazon-ami.ubuntu2004.id
  instance_type = "t3.medium"
  ssh_username  = local.platforms.ubuntu2004.ssh_user
  ami_name      = "app-ubuntu2004-${var.app_version}-${local.timestamp}"
  
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
  
  tags = merge(local.common_tags, {
    Name     = "app-ubuntu2004-${var.app_version}"
    Platform = "Ubuntu 20.04"
    OS       = "ubuntu"
    OSVersion = "20.04"
  })
}

source "amazon-ebs" "ubuntu2204" {
  region        = var.region
  source_ami    = data.amazon-ami.ubuntu2204.id
  instance_type = "t3.medium"
  ssh_username  = local.platforms.ubuntu2204.ssh_user
  ami_name      = "app-ubuntu2204-${var.app_version}-${local.timestamp}"
  
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
  
  tags = merge(local.common_tags, {
    Name     = "app-ubuntu2204-${var.app_version}"
    Platform = "Ubuntu 22.04"
    OS       = "ubuntu"
    OSVersion = "22.04"
  })
}

source "amazon-ebs" "debian11" {
  region        = var.region
  source_ami    = data.amazon-ami.debian11.id
  instance_type = "t3.medium"
  ssh_username  = local.platforms.debian11.ssh_user
  ami_name      = "app-debian11-${var.app_version}-${local.timestamp}"
  
  launch_block_device_mappings {
    device_name           = "/dev/xvda"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
  
  tags = merge(local.common_tags, {
    Name     = "app-debian11-${var.app_version}"
    Platform = "Debian 11"
    OS       = "debian"
    OSVersion = "11"
  })
}

source "amazon-ebs" "amazonlinux2" {
  region        = var.region
  source_ami    = data.amazon-ami.amazonlinux2.id
  instance_type = "t3.medium"
  ssh_username  = local.platforms.amazonlinux2.ssh_user
  ami_name      = "app-amazonlinux2-${var.app_version}-${local.timestamp}"
  
  launch_block_device_mappings {
    device_name           = "/dev/xvda"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
  
  tags = merge(local.common_tags, {
    Name     = "app-amazonlinux2-${var.app_version}"
    Platform = "Amazon Linux 2"
    OS       = "amazonlinux"
    OSVersion = "2"
  })
}

source "amazon-ebs" "rhel9" {
  region        = var.region
  source_ami    = data.amazon-ami.rhel9.id
  instance_type = "t3.medium"
  ssh_username  = local.platforms.rhel9.ssh_user
  ami_name      = "app-rhel9-${var.app_version}-${local.timestamp}"
  
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
  
  tags = merge(local.common_tags, {
    Name     = "app-rhel9-${var.app_version}"
    Platform = "RHEL 9"
    OS       = "rhel"
    OSVersion = "9"
  })
}

////////////////////////////////////////////////////////////////////////////////
// BUILD CONFIGURATION - All platforms in parallel
////////////////////////////////////////////////////////////////////////////////

build {
  name = "multi-platform-parallel"
  
  // Optional: HCP Packer integration
  // hcp_packer_registry {
  //   bucket_name = "app-multiplatform"
  //   description = "Multi-platform build v${var.app_version}"
  //   bucket_labels = merge(local.common_tags, {
  //     "build_type" = "multi-platform"
  //   })
  // }
  
  // List all sources - they will build in parallel
  sources = [
    "source.amazon-ebs.ubuntu2004",
    "source.amazon-ebs.ubuntu2204",
    "source.amazon-ebs.debian11",
    "source.amazon-ebs.amazonlinux2",
    "source.amazon-ebs.rhel9",
  ]
  
  // Control parallelization
  // max_parallel = 3  // Limit to 3 simultaneous builds
  
  ////////////////////////////////////////////////////////////////////////////////
  // COMMON PROVISIONING - Applied to all platforms
  ////////////////////////////////////////////////////////////////////////////////
  
  // Wait for cloud-init
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init...'",
      "cloud-init status --wait || true",
    ]
  }
  
  // Detect OS family for appropriate package manager
  provisioner "shell" {
    inline = [
      "set -e",
      "echo 'Detecting OS family...'",
      "if [ -f /etc/debian_version ]; then",
      "  echo 'OS_FAMILY=debian' > /tmp/os_family",
      "elif [ -f /etc/redhat-release ]; then",
      "  echo 'OS_FAMILY=rhel' > /tmp/os_family",
      "fi",
    ]
  }
  
  // Update system (Debian-based)
  provisioner "shell" {
    only = [
      "amazon-ebs.ubuntu2004",
      "amazon-ebs.ubuntu2204",
      "amazon-ebs.debian11",
    ]
    inline = [
      "set -e",
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
      "sudo apt-get install -y --no-install-recommends curl ca-certificates",
    ]
  }
  
  // Update system (RHEL-based)
  provisioner "shell" {
    only = [
      "amazon-ebs.amazonlinux2",
      "amazon-ebs.rhel9",
    ]
    inline = [
      "set -e",
      "sudo yum update -y",
      "sudo yum install -y curl ca-certificates",
    ]
  }
  
  // Deploy application (common for all)
  provisioner "file" {
    source      = "app/"
    destination = "/tmp/app/"
  }
  
  provisioner "shell" {
    inline = [
      "sudo mkdir -p /opt/app",
      "sudo mv /tmp/app/* /opt/app/",
      "sudo chmod +x /opt/app/bin/*",
    ]
  }
  
  ////////////////////////////////////////////////////////////////////////////////
  // PLATFORM-SPECIFIC CONFIGURATION
  ////////////////////////////////////////////////////////////////////////////////
  
  // Ubuntu-specific configuration
  provisioner "shell" {
    only = [
      "amazon-ebs.ubuntu2004",
      "amazon-ebs.ubuntu2204",
    ]
    inline = [
      "echo 'Applying Ubuntu-specific configuration...'",
      "sudo systemctl enable app.service",
    ]
  }
  
  // RHEL-specific configuration
  provisioner "shell" {
    only = [
      "amazon-ebs.rhel9",
      "amazon-ebs.amazonlinux2",
    ]
    inline = [
      "echo 'Applying RHEL-specific configuration...'",
      "sudo systemctl enable app.service",
    ]
  }
  
  ////////////////////////////////////////////////////////////////////////////////
  // CLEANUP - Common for all platforms
  ////////////////////////////////////////////////////////////////////////////////
  
  // Cleanup (Debian-based)
  provisioner "shell" {
    only = [
      "amazon-ebs.ubuntu2004",
      "amazon-ebs.ubuntu2204",
      "amazon-ebs.debian11",
    ]
    inline = [
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
    ]
  }
  
  // Cleanup (RHEL-based)
  provisioner "shell" {
    only = [
      "amazon-ebs.amazonlinux2",
      "amazon-ebs.rhel9",
    ]
    inline = [
      "sudo yum clean all",
      "sudo rm -rf /var/cache/yum",
    ]
  }
  
  // Common cleanup
  provisioner "shell" {
    inline = [
      "sudo rm -rf /tmp/*",
      "sudo cloud-init clean",
      "history -c",
    ]
  }
}

// Alternative: Build specific platforms only
build {
  name = "ubuntu-only"
  
  // Build only Ubuntu variants
  sources = [
    "source.amazon-ebs.ubuntu2004",
    "source.amazon-ebs.ubuntu2204",
  ]
  
  // Use same provisioners as above
  // (Abbreviated for clarity)
}

// Alternative: Sequential builds with validation
build {
  name = "sequential-validated"
  
  // Build one at a time with validation between
  max_parallel = 1
  
  sources = [
    "source.amazon-ebs.ubuntu2204",
  ]
  
  // Full provisioning here...
  
  // Validate after build
  provisioner "shell-local" {
    inline = [
      "echo 'Validating AMI...'",
      "./scripts/validate-ami.sh ${build.ID}",
    ]
  }
}
