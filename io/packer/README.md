# Packer AMI Builder

This directory contains Packer templates for building application AMIs.

## Overview

The Packer template creates a custom Amazon Machine Image (AMI) with:
- Ubuntu 22.04 LTS base image
- Node.js 18.x (LTS)
- Nginx web server
- Application deployment scripts

## Prerequisites

- Packer >= 1.8
- AWS CLI configured with credentials
- AWS permissions to create AMIs

## Available Scripts

- `install-nodejs.sh` - Installs Node.js 18.x LTS
- `install-nginx.sh` - Installs and configures nginx
- `deploy-app.sh` - Deploys application files (customize as needed)

## Usage

### Initialize Packer

```bash
packer init app.pkr.hcl
```

### Validate Template

```bash
packer validate app.pkr.hcl
```

### Build AMI

```bash
packer build app.pkr.hcl
```

### Build for Specific Environment

```bash
packer build -var 'environment=production' app.pkr.hcl
```

## Customization

### Adding New Provisioners

Edit `app.pkr.hcl` and add new provisioner blocks:

```hcl
provisioner "shell" {
  script = "${path.root}/scripts/your-script.sh"
}
```

### Changing Base Image

Modify the `amazon-ami` data source filters to use a different base image.

### Deploying Application Files

Uncomment the file provisioner in `app.pkr.hcl` and customize the source path.

## Variables

- `aws_region` - AWS region (default: us-east-1)
- `instance_type` - Build instance type (default: t2.micro)
- `ami_name_prefix` - AMI name prefix (default: {{PROJECT_NAME_LOWER}})
- `environment` - Environment name (default: dev)

## Output

After building, Packer outputs the AMI ID. Use this ID in your Terraform variables.
