---
name: terraform-module-architect
description: Expert infrastructure engineering skill for designing, building, and maintaining production-grade Terraform modules. Use when creating reusable Terraform modules, designing module interfaces, structuring module repositories, implementing module best practices, composing complex infrastructure patterns, or refactoring code into modules. Includes module scaffolding, testing patterns, documentation standards, and common infrastructure module templates.
---

# Terraform Module Architect

## Overview

This skill provides expert guidance for designing and building production-grade Terraform modules with enterprise best practices, reusability patterns, and maintainability standards.

## Module Design Philosophy

### Core Principles

1. **Single Responsibility** - Each module manages one logical infrastructure component
2. **Composability** - Modules combine to build complex infrastructure
3. **Flexibility** - Support multiple use cases without becoming overly complex
4. **Sensible Defaults** - Work out-of-the-box with minimal configuration
5. **Clear Contracts** - Well-defined inputs and outputs
6. **Self-Documenting** - Clear variable descriptions and examples

## Module Scaffolding

Use the scaffolding script to generate new module structure:

```bash
python scripts/scaffold_module.py <module-name> [--type vpc|compute|database|generic]
```

This creates a complete module structure with:
- Standard file organization
- Template variables and outputs
- Example usage
- Testing structure
- Documentation templates

## Migration Assistant (NEW - Phase 13)

Extract existing Terraform code into reusable modules with automatic dependency detection, variable inference, and state migration support.

### When to Use Migration vs Scaffolding

**Use Migration Assistant when:**
- You have existing Terraform code to modularize
- You want to extract specific resources from monolithic files
- You need to maintain existing infrastructure state
- You want automatic variable detection from hardcoded values

**Use Scaffolding when:**
- Starting a new module from scratch
- Following standard templates for common patterns
- Building greenfield infrastructure
- Learning module best practices

### Migration Features

1. **HCL Parsing** - Parse existing .tf files with full syntax support
2. **Smart Extraction** - Extract resources by type/category with automatic dependency detection
3. **Variable Inference** - Detect hardcoded values and generate sensible variables
4. **Output Generation** - Create useful outputs based on resource types
5. **State Migration** - Generate safe state migration scripts with rollback support
6. **Dry-Run Mode** - Preview extraction before making changes

### Migration Usage

```bash
# Extract EC2 resources
python scripts/migrate_module.py --from-existing=io/terraform/main.tf --extract=ec2 --name=web-servers

# Extract with state migration
python scripts/migrate_module.py --from-existing=io/terraform/main.tf --extract=ec2 --name=web-servers --preserve-state

# Preview extraction (dry run)
python scripts/migrate_module.py --from-existing=io/terraform/main.tf --extract=vpc --name=my-vpc --dry-run

# Extract specific resources
python scripts/migrate_module.py --from-existing=io/terraform/main.tf --resources=aws_instance.web,aws_security_group.web --name=web-module
```

### Resource Categories Supported

The migration assistant understands these resource categories:
- **vpc** - VPCs, subnets, gateways, route tables
- **ec2** - Instances, launch templates, autoscaling groups, security groups
- **s3** - Buckets and bucket configurations
- **rds** - Database instances and configurations
- **iam** - Roles, policies, instance profiles
- **security** - Security groups, key pairs, network ACLs
- **eks** - EKS clusters and node groups
- **lambda** - Lambda functions and configurations
- **api-gateway** - API Gateway resources

### State Migration Workflow

When using `--preserve-state`, the migration assistant generates:

1. **migrate_state.sh** - Safe migration script with confirmation prompts
2. **rollback_state.sh** - Rollback script to undo migration
3. **MIGRATION.md** - Complete migration guide with troubleshooting

**Migration steps:**
```bash
# 1. Generate module with state migration scripts
python scripts/migrate_module.py --from-existing=io/terraform/main.tf --extract=ec2 --name=web --preserve-state

# 2. Review generated module
cd io/terraform/modules/web

# 3. Update root module to use new module
# Add to your main.tf:
module "web" {
  source = "./io/terraform/modules/web"
  # ... configure variables
}

# 4. Run migration script
./migrate_state.sh

# 5. Verify (should show no changes)
terraform plan
```

### Variable Inference Patterns

The migration assistant automatically detects and converts:

| Hardcoded Value | Inferred Variable | Validation |
|-----------------|-------------------|------------|
| `"t3.micro"` | `var.instance_type` | Instance type format |
| `"10.0.0.0/16"` | `var.cidr_block` | Valid CIDR |
| `80`, `443` | `var.http_port`, `var.https_port` | Port range |
| `"ami-..."` | `var.ami_id` | AMI ID format |
| `"prod"`, `"staging"` | `var.environment` | Allowed values |

### Troubleshooting

**Parser fails on complex HCL:**
- The parser uses simple regex for most cases
- For complex expressions, it may miss some attributes
- Review and manually adjust generated module if needed

**Missing dependencies:**
- The dependency detection is automatic but may miss implicit dependencies
- Review the generated main.tf and add missing resources manually

**State migration shows changes after migration:**
- Check that module variable values match original hardcoded values
- Ensure all resources were extracted (check for missing dependencies)
- Review the terraform plan diff carefully

## Automated Module Generation

This skill provides automated module generation capabilities invoked via the `/ipe_module` command.

### Generation Process

When invoked with module parameters, this skill will:

#### 1. Argument Validation
- Validate module type is supported
- Validate name follows kebab-case convention (^[a-z0-9-]+$)
- Validate environment if provided (dev, staging, prod)
- Set defaults for optional parameters

#### 2. Variable Preparation
Create substitution map:
```python
variables = {
    'MODULE_NAME': name,                              # e.g., "app-vpc"
    'MODULE_NAME_UNDERSCORED': name.replace('-', '_'), # e.g., "app_vpc"
    'MODULE_TYPE': module_type,                       # e.g., "vpc"
    'ENVIRONMENT': environment or 'dev',
    'DESCRIPTION': description or f'{module_type.upper()} module',
    'AUTHOR': git config user.name,
    'DATE': datetime.now().isoformat(),
    'TERRAFORM_VERSION': version or '>= 1.0',
    'PROVIDER': provider or 'aws',
}
```

#### 3. Template Loading
- Determine template directory: `.claude/skills/terraform-module-architect/templates/{module_type}/`
- Recursively scan for all `.template` files
- Read each template file content
- Store template path and content

#### 4. Variable Substitution
For each template file:
- Replace all `{{PLACEHOLDER}}` with actual values
- Use simple string replacement (no regex needed)
- Example: `{{MODULE_NAME}}` → `app-vpc`

#### 5. Directory Creation
- Output path: `{path}` or `io/terraform/modules/{name}`
- Create directory structure:
  - Main directory
  - `examples/basic/`
  - `examples/complete/`
  - `tests/`
- Use: `os.makedirs(path, exist_ok=True)`

#### 6. File Writing
- For each rendered template:
  - Determine output path (remove `.template` extension)
  - Write rendered content to file
  - Set file permissions (644 for regular files, 755 for scripts)

#### 7. Formatting
- Run: `terraform fmt -recursive {output_path}`
- Capture output and errors
- Display formatting results

#### 8. Validation
- Run: `cd {output_path} && terraform init -backend=false && terraform validate`
- Capture output and errors
- Display validation results

#### 9. Summary Generation
Display:
```
Module '{name}' created successfully!

Location: {output_path}

Generated Files:
  - main.tf (resource definitions)
  - variables.tf (N variables with validation)
  - outputs.tf (M outputs)
  - versions.tf (Terraform >= 1.0, AWS ~> 5.0)
  - README.md (comprehensive documentation)
  - examples/basic/ (working example)
  - tests/basic_test.go (Terratest scaffolding)

Next Steps:
1. Review generated files: cd {output_path}
2. Customize variables and resources as needed
3. Update README with specific usage details
4. Test with example: cd examples/basic && terraform init
5. Run tests: cd tests && go test -v
6. Commit to version control

Documentation: {output_path}/README.md
```

### Supported Module Types

| Type | Description | Files Generated | Priority |
|------|-------------|-----------------|----------|
| custom | Minimal scaffold for any resource | 5 files | P0 |
| vpc | Full VPC with subnets, NAT, IGW | 12+ files | P0 |
| ec2 | Compute instances with security groups | 8 files | P0 |
| s3 | Storage buckets with encryption | 7 files | P0 |
| rds | Database instances with backups | 9 files | P1 |
| iam | Roles and policies | 6 files | P1 |
| eks | Kubernetes clusters | 15+ files | P1 |
| lambda | Serverless functions | 8 files | P2 |
| api-gateway | REST/HTTP APIs | 10 files | P2 |

### Template Variable Reference

All templates support these substitution variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{MODULE_NAME}}` | Module name (kebab-case) | `app-vpc` |
| `{{MODULE_NAME_UNDERSCORED}}` | Module name (snake_case) | `app_vpc` |
| `{{MODULE_TYPE}}` | Type of module | `vpc` |
| `{{ENVIRONMENT}}` | Target environment | `prod` |
| `{{DESCRIPTION}}` | Module description | `VPC module for app` |
| `{{AUTHOR}}` | Git user name | `John Doe` |
| `{{DATE}}` | Current ISO 8601 date | `2025-11-17T15:30:00Z` |
| `{{TERRAFORM_VERSION}}` | Version constraint | `>= 1.0` |
| `{{PROVIDER}}` | Cloud provider | `aws` |

### Best Practices Enforced

Generated modules automatically include:

1. **Validation Rules**
   - Variable validation for environments
   - CIDR block validation
   - Port range validation
   - String format validation

2. **Security Defaults**
   - Encryption enabled by default
   - Private subnets for databases
   - Security group restrictions
   - IAM least privilege

3. **Tagging Strategy**
   - Name tag with consistent format
   - Environment tag
   - ManagedBy = "Terraform"
   - Module tag with module name

4. **Documentation**
   - Complete README with usage examples
   - Variable and output tables
   - Requirements section
   - Cost considerations

5. **Testing Infrastructure**
   - Terratest scaffolding
   - Example configurations
   - Validation commands

### Error Handling

The skill will handle these errors gracefully:

| Error | Cause | Resolution |
|-------|-------|------------|
| Invalid module type | Type not in supported list | Display supported types, exit |
| Invalid name format | Name contains uppercase/spaces | Show naming rules, exit |
| Template not found | Missing template directory | Create minimal template, warn |
| Terraform fmt fails | Syntax errors in templates | Show errors, continue anyway |
| Terraform validate fails | Invalid HCL | Show errors, manual fix needed |
| Directory exists | Module already created | Prompt to overwrite or rename |

### Invocation Examples

Via slash command:
```
/ipe_module vpc app-vpc prod
/ipe_module ec2 web-server staging
/ipe_module s3 data-bucket
```

The skill receives these parameters and orchestrates the entire generation process.

## Standard Module Structure

```
terraform-module-name/
├── main.tf              # Primary resource definitions
├── variables.tf         # Input variable declarations
├── outputs.tf           # Output value declarations
├── versions.tf          # Provider and Terraform version constraints
├── README.md            # Module documentation
├── CHANGELOG.md         # Version history
├── LICENSE              # License file
├── examples/            # Usage examples
│   ├── basic/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── complete/
│   │   └── ...
│   └── minimal/
│       └── ...
├── tests/               # Automated tests
│   ├── unit/
│   └── integration/
└── modules/             # Submodules (if needed)
    └── submodule-name/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Variable Design Patterns

### Basic Variable Structure

```hcl
# variables.tf
variable "name" {
  description = "Name of the resource (used in tags and resource naming)"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

### Complex Variable Patterns

See `references/variable_patterns.md` for comprehensive patterns including:
- Object types for complex configurations
- Dynamic block patterns
- Conditional resource creation
- Feature flags
- Validation rules

## Output Design Patterns

### Standard Output Structure

```hcl
# outputs.tf
output "id" {
  description = "The ID of the created resource"
  value       = aws_resource.main.id
}

output "arn" {
  description = "The ARN of the created resource"
  value       = aws_resource.main.arn
}

output "connection_info" {
  description = "Connection information for the resource"
  value = {
    endpoint = aws_resource.main.endpoint
    port     = aws_resource.main.port
    address  = aws_resource.main.address
  }
}

output "security_group_id" {
  description = "ID of the security group for additional rule attachment"
  value       = aws_security_group.main.id
}
```

### Output Best Practices

1. **Return IDs for dependencies** - Enable module composition
2. **Group related outputs** - Use objects for logical grouping
3. **Mark sensitive data** - Use `sensitive = true` for secrets
4. **Provide connection info** - Help users integrate the resource
5. **Enable customization** - Return resource IDs for further configuration

## Module Composition

### Parent-Child Pattern

```hcl
# High-level application module
module "app" {
  source = "./modules/application"
  
  name        = "myapp"
  environment = "production"
  
  # Use outputs from infrastructure modules
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  database_endpoint = module.database.endpoint
}

module "vpc" {
  source = "./modules/vpc"
  
  name        = "myapp"
  environment = "production"
  cidr_block  = "10.0.0.0/16"
}

module "database" {
  source = "./modules/rds"
  
  name               = "myapp"
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.database_subnet_ids
  security_group_ids = [module.vpc.database_security_group_id]
}
```

### Submodule Pattern

Use for related resources that are always deployed together:

```
modules/vpc/
├── main.tf              # VPC resource
├── modules/
│   ├── subnets/         # Subnet submodule
│   ├── nat-gateway/     # NAT gateway submodule
│   └── endpoints/       # VPC endpoint submodule
```

## Common Module Patterns

See comprehensive module templates in `references/`:
- `module_vpc.md` - VPC with subnets, NAT, and routing
- `module_compute.md` - EC2, ASG, Launch Templates
- `module_database.md` - RDS with replicas and backups
- `module_s3.md` - S3 buckets with policies and lifecycle
- `module_iam.md` - IAM roles and policies
- `module_security_group.md` - Security groups with rules

## Resource Naming Conventions

```hcl
# Local values for consistent naming
locals {
  # Base name for all resources
  name_prefix = "${var.name}-${var.environment}"
  
  # Common tags applied to all resources
  common_tags = merge(
    var.tags,
    {
      Name        = local.name_prefix
      Environment = var.environment
      ManagedBy   = "Terraform"
      Module      = "vpc"
    }
  )
}

# Resource naming pattern
resource "aws_vpc" "main" {
  cidr_block = var.cidr_block
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-vpc"
    }
  )
}
```

## Module Versioning

### Semantic Versioning

Follow semver (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version Constraints in versions.tf

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0, < 6.0"
    }
  }
}
```

### Git Tagging

```bash
# Tag a new version
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# Use specific version in module source
module "vpc" {
  source = "git::https://github.com/org/terraform-aws-vpc.git?ref=v1.2.0"
  # ...
}
```

## Module Documentation

### README Template

```markdown
# Terraform AWS VPC Module

Brief description of what this module creates.

## Usage

```hcl
module "vpc" {
  source = "github.com/org/terraform-aws-vpc"
  
  name        = "myapp"
  environment = "production"
  cidr_block  = "10.0.0.0/16"
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | >= 5.0 |

## Providers

| Name | Version |
|------|---------|
| aws | >= 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | Name prefix for resources | `string` | n/a | yes |
| cidr_block | CIDR block for VPC | `string` | `"10.0.0.0/16"` | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | The ID of the VPC |
| private_subnet_ids | List of private subnet IDs |

## Examples

- [Basic](./examples/basic) - Basic VPC setup
- [Complete](./examples/complete) - Full-featured VPC with all options

## License

Apache 2.0
```

### Auto-generating Documentation

```bash
# Use terraform-docs
terraform-docs markdown table . > README.md

# Or use the included script
python scripts/generate_docs.py ./modules/vpc
```

## Testing Strategies

### Unit Testing with Terratest

```go
// tests/unit/vpc_test.go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../../examples/basic",
    }
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcID)
}
```

### Validation Testing

```bash
# Validate module
terraform init
terraform validate

# Check formatting
terraform fmt -check -recursive

# Static analysis
tfsec .
checkov -d .
```

See `references/testing_patterns.md` for comprehensive testing strategies.

## Advanced Patterns

### Conditional Resource Creation

```hcl
# variables.tf
variable "create_nat_gateway" {
  description = "Whether to create NAT Gateway"
  type        = bool
  default     = true
}

variable "nat_gateway_count" {
  description = "Number of NAT Gateways (0 to disable)"
  type        = number
  default     = 1
  
  validation {
    condition     = var.nat_gateway_count >= 0
    error_message = "NAT gateway count must be 0 or greater."
  }
}

# main.tf
resource "aws_nat_gateway" "main" {
  count = var.create_nat_gateway ? var.nat_gateway_count : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-nat-${count.index + 1}"
    }
  )
}
```

### Dynamic Blocks

```hcl
# Create security group with dynamic rules
resource "aws_security_group" "main" {
  name   = "${local.name_prefix}-sg"
  vpc_id = aws_vpc.main.id
  
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
  
  tags = local.common_tags
}

# variables.tf
variable "ingress_rules" {
  description = "List of ingress rules"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  default = []
}
```

### For_each with Maps

```hcl
# Create multiple subnets from map
variable "subnets" {
  description = "Map of subnet configurations"
  type = map(object({
    cidr_block        = string
    availability_zone = string
    public           = bool
  }))
}

resource "aws_subnet" "main" {
  for_each = var.subnets
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.availability_zone
  
  map_public_ip_on_launch = each.value.public
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-${each.key}"
      Type = each.value.public ? "public" : "private"
    }
  )
}

# Usage
module "vpc" {
  source = "./modules/vpc"
  
  subnets = {
    public-1a = {
      cidr_block        = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      public           = true
    }
    private-1a = {
      cidr_block        = "10.0.10.0/24"
      availability_zone = "us-east-1a"
      public           = false
    }
  }
}
```

## Data Source Patterns

```hcl
# Get latest AMI
data "aws_ami" "latest" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  
  filter {
    name   = "state"
    values = ["available"]
  }
}

# Get availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Use in resource
resource "aws_subnet" "private" {
  count = length(data.aws_availability_zones.available.names)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}
```

## Module Best Practices

### 1. Start Simple, Add Complexity Gradually

```hcl
# Version 1.0 - Basic functionality
resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name
  tags   = var.tags
}

# Version 1.1 - Add versioning option
resource "aws_s3_bucket_versioning" "main" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.main.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Version 1.2 - Add lifecycle rules option
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.main.id
  
  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status
      # ...
    }
  }
}
```

### 2. Provide Multiple Examples

- `examples/minimal/` - Bare minimum configuration
- `examples/basic/` - Common use case
- `examples/complete/` - All features enabled
- `examples/custom/` - Specific scenarios

### 3. Use Feature Flags Over Multiple Modules

```hcl
# Better: Single module with feature flags
module "vpc" {
  source = "./modules/vpc"
  
  enable_nat_gateway    = true
  enable_vpn_gateway    = false
  enable_dns_hostnames  = true
  enable_flow_logs      = true
}

# Avoid: Multiple similar modules
# module "vpc_with_nat"
# module "vpc_without_nat"
# module "vpc_with_vpn"
```

### 4. Return Resource Objects

```hcl
# Return entire resource for flexibility
output "vpc" {
  description = "VPC resource with all attributes"
  value       = aws_vpc.main
}

# Users can access any attribute
vpc_id      = module.vpc.vpc.id
cidr_block  = module.vpc.vpc.cidr_block
arn         = module.vpc.vpc.arn
```

### 5. Validate Inputs

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  
  validation {
    condition     = can(regex("^t[23]\\.", var.instance_type))
    error_message = "Instance type must be t2 or t3 family."
  }
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  
  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be valid IPv4 CIDR."
  }
}
```

## Publishing Modules

### Terraform Registry

```hcl
# Module naming convention
terraform-<PROVIDER>-<NAME>

# Examples:
terraform-aws-vpc
terraform-azurerm-aks
terraform-google-gke
```

### Private Registry

```hcl
# Using GitHub
module "vpc" {
  source = "github.com/myorg/terraform-aws-vpc?ref=v1.0.0"
}

# Using GitLab
module "vpc" {
  source = "git::https://gitlab.com/myorg/terraform-aws-vpc.git?ref=v1.0.0"
}

# Using Terraform Cloud
module "vpc" {
  source  = "app.terraform.io/myorg/vpc/aws"
  version = "1.0.0"
}
```

## Module Development Workflow

1. **Design** - Define module scope and interface
2. **Scaffold** - Use scaffolding script
3. **Implement** - Write resources, variables, outputs
4. **Example** - Create usage examples
5. **Test** - Validate and test locally
6. **Document** - Generate comprehensive README
7. **Version** - Tag release with semver
8. **Publish** - Push to registry/repository
9. **Iterate** - Collect feedback and improve

## Quick Start

Generate a new module:

```bash
# Generate VPC module
python scripts/scaffold_module.py my-vpc --type vpc

# Generate compute module
python scripts/scaffold_module.py my-ec2 --type compute

# Generate generic module
python scripts/scaffold_module.py my-module
```

## Resources

### Scripts
- `scaffold_module.py` - Generate module structure
- `generate_docs.py` - Auto-generate documentation
- `validate_module.py` - Run validation checks

### References
- `variable_patterns.md` - Comprehensive variable design patterns
- `testing_patterns.md` - Testing strategies and examples
- `module_vpc.md` - Complete VPC module template
- `module_compute.md` - Compute resources module template
- `module_database.md` - Database module template
- `module_s3.md` - S3 bucket module template
- `module_iam.md` - IAM resources module template
- `module_security_group.md` - Security group module template

### Templates
- Module scaffolding templates
- Example configurations
- Testing templates
- Documentation templates
