# {{PROJECT_NAME}} Infrastructure

This directory contains Terraform infrastructure code for deploying the application on AWS.

## Architecture

- **EC2 Instance**: Hosts the application with nginx
- **Security Group**: HTTP, HTTPS, and SSH access
- **Elastic IP**: Stable public IP for DNS
- **AMI**: Custom AMI built with Packer

## Quick Start

### 1. Configure Terraform Cloud

Edit `terraform.tf` and set your organization:
```hcl
cloud {
  organization = "your-org-name"
  workspaces {
    project = "your-project"
    tags    = ["{{PROJECT_NAME_SLUG}}"]
  }
}
```

### 2. Create Workspaces

Create workspaces in Terraform Cloud:
- `{{PROJECT_NAME_SLUG}}-sandbox`
- `{{PROJECT_NAME_SLUG}}-dev`
- `{{PROJECT_NAME_SLUG}}-staging`
- `{{PROJECT_NAME_SLUG}}-prod`

### 3. Configure Variables

Set these variables in Terraform Cloud:

| Variable | Type | Description |
|----------|------|-------------|
| `ssh_public_key` | Sensitive | SSH public key for EC2 access |
| `ssl_cert` | Sensitive | SSL certificate (PEM format) |
| `ssl_key` | Sensitive | SSL private key (PEM format) |

### 4. Initialize and Deploy

```bash
# Set workspace
export TF_WORKSPACE={{PROJECT_NAME_SLUG}}-sandbox

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply
```

## Files

| File | Description |
|------|-------------|
| `main.tf` | Main infrastructure resources |
| `variables.tf` | Input variables with validation |
| `outputs.tf` | Output values |
| `locals.tf` | Local values and computed data |
| `terraform.tf` | Backend and provider configuration |

## Packer AMI Builds

AMIs are built using Packer templates in `io/packer/`.

```bash
cd packer
packer init app.pkr.hcl
packer build app.pkr.hcl
```

## Security Best Practices

- IMDSv2 is enforced on all EC2 instances
- Root volumes are encrypted
- SSH access is configurable via `allowed_ssh_cidr_blocks`
- Secrets are stored in Terraform Cloud (never in code)

## Environments

| Environment | Use Case |
|-------------|----------|
| `sandbox` | Experimental changes |
| `dev` | Development and testing |
| `staging` | Pre-production validation |
| `prod` | Production deployment |

## Destroying Infrastructure

```bash
terraform plan -destroy
terraform destroy
```

Or use the GitHub Actions "Destroy Infrastructure" workflow.

## Troubleshooting

### State Lock Issues
```bash
terraform force-unlock <lock-id>
```

### AMI Not Found
Ensure Packer has built an AMI with the pattern `{{PROJECT_NAME_SLUG}}-*`.

### SSH Access Denied
Check that your IP is in `allowed_ssh_cidr_blocks`.
