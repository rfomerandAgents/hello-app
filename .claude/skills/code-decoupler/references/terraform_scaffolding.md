# Terraform Scaffolding Reference

This document provides complete templates for generating generic Terraform scaffolding in the decoupled template.

## Overview

The Terraform scaffolding creates a working infrastructure template with:
- Generic AWS provider configuration
- Common variables for typical deployments
- Placeholder resource definitions
- Packer AMI builder template
- Deployment automation scripts

## File Templates

### io/terraform/main.tf

```hcl
# {{PROJECT_NAME}} Infrastructure
#
# This file contains the main infrastructure resources.
# Customize the resources below for your specific needs.

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Example EC2 Instance
# Uncomment and customize for your application
#
# resource "aws_instance" "app" {
#   ami           = var.app_ami_id
#   instance_type = var.instance_type
#   key_name      = var.key_name
#
#   vpc_security_group_ids = [aws_security_group.app.id]
#
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-app"
#     Environment = var.environment
#     ManagedBy   = "Terraform"
#   }
#
#   user_data = <<-EOF
#               #!/bin/bash
#               # Add your initialization script here
#               EOF
# }

# Example Security Group
# Uncomment and customize for your security requirements
#
# resource "aws_security_group" "app" {
#   name        = "${var.project_name}-${var.environment}-sg"
#   description = "Security group for ${var.project_name} application"
#
#   ingress {
#     from_port   = 80
#     to_port     = 80
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#     description = "HTTP access"
#   }
#
#   ingress {
#     from_port   = 22
#     to_port     = 22
#     protocol    = "tcp"
#     cidr_blocks = var.ssh_cidr_blocks
#     description = "SSH access"
#   }
#
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#     description = "Allow all outbound traffic"
#   }
#
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-sg"
#     Environment = var.environment
#     ManagedBy   = "Terraform"
#   }
# }

# Example Elastic IP
# Uncomment to assign a static IP to your instance
#
# resource "aws_eip" "app" {
#   instance = aws_instance.app.id
#   domain   = "vpc"
#
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-eip"
#     Environment = var.environment
#     ManagedBy   = "Terraform"
#   }
# }
```

---

### io/terraform/variables.tf

```hcl
# Common Variables for {{PROJECT_NAME}}

variable "project_name" {
  description = "Name of the project (used in resource naming)"
  type        = string
  default     = "{{PROJECT_NAME_LOWER}}"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "app_ami_id" {
  description = "AMI ID for the application (built with Packer)"
  type        = string
  default     = ""  # Set this in terraform.tfvars or via -var flag
}

variable "key_name" {
  description = "Name of the SSH key pair for EC2 instance access"
  type        = string
  default     = "{{PROJECT_NAME_LOWER}}-key"
}

variable "ssh_public_key" {
  description = "SSH public key content for EC2 instance access"
  type        = string
  default     = ""  # Set this in terraform.tfvars or environment variable
  sensitive   = true
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production!
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

---

### io/terraform/outputs.tf

```hcl
# Outputs for {{PROJECT_NAME}}

# output "instance_id" {
#   description = "ID of the EC2 instance"
#   value       = aws_instance.app.id
# }

# output "public_ip" {
#   description = "Public IP address of the EC2 instance"
#   value       = aws_eip.app.public_ip
# }

# output "website_url" {
#   description = "URL to access the deployed website"
#   value       = "http://${aws_eip.app.public_ip}"
# }

# output "ssh_command" {
#   description = "SSH command to access the instance"
#   value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.app.public_ip}"
# }

# output "security_group_id" {
#   description = "ID of the security group"
#   value       = aws_security_group.app.id
# }
```

---

### io/terraform/terraform.tf

```hcl
# Terraform Configuration for {{PROJECT_NAME}}

terraform {
  required_version = ">= 1.0"

  # Uncomment and configure for Terraform Cloud backend
  # cloud {
  #   organization = "{{ORGANIZATION}}"
  #
  #   workspaces {
  #     name = "{{PROJECT_NAME_LOWER}}-${var.environment}"
  #   }
  # }

  # Or use S3 backend
  # backend "s3" {
  #   bucket         = "{{PROJECT_NAME_LOWER}}-terraform-state"
  #   key            = "{{ENVIRONMENT}}/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "{{PROJECT_NAME_LOWER}}-terraform-lock"
  # }
}
```

---

### io/terraform/.gitignore

```
# Terraform state files
*.tfstate
*.tfstate.*
*.tfstate.backup

# Terraform variable files (may contain secrets)
*.tfvars
!terraform.tfvars.example

# Terraform directory
.io/terraform/
.terraform.lock.hcl

# Crash log files
crash.log
crash.*.log

# Override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# CLI configuration files
.terraformrc
terraform.rc

# Packer build logs
logs/*.log
io/packer/manifest.json
```

---

### io/terraform/README.md

```markdown
# {{PROJECT_NAME}} Infrastructure

This directory contains Terraform infrastructure as code for {{PROJECT_NAME}}.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with credentials
- Packer (for AMI building)

## Quick Start

### 1. Configure Variables

Create a `terraform.tfvars` file:

\`\`\`hcl
project_name     = "{{PROJECT_NAME_LOWER}}"
environment      = "dev"
aws_region       = "us-east-1"
instance_type    = "t2.micro"
ssh_public_key   = "ssh-rsa AAAA..."  # Your SSH public key
\`\`\`

### 2. Build AMI with Packer

\`\`\`bash
cd packer
packer init app.pkr.hcl
packer build app.pkr.hcl
\`\`\`

### 3. Deploy Infrastructure

\`\`\`bash
terraform init
terraform plan
terraform apply
\`\`\`

## Directory Structure

\`\`\`
io/terraform/
├── main.tf              # Main infrastructure resources
├── variables.tf         # Input variable declarations
├── outputs.tf           # Output value declarations
├── terraform.tf         # Terraform and backend configuration
├── io/packer/              # Packer AMI templates
│   ├── app.pkr.hcl      # Application AMI builder
│   └── scripts/         # Provisioner scripts
└── scripts/             # Deployment automation scripts
    ├── build-ami.sh     # Build AMI
    ├── deploy.sh        # Deploy infrastructure
    └── destroy.sh       # Destroy infrastructure
\`\`\`

## Usage

### Building AMIs

Build a new application AMI:

\`\`\`bash
./scripts/build-ami.sh
\`\`\`

### Deploying Infrastructure

Deploy with validation:

\`\`\`bash
./scripts/deploy.sh
\`\`\`

### Destroying Infrastructure

Remove all resources:

\`\`\`bash
./scripts/destroy.sh
\`\`\`

## Configuration

### Required Variables

- \`project_name\` - Project identifier
- \`environment\` - Deployment environment (dev/staging/production)
- \`app_ami_id\` - AMI ID from Packer build
- \`ssh_public_key\` - SSH public key for instance access

### Optional Variables

- \`aws_region\` - AWS region (default: us-east-1)
- \`instance_type\` - EC2 instance type (default: t2.micro)
- \`ssh_cidr_blocks\` - SSH access CIDR blocks

## Terraform Cloud Integration

To use Terraform Cloud for remote state:

1. Uncomment the \`cloud\` block in \`terraform.tf\`
2. Set \`organization\` to your Terraform Cloud org
3. Run \`terraform login\`
4. Run \`terraform init\`

## Security

- Never commit \`terraform.tfvars\` with secrets
- Restrict \`ssh_cidr_blocks\` in production
- Use Terraform Cloud for state encryption
- Rotate SSH keys regularly

## Troubleshooting

### Terraform init fails

- Check AWS credentials: \`aws sts get-caller-identity\`
- Verify Terraform version: \`terraform version\`

### Packer build fails

- Check Packer logs in \`logs/\`
- Verify AMI base image is available
- Check AWS credentials

### Instance not accessible

- Verify security group allows HTTP/SSH
- Check instance is running: \`aws ec2 describe-instances\`
- Verify SSH key is correct
\`\`\`

---

### io/terraform/io/packer/app.pkr.hcl

```hcl
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
```

---

### io/terraform/io/packer/scripts/install-nodejs.sh

```bash
#!/bin/bash
set -e

echo "=== Installing Node.js ==="

# Install Node.js 18.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version

echo "Node.js installation complete"
```

---

### io/terraform/io/packer/scripts/install-nginx.sh

```bash
#!/bin/bash
set -e

echo "=== Installing nginx ==="

# Install nginx
sudo apt-get install -y nginx

# Enable nginx service
sudo systemctl enable nginx
sudo systemctl start nginx

# Verify installation
nginx -v

echo "nginx installation complete"
```

---

### io/terraform/io/packer/scripts/deploy-app.sh

```bash
#!/bin/bash
set -e

echo "=== Deploying application ==="

# Example deployment script
# Customize for your application

# Create web root
sudo mkdir -p /var/www/html

# Copy application files
sudo cp -r /tmp/app/* /var/www/html/

# Set permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Configure nginx
sudo tee /etc/nginx/sites-available/default > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html;

    server_name _;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

echo "Application deployment complete"
```

---

### io/terraform/scripts/build-ami.sh

```bash
#!/bin/bash
set -e

echo "=== Building AMI with Packer ==="

cd "$(dirname "$0")/.."

# Navigate to packer directory
cd packer

# Initialize Packer
packer init app.pkr.hcl

# Validate template
packer validate app.pkr.hcl

# Build AMI
packer build app.pkr.hcl

echo "AMI build complete!"
```

---

### io/terraform/scripts/deploy.sh

```bash
#!/bin/bash
set -e

echo "=== Deploying Infrastructure ==="

cd "$(dirname "$0")/.."

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=tfplan

# Ask for confirmation
read -p "Apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply changes
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo "Deployment complete!"
terraform output
```

---

### io/terraform/scripts/destroy.sh

```bash
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
```

---

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{PROJECT_NAME}}` | Human-readable project name | "My Project" |
| `{{PROJECT_NAME_LOWER}}` | Lowercase project identifier | "my-project" |
| `{{ORGANIZATION}}` | Terraform Cloud organization | "my-company" |
| `{{AWS_REGION}}` | Default AWS region | "us-east-1" |
| `{{ENVIRONMENT}}` | Environment name | "dev", "staging", "production" |

## Customization Checklist

After generating the scaffold:

- [ ] Replace all `{{PLACEHOLDER}}` values
- [ ] Uncomment required resources in main.tf
- [ ] Set variables in terraform.tfvars
- [ ] Configure backend in terraform.tf
- [ ] Customize Packer provisioners
- [ ] Update deployment scripts with project paths
- [ ] Restrict SSH CIDR blocks in production
- [ ] Add additional resources as needed
- [ ] Test with `terraform plan`
- [ ] Build AMI with Packer
- [ ] Deploy with `terraform apply`
