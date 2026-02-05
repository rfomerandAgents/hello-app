# Terraform Best Practices - Comprehensive Guide

This guide provides in-depth best practices for writing maintainable, secure, and performant Terraform code.

## Table of Contents

1. [Provider Configuration](#provider-configuration)
2. [Variable Design](#variable-design)
3. [Resource Patterns](#resource-patterns)
4. [Module Design](#module-design)
5. [State Management](#state-management)
6. [Output Design](#output-design)
7. [Data Sources](#data-sources)
8. [Terraform Settings](#terraform-settings)

---

## Provider Configuration

### Version Pinning

**Always pin provider versions** to prevent unexpected changes:

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Allow patch updates only
    }
  }
}
```

**Version constraint operators:**

- `= 1.0.0` - Exact version (too restrictive)
- `>= 1.0.0` - Greater than or equal (too permissive)
- `~> 1.0` - Pessimistic constraint: `>= 1.0, < 2.0` (recommended)
- `~> 1.0.0` - Pessimistic constraint: `>= 1.0.0, < 1.1.0` (recommended for stability)

### Provider Aliases

Use aliases for multi-region or multi-account deployments:

```hcl
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

resource "aws_instance" "east" {
  provider = aws
  # ... configuration ...
}

resource "aws_instance" "west" {
  provider = aws.west
  # ... configuration ...
}
```

### Provider Configuration Best Practices

```hcl
provider "aws" {
  region = var.aws_region

  # Default tags applied to all resources
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = var.repository_url
    }
  }

  # Retry logic for transient API errors
  retry_mode = "standard"
  max_retries = 3
}
```

---

## Variable Design

### Type Constraints

**Use specific types, not just `string`:**

```hcl
# Primitive types
variable "instance_count" {
  type    = number
  default = 1
}

variable "enable_monitoring" {
  type    = bool
  default = true
}

# Collection types
variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "tags" {
  type    = map(string)
  default = {}
}

# Object types
variable "instance_config" {
  type = object({
    type         = string
    ami          = string
    disk_size_gb = number
  })
}
```

### Validation Rules

**Always validate non-trivial inputs:**

```hcl
variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string

  validation {
    condition = can(regex("^t[3-4]\\.", var.instance_type)) ||
                can(regex("^c[5-7]\\.", var.instance_type))
    error_message = "Instance type must be t3/t4 or c5/c6/c7 family."
  }
}

variable "cidr_block" {
  description = "VPC CIDR block"
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block."
  }
}
```

### Sensitive Variables

**Mark sensitive data appropriately:**

```hcl
variable "database_password" {
  description = "Database master password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.database_password) >= 16
    error_message = "Password must be at least 16 characters."
  }
}

variable "api_key" {
  description = "API key for external service"
  type        = string
  sensitive   = true
}
```

### Variable Documentation

**Every variable should have a description:**

```hcl
variable "vpc_cidr" {
  description = <<-EOT
    CIDR block for the VPC. Should be a /16 network to allow for
    sufficient subnet allocation across multiple availability zones.
    Example: 10.0.0.0/16
  EOT
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}
```

### Default Values

**Provide sensible defaults where appropriate:**

```hcl
variable "enable_deletion_protection" {
  description = "Enable deletion protection for RDS instance"
  type        = bool
  default     = true  # Safe default
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 35
    error_message = "Backup retention must be between 1 and 35 days."
  }
}
```

---

## Resource Patterns

### Lifecycle Rules

**Use lifecycle blocks strategically:**

```hcl
# Prevent downtime during updates
resource "aws_security_group" "app" {
  name_prefix = "app-"
  # ... configuration ...

  lifecycle {
    create_before_destroy = true
  }
}

# Prevent accidental destruction
resource "aws_db_instance" "prod" {
  # ... configuration ...

  lifecycle {
    prevent_destroy = var.environment == "prod"
  }
}

# Ignore external changes
resource "aws_instance" "app" {
  # ... configuration ...

  lifecycle {
    ignore_changes = [
      ami,  # Managed through separate AMI update process
      user_data  # May be updated outside Terraform
    ]
  }
}

# Replace when specific attributes change
resource "aws_launch_template" "app" {
  # ... configuration ...

  lifecycle {
    create_before_destroy = true
    replace_triggered_by = [
      aws_security_group.app.id
    ]
  }
}
```

### Timeouts

**Define explicit timeouts for long-running operations:**

```hcl
resource "aws_db_instance" "main" {
  # ... configuration ...

  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}

resource "aws_ecs_service" "app" {
  # ... configuration ...

  timeouts {
    create = "20m"
    update = "20m"
    delete = "20m"
  }
}
```

### for_each vs count

**Prefer `for_each` over `count`:**

```hcl
# BAD - Using count makes addresses fragile
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  # If an AZ is removed from the middle of the list,
  # Terraform will destroy and recreate all subsequent subnets!
}

# GOOD - for_each creates stable resource addresses
resource "aws_subnet" "public" {
  for_each = toset(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, index(var.availability_zones, each.value))
  availability_zone = each.value

  tags = {
    Name = "${var.name_prefix}-public-${each.value}"
  }
}
```

### Resource Dependencies

**Make dependencies explicit when needed:**

```hcl
# Implicit dependency (preferred when possible)
resource "aws_instance" "app" {
  subnet_id = aws_subnet.public.id  # Terraform knows to create subnet first
}

# Explicit dependency (use when Terraform can't infer)
resource "aws_instance" "app" {
  # ... configuration ...

  depends_on = [
    aws_internet_gateway.main,  # Must exist before instance
    aws_route_table.public      # Routes must be configured
  ]
}
```

### Conditional Resources

**Use `count` for conditional creation:**

```hcl
resource "aws_eip" "app" {
  count = var.use_elastic_ip ? 1 : 0

  instance = aws_instance.app.id
  domain   = "vpc"
}

# Reference with conditional
locals {
  public_ip = var.use_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip
}
```

### Dynamic Blocks

**Use `dynamic` blocks for repeated nested blocks:**

```hcl
resource "aws_security_group" "app" {
  name_prefix = "app-"
  vpc_id      = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.allowed_ingress_rules

    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
}

# Variable definition
variable "allowed_ingress_rules" {
  description = "List of allowed ingress rules"
  type = list(object({
    port        = number
    cidr_blocks = list(string)
    description = string
  }))
  default = [
    {
      port        = 80
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTP from anywhere"
    },
    {
      port        = 443
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS from anywhere"
    }
  ]
}
```

---

## Module Design

### Module Structure

**Standard module structure:**

```
modules/vpc/
├── README.md          # Usage examples and documentation
├── main.tf            # Primary resource definitions
├── variables.tf       # Input variables
├── outputs.tf         # Output values
├── versions.tf        # Terraform and provider version constraints
├── locals.tf          # Local values (optional)
└── examples/
    └── complete/      # Complete example usage
        ├── main.tf
        └── outputs.tf
```

### versions.tf

**Always specify version constraints:**

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

### Module Variables

**Design stable, well-documented interfaces:**

```hcl
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "azs" {
  description = "Availability zones for subnet creation"
  type        = list(string)

  validation {
    condition     = length(var.azs) >= 2
    error_message = "At least 2 availability zones required for HA."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

### Module Outputs

**Export useful values for composition:**

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = [for s in aws_subnet.private : s.id]
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}
```

### Module README

**Document usage clearly:**

```markdown
# VPC Module

Creates a VPC with public and private subnets across multiple availability zones.

## Usage

```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr = "10.0.0.0/16"
  azs      = ["us-east-1a", "us-east-1b", "us-east-1c"]

  tags = {
    Environment = "production"
    Project     = "my-app"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| aws | >= 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| vpc_cidr | CIDR block for VPC | `string` | n/a | yes |
| azs | Availability zones | `list(string)` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | ID of the VPC |
| public_subnet_ids | Public subnet IDs |
```

---

## State Management

### Backend Configuration

**Always use remote state for teams:**

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "vpc/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"

    # Enable versioning on the bucket
    # Enable MFA delete in production
  }
}
```

### State Isolation Strategies

**1. Per-environment backends:**

```hcl
# environments/dev/backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "dev/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

# environments/prod/backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "prod/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}
```

**2. Component-based isolation:**

```hcl
# networking/backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "networking/terraform.tfstate"
  }
}

# compute/backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "compute/terraform.tfstate"
  }
}
```

### State Locking

**Enable state locking to prevent concurrent modifications:**

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"  # Must have LockID primary key
  }
}
```

### Remote State Data Sources

**Share data between state files:**

```hcl
# In networking component
output "vpc_id" {
  value = aws_vpc.main.id
}

# In compute component
data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "mycompany-terraform-state"
    key    = "networking/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  vpc_security_group_ids = [data.terraform_remote_state.networking.outputs.vpc_id]
}
```

---

## Output Design

### Output Documentation

```hcl
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

output "private_ip" {
  description = "Private IP address of the instance"
  value       = aws_instance.main.private_ip
}

output "db_connection_string" {
  description = "Database connection string (password not included)"
  value       = "postgresql://${aws_db_instance.main.username}@${aws_db_instance.main.endpoint}/mydb"
  sensitive   = true
}
```

### Sensitive Outputs

```hcl
output "db_password" {
  description = "Database master password"
  value       = random_password.db.result
  sensitive   = true
}

# Access with: terraform output -raw db_password
```

---

## Data Sources

### Efficient Data Source Usage

```hcl
# Get latest AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get current AWS account
data "aws_caller_identity" "current" {}

# Get available AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# Use in locals
locals {
  account_id = data.aws_caller_identity.current.account_id
  az_count   = min(length(data.aws_availability_zones.available.names), 3)
}
```

---

## Terraform Settings

### Required Terraform Version

```hcl
terraform {
  required_version = ">= 1.5.0"

  experiments = []  # Avoid experiments in production
}
```

### Cloud Integration

```hcl
terraform {
  cloud {
    organization = "mycompany"

    workspaces {
      name = "my-app-production"
    }
  }
}
```

---

## Advanced Patterns

### Locals for Complex Logic

```hcl
locals {
  # Naming convention
  name_prefix = "${var.project}-${var.environment}"

  # Common tags
  common_tags = merge(
    var.tags,
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  )

  # Computed subnet CIDRs
  public_subnet_cidrs = [
    for i in range(local.az_count) :
    cidrsubnet(var.vpc_cidr, 8, i)
  ]

  private_subnet_cidrs = [
    for i in range(local.az_count) :
    cidrsubnet(var.vpc_cidr, 8, i + 100)
  ]
}
```

### Conditional Logic

```hcl
locals {
  # Conditional instance type
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"

  # Conditional feature enablement
  monitoring_enabled = var.environment == "prod" ? true : var.enable_monitoring

  # Complex conditions
  use_multi_az = var.environment == "prod" && var.high_availability
}
```

---

## Summary

Following these best practices will result in:

- **Maintainable** code that's easy to understand and modify
- **Secure** infrastructure with proper isolation and encryption
- **Reliable** deployments with predictable behavior
- **Collaborative** workflows with proper state management
- **Documented** infrastructure that new team members can understand

Remember: The goal is not just working infrastructure, but infrastructure that can be safely modified, understood, and maintained over time.
