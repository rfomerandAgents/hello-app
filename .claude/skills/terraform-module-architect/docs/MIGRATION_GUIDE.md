# Migration Assistant Guide

Complete guide for extracting existing Terraform code into reusable modules.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [Usage Examples](#usage-examples)
5. [Resource Categories](#resource-categories)
6. [Variable Inference](#variable-inference)
7. [State Migration](#state-migration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Overview

The Migration Assistant helps you refactor monolithic Terraform configurations into reusable modules. It automatically:

- Parses existing .tf files
- Extracts specific resources with their dependencies
- Infers sensible variables from hardcoded values
- Generates useful outputs based on resource types
- Creates state migration scripts (optional)

### When to Use

**Good candidates for extraction:**
- Repeated resource patterns (multiple VPCs, EC2 instances, etc.)
- Logically grouped resources (networking, compute, storage)
- Resources you want to reuse across environments
- Infrastructure you're planning to version independently

**Not recommended for:**
- Single-use resources with no reuse potential
- Resources with complex, unique configurations
- Infrastructure still in active development/prototyping

## Quick Start

### Basic Extraction

Extract EC2 resources from existing infrastructure:

```bash
cd /path/to/terraform-module-architect

python scripts/migrate_module.py \
  --from-existing=../../io/terraform/main.tf \
  --extract=ec2 \
  --name=web-servers
```

This creates: `io/terraform/modules/web-servers/`

### Preview Before Extracting (Dry Run)

See what would be extracted without creating files:

```bash
python scripts/migrate_module.py \
  --from-existing=../../io/terraform/main.tf \
  --extract=ec2 \
  --name=web-servers \
  --dry-run
```

### Extract with State Migration

Generate scripts to safely migrate Terraform state:

```bash
python scripts/migrate_module.py \
  --from-existing=../../io/terraform/main.tf \
  --extract=ec2 \
  --name=web-servers \
  --preserve-state
```

## How It Works

### 1. Parsing Phase

The HCL parser reads your Terraform file and builds an abstract syntax tree (AST):

```python
# Parses all block types
- resources (aws_instance, aws_vpc, etc.)
- data sources
- variables
- outputs
- locals
- modules
```

### 2. Extraction Phase

The resource extractor:
1. Finds resources matching your category (e.g., "ec2")
2. Builds a dependency graph
3. Automatically includes related resources
4. Extracts referenced data sources
5. Includes necessary local values

**Example:**
```hcl
# You extract: aws_instance.web
# Automatically includes:
- aws_security_group.web (referenced)
- aws_key_pair.web (referenced)
- data.aws_ami.latest (data source)
- local.common_tags (local value)
```

### 3. Variable Inference Phase

Detects hardcoded values and generates variables:

```hcl
# Original
instance_type = "t3.micro"
cidr_block = "10.0.0.0/16"

# Generated variable
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^[a-z][0-9]\\.", var.instance_type))
    error_message = "Instance type must be valid AWS instance type."
  }
}
```

### 4. Output Generation Phase

Creates useful outputs based on resource types:

```hcl
# For aws_instance
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.web.id
}

output "public_ip" {
  description = "Public IP address"
  value       = aws_instance.web.public_ip
}
```

### 5. Module Creation Phase

Generates complete module structure:

```
io/terraform/modules/web-servers/
├── main.tf              # Extracted resources
├── variables.tf         # Inferred variables
├── outputs.tf           # Generated outputs
├── versions.tf          # Provider requirements
├── README.md            # Documentation
└── examples/
    └── basic/
        └── main.tf      # Usage example
```

### 6. State Migration (Optional)

If `--preserve-state` is used, generates:

```
├── migrate_state.sh     # Migration script
├── rollback_state.sh    # Rollback script
└── MIGRATION.md         # Migration guide
```

## Usage Examples

### Extract VPC Resources

```bash
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --extract=vpc \
  --name=app-network \
  --preserve-state
```

**Extracts:**
- aws_vpc
- aws_subnet (all subnets)
- aws_internet_gateway
- aws_nat_gateway
- aws_route_table (all route tables)
- Related EIPs, route table associations

### Extract Specific Resources

```bash
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --resources=aws_instance.web,aws_security_group.web,aws_key_pair.web \
  --name=web-server
```

### Extract to Custom Path

```bash
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --extract=s3 \
  --name=data-buckets \
  --path=infrastructure/modules
```

Creates: `infrastructure/modules/data-buckets/`

### Multiple Extractions

Extract different resource types into separate modules:

```bash
# Network module
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --extract=vpc \
  --name=network

# Compute module
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --extract=ec2 \
  --name=compute

# Storage module
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --extract=s3 \
  --name=storage
```

## Resource Categories

### VPC (--extract=vpc)

Includes:
- aws_vpc
- aws_subnet
- aws_internet_gateway
- aws_nat_gateway
- aws_eip (for NAT)
- aws_route_table
- aws_route_table_association
- aws_network_acl
- aws_vpc_endpoint

### EC2 (--extract=ec2)

Includes:
- aws_instance
- aws_launch_template
- aws_autoscaling_group
- aws_security_group
- aws_key_pair
- aws_eip
- aws_network_interface

### S3 (--extract=s3)

Includes:
- aws_s3_bucket
- aws_s3_bucket_policy
- aws_s3_bucket_versioning
- aws_s3_bucket_encryption
- aws_s3_bucket_lifecycle_configuration

### RDS (--extract=rds)

Includes:
- aws_db_instance
- aws_db_subnet_group
- aws_db_parameter_group
- aws_rds_cluster

### IAM (--extract=iam)

Includes:
- aws_iam_role
- aws_iam_policy
- aws_iam_role_policy_attachment
- aws_iam_instance_profile

### Security (--extract=security)

Includes:
- aws_security_group
- aws_security_group_rule
- aws_network_acl
- aws_key_pair

### EKS (--extract=eks)

Includes:
- aws_eks_cluster
- aws_eks_node_group
- aws_eks_addon
- Related IAM roles

### Lambda (--extract=lambda)

Includes:
- aws_lambda_function
- aws_lambda_permission
- aws_lambda_layer_version
- Related IAM roles

## Variable Inference

### Automatic Patterns

| Hardcoded Value | Variable Name | Type | Validation |
|----------------|---------------|------|------------|
| `"t3.micro"` | `instance_type` | string | Instance type format |
| `"10.0.0.0/16"` | `cidr_block` | string | Valid CIDR |
| `80` | `http_port` | number | Port range (0-65535) |
| `443` | `https_port` | number | Port range (0-65535) |
| `"ami-abc123"` | `ami_id` | string | AMI ID format |
| `"prod"` | `environment` | string | Allowed values |

### Common Variables

Always added:
- `name` - Resource name prefix
- `environment` - Environment name
- `tags` - Additional tags (map)

### Manual Customization

After generation, review variables.tf and:
1. Adjust descriptions
2. Modify default values
3. Add/remove validation rules
4. Change variable types if needed

## State Migration

### Overview

State migration moves resources from root module to new module without destroying/recreating them.

### Process

1. **Generate module with migration scripts:**

```bash
python scripts/migrate_module.py \
  --from-existing=io/terraform/main.tf \
  --extract=ec2 \
  --name=web \
  --preserve-state
```

2. **Review generated module:**

```bash
cd io/terraform/modules/web
cat main.tf variables.tf outputs.tf
```

3. **Update root module to use new module:**

```hcl
# io/terraform/main.tf
module "web" {
  source = "./modules/web"

  instance_type = "t3.micro"
  name          = "myapp"
  environment   = "prod"
}
```

4. **Review migration script:**

```bash
cat migrate_state.sh
```

5. **Run migration:**

```bash
# Creates automatic backup
./migrate_state.sh
```

6. **Verify no changes:**

```bash
cd ../../..
terraform plan
# Should show: No changes. Your infrastructure matches the configuration.
```

### Rollback

If something goes wrong:

```bash
# Option 1: Use rollback script
cd io/terraform/modules/web
./rollback_state.sh

# Option 2: Restore from backup
terraform state push state_backup_YYYYMMDD_HHMMSS.tfstate
```

### Safety Features

The migration script includes:
- Confirmation prompt
- Automatic state backup
- Error handling
- Rollback instructions

## Troubleshooting

### Parser Issues

**Problem:** Parser fails on complex HCL syntax

**Solution:**
- The parser uses simplified regex patterns
- Manually review and adjust generated code
- For complex expressions, consider manual extraction

### Missing Dependencies

**Problem:** Some resources are missing from extraction

**Solution:**
- Dependencies are detected automatically from references
- Check for implicit dependencies (not visible in code)
- Manually add missing resources to main.tf

### State Migration Shows Changes

**Problem:** `terraform plan` shows changes after migration

**Causes & Solutions:**

1. **Variable values don't match hardcoded values**
   - Ensure module variables match original values exactly
   - Check data types (string vs number)

2. **Missing resources**
   - Review dependency graph
   - Add missing resources to module

3. **Attribute differences**
   - Compare old and new resource definitions
   - Ensure all attributes are included

### Validation Errors

**Problem:** Generated module fails `terraform validate`

**Solution:**
- Review error messages
- Check syntax in main.tf
- Adjust variable references
- Test with `terraform fmt -check`

## Best Practices

### Before Extraction

1. **Commit current state**
   ```bash
   git commit -am "Before module extraction"
   ```

2. **Backup state**
   ```bash
   terraform state pull > backup.tfstate
   ```

3. **Review resources**
   - Identify resource groups
   - Plan module boundaries
   - Consider dependencies

### During Extraction

1. **Start with dry-run**
   ```bash
   --dry-run
   ```

2. **Extract one category at a time**
   - Don't extract everything at once
   - Test each module independently

3. **Review generated code**
   - Check variable names
   - Verify output values
   - Ensure dependencies are correct

### After Extraction

1. **Test the module**
   ```bash
   cd examples/basic
   terraform init
   terraform plan
   ```

2. **Verify state migration**
   ```bash
   terraform plan  # Should show no changes
   ```

3. **Document module usage**
   - Update README.md
   - Add examples
   - Document prerequisites

### Module Design

1. **Keep modules focused**
   - Single responsibility
   - Clear boundaries
   - Minimal dependencies

2. **Use sensible defaults**
   - Common use cases work out-of-box
   - Advanced features are opt-in

3. **Provide examples**
   - Basic usage
   - Advanced configurations
   - Multiple environments

## Advanced Usage

### Custom Extraction Logic

For complex scenarios, use the Python API directly:

```python
from parsers import HCLParser, ResourceExtractor, VariableInferrer

# Parse file
parser = HCLParser()
parsed = parser.parse_file("main.tf")

# Extract specific resources
extractor = ResourceExtractor()
result = extractor.extract_by_resource_name(
    parsed,
    ["aws_instance.web", "aws_instance.app"]
)

# Infer variables
inferrer = VariableInferrer()
variables = inferrer.infer_variables(result)
```

### Batch Processing

Extract multiple modules programmatically:

```bash
# Script to extract all resource types
for category in vpc ec2 s3 rds iam; do
  python scripts/migrate_module.py \
    --from-existing=io/terraform/main.tf \
    --extract=$category \
    --name=$category-module
done
```

## Support

For issues or questions:
1. Check this guide
2. Review generated MIGRATION.md
3. Test with `--dry-run` first
4. Examine parser output for errors

## Version History

- **v1.0.0** (2025-01-17) - Initial release
  - HCL parsing
  - Resource extraction
  - Variable inference
  - Output generation
  - State migration
