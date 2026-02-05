# IPE Module Generator

Generate production-grade Terraform modules with best practices.

## Description

Creates a complete Terraform module with all necessary files including:
- Resource definitions (main.tf)
- Input variables with validation (variables.tf)
- Output values (outputs.tf)
- Provider version constraints (versions.tf)
- Comprehensive documentation (README.md)
- Usage examples (examples/)
- Test scaffolding (tests/)

**NEW**: Supports extracting existing Terraform code into modules with the `--from-existing` option.

## Variables

type: $1
name: $2
environment: $3
path: $4
description: $5
provider: $6
version: $7

## Instructions

This command invokes the terraform-module-architect skill to generate a complete module.

### Mode 1: Template-Based Generation (Scaffolding)

Required arguments:
- `type`: Module type (custom, vpc, ec2, s3, rds, iam, eks, lambda, api-gateway)
- `name`: Module name in kebab-case (e.g., app-vpc, web-server)

Optional arguments:
- `environment`: Target environment (dev, staging, prod) [default: dev]
- `path`: Custom output path [default: io/terraform/modules/{name}]
- `description`: Module description [default: auto-generated]
- `provider`: Cloud provider (aws, azure, gcp) [default: aws]
- `version`: Terraform version constraint [default: >= 1.0]

Usage examples:

Generate a VPC module:
```
/ipe_module vpc app-vpc prod
```

Generate an EC2 module with custom path:
```
/ipe_module ec2 web-server prod io/terraform/custom/web-server
```

Generate a custom module with description:
```
/ipe_module custom my-resource dev "" "Custom resource module"
```

### Mode 2: Migration from Existing Code (NEW)

Required arguments:
- `--from-existing=FILE`: Path to existing Terraform file to extract from
- `--name=NAME`: Name for the new module (kebab-case)
- `--extract=CATEGORY`: Resource category to extract (vpc, ec2, s3, rds, iam, eks, lambda, api-gateway, security)

Optional arguments:
- `--path=PATH`: Output path for module [default: io/terraform/modules/NAME]
- `--preserve-state`: Generate state migration scripts
- `--dry-run`: Preview extraction without creating files
- `--resources=LIST`: Extract specific resources (comma-separated)

Usage examples:

Extract EC2 resources from existing infrastructure:
```
/ipe_module --from-existing=io/terraform/main.tf --extract=ec2 --name=web-servers
```

Extract with state migration support:
```
/ipe_module --from-existing=io/terraform/main.tf --extract=ec2 --name=web-servers --preserve-state
```

Dry run to preview extraction:
```
/ipe_module --from-existing=io/terraform/main.tf --extract=vpc --name=my-vpc --dry-run
```

Extract specific resources:
```
/ipe_module --from-existing=io/terraform/main.tf --resources=aws_instance.web,aws_security_group.web --name=web-module
```

## Run

Invoke the terraform-module-architect skill with module generation capabilities.

### Template-Based Generation Workflow:
1. Validate all arguments
2. Select appropriate templates
3. Perform variable substitution
4. Create directory structure
5. Generate all module files
6. Run terraform fmt for formatting
7. Run terraform validate for syntax checking
8. Display summary and next steps

### Migration-Based Generation Workflow:
1. Parse existing Terraform file using HCL parser
2. Extract specified resources with dependencies
3. Infer variables from hardcoded values
4. Generate outputs based on resource types
5. Create module directory structure
6. Generate main.tf, variables.tf, outputs.tf, versions.tf
7. Generate README.md and examples
8. (Optional) Generate state migration scripts if --preserve-state is used
9. Display extraction summary and next steps

## Report

The skill will display:
- Module creation status
- File location
- List of generated files
- For migrations: extraction summary (primary resources, related resources, inferred variables, outputs)
- Validation results (template mode only)
- Next steps for customization or state migration
