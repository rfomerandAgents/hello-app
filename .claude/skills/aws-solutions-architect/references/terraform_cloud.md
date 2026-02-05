# Terraform Cloud / HCP Terraform

Comprehensive guide for Terraform Cloud workspace management, API integration, and policy as code.

## Workspace Configuration

### VCS-Driven Workflow

**terraform.tf:**
```hcl
terraform {
  cloud {
    organization = "my-organization"
    
    workspaces {
      name = "aws-production"
      # OR for dynamic workspace selection:
      # tags = ["aws", "production"]
    }
  }
  
  required_version = ">= 1.9.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### CLI-Driven Workflow

For workspaces that don't use VCS integration:

```hcl
terraform {
  cloud {
    organization = "my-organization"
    
    workspaces {
      name = "cli-driven-workspace"
    }
  }
}
```

Run locally:
```bash
terraform login
terraform init
terraform plan
terraform apply
```

### Workspace Variables

**Terraform Variables:**
- Set in workspace UI or via API
- HCL or JSON format
- Can be sensitive (write-only)
- Can reference variable sets

**Environment Variables:**
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (legacy)
- TFC_CONFIGURATION_VERSION_GIT_COMMIT_SHA
- TFC_RUN_ID
- TFC_WORKSPACE_NAME

**Variable Sets:**
```hcl
# Applied to multiple workspaces
# Useful for common credentials, region settings, or tags

# Example structure in TFC:
# Variable Set: "aws-production"
# - AWS_REGION = us-east-1
# - ENVIRONMENT = production
# Applied to workspaces: aws-vpc, aws-eks, aws-rds
```

## Dynamic Provider Credentials

Replace static credentials with OIDC for AWS, Azure, and GCP.

### AWS Dynamic Credentials

**IAM Role Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/app.terraform.io"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "app.terraform.io:aud": "aws.workload.identity"
        },
        "StringLike": {
          "app.terraform.io:sub": "organization:ORG_NAME:project:PROJECT_NAME:workspace:WORKSPACE_NAME:run_phase:*"
        }
      }
    }
  ]
}
```

**Workspace Configuration:**
```hcl
provider "aws" {
  region = "us-east-1"
  
  # No static credentials needed
  # TFC will use dynamic credentials automatically
}
```

**Workspace Environment Variables:**
```
TFC_AWS_PROVIDER_AUTH = true
TFC_AWS_RUN_ROLE_ARN = arn:aws:iam::ACCOUNT_ID:role/TerraformCloudRole
```

## Remote State Data Sources

Reference outputs from other workspaces.

```hcl
data "terraform_remote_state" "vpc" {
  backend = "remote"
  
  config = {
    organization = "my-organization"
    workspaces = {
      name = "aws-vpc-production"
    }
  }
}

resource "aws_instance" "app" {
  ami           = "ami-12345678"
  instance_type = "t3.medium"
  subnet_id     = data.terraform_remote_state.vpc.outputs.private_subnet_ids[0]
  
  tags = {
    Name = "app-server"
  }
}
```

**Best Practice:** Share state via outputs, not direct resource references:

```hcl
# In VPC workspace
output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "security_group_id" {
  value = aws_security_group.app.id
}
```

## Run Triggers

Chain workspace dependencies to automate cascading updates.

**Scenario:** VPC changes should trigger dependent application infrastructure updates.

**Configuration:**
1. In dependent workspace (e.g., aws-app), configure source workspace (aws-vpc)
2. When aws-vpc completes successfully, aws-app run triggers automatically

**Terraform Configuration:**
```hcl
# No code changes needed
# Run triggers configured in TFC workspace settings
```

**API Configuration:**
```bash
curl \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  --data '{
    "data": {
      "type": "run-triggers",
      "relationships": {
        "sourceable": {
          "data": {
            "type": "workspaces",
            "id": "ws-SOURCE_WORKSPACE_ID"
          }
        }
      }
    }
  }' \
  https://app.terraform.io/api/v2/workspaces/ws-DEPENDENT_WORKSPACE_ID/run-triggers
```

## Sentinel Policies

Implement policy as code for governance and compliance.

### Example: Enforce Resource Tagging

**mandatory-tags.sentinel:**
```python
import "tfplan/v2" as tfplan

# Required tags for all resources
required_tags = ["Environment", "Owner", "CostCenter"]

# Get all AWS resources
aws_resources = filter tfplan.resource_changes as _, rc {
  rc.provider_name matches "^registry\\.terraform\\.io/hashicorp/aws" and
  rc.mode is "managed" and
  (rc.change.actions contains "create" or rc.change.actions contains "update")
}

# Validation function
validate_tags = func(resource) {
  # Check if tags exist
  if "tags" not in resource.change.after {
    return false
  }
  
  tags = resource.change.after.tags
  
  # Check for required tags
  for required_tags as tag {
    if tag not in keys(tags) {
      print("Resource", resource.address, "missing required tag:", tag)
      return false
    }
  }
  
  return true
}

# Main rule
main = rule {
  all aws_resources as _, resource {
    validate_tags(resource)
  }
}
```

### Example: Restrict Instance Types

**allowed-instance-types.sentinel:**
```python
import "tfplan/v2" as tfplan

# Allowed instance types
allowed_types = [
  "t3.micro",
  "t3.small",
  "t3.medium",
  "t3.large",
]

# Get all EC2 instances
instances = filter tfplan.resource_changes as _, rc {
  rc.type is "aws_instance" and
  rc.mode is "managed" and
  (rc.change.actions contains "create" or rc.change.actions contains "update")
}

# Validation
instance_type_allowed = rule {
  all instances as _, instance {
    instance.change.after.instance_type in allowed_types
  }
}

# Main rule with advisory enforcement
main = rule when instance_type_allowed is false {
  print("Warning: Instance type not in approved list")
  true  # Advisory only - allows override
}
```

### Policy Sets

Group related policies and apply to workspaces.

```hcl
# policy-set.hcl
policy "mandatory-tags" {
  source            = "./mandatory-tags.sentinel"
  enforcement_level = "hard-mandatory"  # Cannot be overridden
}

policy "allowed-instance-types" {
  source            = "./allowed-instance-types.sentinel"
  enforcement_level = "soft-mandatory"  # Requires override permission
}

policy "cost-estimation" {
  source            = "./cost-estimation.sentinel"
  enforcement_level = "advisory"  # Warning only
}
```

## Cost Estimation

Enable cost estimation for change review before apply.

**Features:**
- Automatic cost estimates for AWS, Azure, GCP resources
- Show monthly and hourly cost deltas
- Compare against previous runs
- Block applies based on cost thresholds (with Sentinel)

**Sentinel Cost Control:**
```python
import "tfrun"

# Maximum monthly cost increase
max_monthly_delta = 1000.0

# Get cost estimate
cost_estimate = decimal.new(tfrun.cost_estimate.delta_monthly_cost)

# Enforce cost limit
main = rule {
  cost_estimate.less_than(max_monthly_delta)
}
```

## Private Module Registry

Share reusable Terraform modules across your organization.

### Publishing Modules

**Module Structure:**
```
terraform-aws-vpc/
├── main.tf
├── variables.tf
├── outputs.tf
├── README.md
└── examples/
    └── complete/
        ├── main.tf
        └── README.md
```

**Version Tagging:**
```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

**Using Private Modules:**
```hcl
module "vpc" {
  source  = "app.terraform.io/my-org/vpc/aws"
  version = "1.0.0"
  
  cidr_block = "10.0.0.0/16"
  environment = "production"
}
```

## API Integration

Automate workspace management and runs via API.

### Create Workspace

```bash
curl \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  --data @payload.json \
  https://app.terraform.io/api/v2/organizations/ORG_NAME/workspaces
```

**payload.json:**
```json
{
  "data": {
    "type": "workspaces",
    "attributes": {
      "name": "aws-production",
      "terraform-version": "1.9.0",
      "working-directory": "io/terraform/",
      "auto-apply": false,
      "queue-all-runs": false,
      "file-triggers-enabled": true,
      "trigger-patterns": ["/modules/**/*"],
      "vcs-repo": {
        "identifier": "org/repo",
        "oauth-token-id": "ot-xxxxx",
        "branch": "main"
      }
    }
  }
}
```

### Trigger Run

```bash
# Create configuration version
CONFIG_VERSION=$(curl \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  --data '{"data":{"type":"configuration-versions","attributes":{"auto-queue-runs":true}}}' \
  https://app.terraform.io/api/v2/workspaces/ws-ID/configuration-versions \
  | jq -r '.data.id')

# Upload configuration
tar czf config.tar.gz -C terraform .
curl \
  --header "Content-Type: application/octet-stream" \
  --request PUT \
  --data-binary @config.tar.gz \
  https://app.terraform.io/api/v2/configuration-versions/${CONFIG_VERSION}/upload
```

### Apply Run

```bash
# Get current run
RUN_ID=$(curl \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  https://app.terraform.io/api/v2/workspaces/ws-ID/runs?page%5Bsize%5D=1 \
  | jq -r '.data[0].id')

# Apply run
curl \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  https://app.terraform.io/api/v2/runs/${RUN_ID}/actions/apply
```

## Team and Access Management

### Team Configuration

**Workspace Permissions:**
- **Read**: View workspace settings and state
- **Plan**: Queue plans and view results
- **Write**: Apply runs
- **Admin**: Full workspace management

**Organization Permissions:**
- **Owners**: Full organization access
- **Manage Policies**: Create and edit Sentinel policies
- **Manage Workspaces**: Create and delete workspaces
- **Manage VCS Settings**: Configure VCS connections

### RBAC Best Practices

```
Organization: my-company
├── Team: platform-engineers (Admin on all workspaces)
├── Team: app-team-1 (Write on app-team-1-* workspaces)
├── Team: app-team-2 (Write on app-team-2-* workspaces)
├── Team: security (Read on all, Manage Policies)
└── Team: executives (Read on production workspaces)
```

## Workspace Organization Strategies

### Strategy 1: Environment-Based

```
Workspaces:
- aws-vpc-dev
- aws-vpc-staging
- aws-vpc-production
- aws-eks-dev
- aws-eks-staging
- aws-eks-production
```

**Pros:** Clear environment separation, easy RBAC
**Cons:** Workspace proliferation, harder to manage at scale

### Strategy 2: Component-Based with Workspaces

```
Workspaces (using workspace selection):
- aws-vpc (workspaces: dev, staging, prod)
- aws-eks (workspaces: dev, staging, prod)
```

**Terraform Code:**
```hcl
locals {
  environment = terraform.workspace
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidrs[local.environment]
  
  tags = {
    Environment = local.environment
  }
}
```

### Strategy 3: Project-Based (HCP Terraform)

```
Projects:
├── Networking
│   ├── vpc-production
│   ├── vpc-staging
│   └── transit-gateway
├── Applications
│   ├── app-prod
│   └── app-staging
└── Security
    ├── security-hub
    └── guard-duty
```

## State Management Best Practices

### State File Security

- Enable encryption at rest (enabled by default)
- Restrict access via team permissions
- Never commit state files to VCS
- Use remote state for team collaboration

### State Locking

- Automatic with Terraform Cloud
- Prevents concurrent modifications
- Manual unlock available if needed:
```bash
terraform force-unlock LOCK_ID
```

### State Versioning

- Every apply creates new state version
- Roll back to previous versions via UI
- Download historical state for recovery

## Notifications

Configure notifications for run events.

**Webhook Notification:**
```bash
curl \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  --data '{
    "data": {
      "type": "notification-configurations",
      "attributes": {
        "destination-type": "generic",
        "enabled": true,
        "name": "Slack Notifications",
        "url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
        "triggers": ["run:created", "run:planning", "run:needs_attention", "run:applying", "run:completed", "run:errored"]
      }
    }
  }' \
  https://app.terraform.io/api/v2/workspaces/ws-ID/notification-configurations
```

**Email Notification:**
- Configure via UI: Workspace Settings → Notifications
- Select events: run:completed, run:errored, run:needs_attention
- Add email addresses for team members

## Troubleshooting

**Issue: VCS connection fails**
- Verify OAuth token is valid
- Check repository permissions
- Confirm webhook is active in repository

**Issue: Dynamic credentials not working**
- Verify IAM role trust policy
- Check TFC_AWS_PROVIDER_AUTH environment variable
- Confirm role ARN is correct

**Issue: State lock timeout**
- Check for stuck runs in workspace
- Verify no manual terraform operations are running
- Force unlock if necessary

**Issue: Cost estimation missing**
- Ensure workspace has cost estimation enabled
- Verify resources are supported for cost estimation
- Check if provider versions are up to date
