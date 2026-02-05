---
name: aws-solutions-architect
description: Expert guidance for AWS infrastructure architecture with GitHub Actions CI/CD pipelines, Terraform Cloud/HCP Terraform workflows, and HashiCorp Packer AMI automation. Use when designing or implementing AWS infrastructure automation, creating CI/CD pipelines for infrastructure deployment, building golden AMIs with Packer, configuring Terraform Cloud workspaces, or integrating these tools for end-to-end infrastructure workflows. Covers AWS Well-Architected principles, security best practices, VPC design, IAM policies, and multi-account strategies.
---

# AWS Solutions Architect

Expert guidance for architecting AWS infrastructure with modern automation tooling including GitHub Actions, Terraform Cloud, and HashiCorp Packer.

## Core Capabilities

### 1. AWS Infrastructure Architecture

Apply AWS Well-Architected Framework principles across operational excellence, security, reliability, performance efficiency, cost optimization, and sustainability pillars.

**VPC Design Patterns:**
- Multi-tier architectures with public/private/data subnets across multiple AZs
- Transit Gateway for multi-VPC connectivity and hybrid cloud integration
- VPC peering for direct VPC-to-VPC communication
- PrivateLink for secure service access without internet exposure
- Network segmentation with security groups and NACLs

**Multi-Account Strategy:**
- AWS Organizations with SCPs for governance
- Control Tower for account vending and guardrails
- Separate accounts for prod/staging/dev/security/logging
- Cross-account IAM roles for least-privilege access
- Centralized logging with CloudWatch Logs aggregation

**Compute Patterns:**
- EC2 with Auto Scaling Groups for scalable workloads
- ECS/EKS for containerized applications
- Lambda for serverless event-driven architectures
- Spot instances for cost optimization on fault-tolerant workloads

### 2. GitHub Actions CI/CD Pipelines

Design GitHub Actions workflows for infrastructure automation with security, efficiency, and reliability.

**Workflow Structure:**
```yaml
name: Infrastructure Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  TF_VERSION: 1.9.0

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
          
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}
```

**Best Practices:**
- Use OIDC for AWS authentication (no long-lived credentials)
- Implement matrix strategies for multi-environment deployments
- Cache dependencies to reduce workflow runtime
- Use reusable workflows for common patterns
- Implement approval gates for production deployments
- Store sensitive data in GitHub Secrets or AWS Secrets Manager
- Use environment protection rules for branch restrictions

**Security Patterns:**
- OIDC trust relationships with GitHub identity provider
- Least-privilege IAM roles scoped to specific workflows
- Branch protection rules requiring status checks
- CODEOWNERS for infrastructure change approvals
- Secret scanning and dependency vulnerability alerts

See `references/github_actions.md` for comprehensive workflow patterns and examples.

### 3. Terraform Cloud/HCP Terraform Integration

Configure Terraform Cloud workspaces, VCS integration, and remote state management for collaborative infrastructure as code.

**Workspace Organization:**
- Workspace per environment (dev/staging/prod) or per component
- Project-based organization for logical grouping
- Variable sets for shared configuration across workspaces
- Dynamic provider credentials with OIDC for AWS

**VCS-Driven Workflows:**
```hcl
terraform {
  cloud {
    organization = "my-org"
    
    workspaces {
      name = "aws-production"
    }
  }
}
```

**Run Triggers and Automation:**
- Auto-apply on main branch for non-production
- Manual approval for production workspaces
- Run triggers to chain workspace dependencies
- Sentinel policies for governance and compliance
- Cost estimation for change review

**State Management:**
- Remote state in Terraform Cloud with encryption at rest
- State locking to prevent concurrent modifications
- State versioning for rollback capability
- Cross-workspace data sharing with remote state data sources

See `references/terraform_cloud.md` for workspace configuration patterns and API integration.

### 4. HashiCorp Packer AMI Building

Automate AMI creation with Packer for immutable infrastructure patterns and consistent golden images.

**Packer Template Structure:**
```hcl
packer {
  required_plugins {
    amazon = {
      version = ">= 1.3.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

source "amazon-ebs" "golden_ami" {
  ami_name      = "app-server-{{timestamp}}"
  instance_type = "t3.medium"
  region        = "us-east-1"
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/*ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"] # Canonical
  }
  ssh_username = "ubuntu"
  
  tags = {
    Name        = "GoldenAMI"
    Environment = "Production"
    BuildDate   = "{{timestamp}}"
  }
}

build {
  sources = ["source.amazon-ebs.golden_ami"]
  
  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y nginx",
      "sudo systemctl enable nginx"
    ]
  }
  
  provisioner "ansible" {
    playbook_file = "./playbook.yml"
  }
}
```

**Best Practices:**
- Use manifest post-processor to track AMI IDs
- Implement AMI cleanup strategy to remove old AMIs
- Tag AMIs with version, environment, and build metadata
- Use HCP Packer for AMI registry and lifecycle management
- Store Packer templates in version control
- Validate images with InSpec or similar tools

**Integration Patterns:**
- GitHub Actions triggers Packer builds on code changes
- Packer outputs AMI ID for Terraform consumption
- HCP Packer tracks AMI ancestry and assignment to environments
- Terraform data sources reference HCP Packer iterations

See `references/packer.md` for comprehensive build patterns and provisioner configurations.

### 5. End-to-End Integration Workflows

Combine GitHub Actions, Terraform Cloud, and Packer for complete infrastructure automation pipelines.

**Golden AMI Pipeline:**
1. Code change to Packer templates triggers GitHub Actions workflow
2. GitHub Actions runs Packer validate and build
3. Packer creates AMI and registers with HCP Packer
4. GitHub Actions updates Terraform variables with new AMI ID
5. Terraform Cloud run deploys new AMI to staging
6. Automated testing validates staging environment
7. Manual approval gate for production deployment
8. Terraform Cloud applies to production with new AMI

**Multi-Environment Deployment:**
```yaml
# .github/workflows/deploy.yml
name: Deploy Infrastructure

on:
  push:
    branches: [main]

jobs:
  build-ami:
    runs-on: ubuntu-latest
    outputs:
      ami-id: ${{ steps.packer.outputs.ami_id }}
    steps:
      - name: Build AMI
        id: packer
        run: packer build -machine-readable template.pkr.hcl
        
  deploy-staging:
    needs: build-ami
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Terraform Cloud Run
        run: |
          curl -X POST https://app.terraform.io/api/v2/runs \
            -H "Authorization: Bearer ${{ secrets.TF_API_TOKEN }}" \
            -d '{"data":{"type":"runs","attributes":{"variables":[{"key":"ami_id","value":"${{ needs.build-ami.outputs.ami-id }}"}]}}}'
```

**Security and Compliance:**
- Implement policy as code with Sentinel or OPA
- Use AWS Config rules for compliance monitoring
- Enable CloudTrail for audit logging
- Implement secrets management with AWS Secrets Manager
- Use KMS for encryption at rest
- Enable VPC Flow Logs for network monitoring

## Decision Framework

**When to use GitHub Actions:**
- Need VCS-native CI/CD with repository integration
- Want workflow-as-code stored alongside infrastructure code
- Require matrix builds or complex conditional logic
- Need marketplace actions for common tasks

**When to use Terraform Cloud:**
- Need collaborative infrastructure as code workflows
- Want remote state management with locking
- Require policy enforcement with Sentinel
- Need cost estimation before apply
- Want private registry for modules
- Need detailed audit logging for compliance

**When to use Packer:**
- Need immutable infrastructure with golden AMIs
- Want consistent server images across environments
- Require multi-cloud image building (AWS, Azure, GCP)
- Need automated security hardening and patching
- Want faster instance launch times with pre-baked images

## Common Patterns

**Pattern 1: Immutable Infrastructure with Blue/Green Deployment**
- Packer builds new AMI with application updates
- Terraform creates new ASG with new AMI
- ALB shifts traffic gradually to new instances
- Old ASG decommissioned after validation

**Pattern 2: GitOps Infrastructure Deployment**
- Infrastructure code in Git repository
- Pull request triggers validation and plan
- Merge to main triggers automatic deployment
- Terraform Cloud manages state and runs

**Pattern 3: Multi-Account AWS Organization**
- Separate AWS accounts for environments
- Cross-account roles for deployments
- Centralized Terraform Cloud organization
- GitHub Actions deploys to multiple accounts

## Resources

### references/
Detailed documentation for each technology area:
- `github_actions.md` - Comprehensive GitHub Actions workflows, reusable actions, and security patterns
- `terraform_cloud.md` - Workspace management, API integration, and policy as code
- `packer.md` - Build templates, provisioners, and HCP Packer integration
- `aws_architecture.md` - AWS service patterns, Well-Architected best practices, and reference architectures

### assets/
Template files and boilerplate:
- `github_workflows/` - Starter GitHub Actions workflow templates
- `terraform_modules/` - Reusable Terraform module examples
- `packer_templates/` - Packer template examples for common use cases
