# Packer Template for {{PROJECT_NAME}} Application AMI

packer {
  required_plugins {
    amazon = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "ami_name_prefix" {
  type    = string
  default = "{{PROJECT_NAME_LOWER}}"
}

variable "environment" {
  type    = string
  default = "dev"
}

# Source AMI - Ubuntu 22.04 LTS
data "amazon-ami" "ubuntu" {
  filters = {
    name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["099720109477"]  # Canonical
  region      = var.aws_region
}

source "amazon-ebs" "app" {
  region        = var.aws_region
  instance_type = var.instance_type
  source_ami    = data.amazon-ami.ubuntu.id
  ssh_username  = "ubuntu"

  ami_name        = "${var.ami_name_prefix}-${var.environment}-{{timestamp}}"
  ami_description = "{{PROJECT_NAME}} application AMI - ${var.environment}"

  tags = {
    Name        = "${var.ami_name_prefix}-${var.environment}"
    Environment = var.environment
    BuildDate   = "{{timestamp}}"
    BuildTool   = "Packer"
    ManagedBy   = "Infrastructure-as-Code"
  }

  # Performance optimizations
  ebs_optimized = true
  ena_support   = true
  sriov_support = true
}

build {
  sources = ["source.amazon-ebs.app"]

  # Update system packages
  provisioner "shell" {
    inline = [
      "echo '=== Updating system packages ==='",
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
    ]
  }

  # Install Node.js (customize version as needed)
  provisioner "shell" {
    script = "${path.root}/scripts/install-nodejs.sh"
  }

  # Install nginx (customize if using different web server)
  provisioner "shell" {
    script = "${path.root}/scripts/install-nginx.sh"
  }

  # Copy application files
  # Uncomment and customize for your application
  # provisioner "file" {
  #   source      = "../../app/out/"
  #   destination = "/tmp/app"
  # }

  # Deploy application
  # Uncomment and customize for your deployment
  # provisioner "shell" {
  #   script = "${path.root}/scripts/deploy-app.sh"
  # }

  # Cleanup
  provisioner "shell" {
    inline = [
      "echo '=== Cleaning up ==='",
      "sudo apt-get clean",
      "sudo rm -rf /tmp/*",
    ]
  }
}
