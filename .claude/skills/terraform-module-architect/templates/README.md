# Terraform Module Templates

This directory contains template files for generating production-grade Terraform modules using the `/ipe_module` command.

## Template Structure

Each module type has its own directory containing:
- Core Terraform files (main.tf, variables.tf, outputs.tf, versions.tf)
- Documentation (README.md, CHANGELOG.md, LICENSE)
- Examples (examples/basic, examples/complete)
- Tests (tests/ with Terratest scaffolding)

## Available Module Types

### P0 (High Priority) - Implemented
- **custom** - Minimal scaffold for any resource (14 files)

### P0 (High Priority) - To Be Implemented
- **vpc** - Full VPC with subnets, NAT, IGW
- **ec2** - Compute instances with security groups
- **s3** - Storage buckets with encryption

### P1 (Medium Priority) - To Be Implemented
- **rds** - Database instances with backups
- **iam** - Roles and policies
- **eks** - Kubernetes clusters

### P2 (Lower Priority) - To Be Implemented
- **lambda** - Serverless functions
- **api-gateway** - REST/HTTP APIs

## Template Variables

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

## Creating New Module Templates

To add a new module type:

1. Create directory structure:
   ```bash
   mkdir -p templates/{module-type}/{examples/{basic,complete},tests}
   ```

2. Create template files:
   - `main.tf.template` - Resource definitions
   - `variables.tf.template` - Input variables with validation
   - `outputs.tf.template` - Output values
   - `versions.tf.template` - Provider version constraints
   - `README.md.template` - Documentation
   - `CHANGELOG.md.template` - Version history
   - `LICENSE.template` - License file
   - `examples/basic/main.tf.template` - Basic usage example
   - `examples/basic/README.md.template` - Basic example docs
   - `examples/complete/main.tf.template` - Complete usage example
   - `examples/complete/README.md.template` - Complete example docs
   - `tests/basic_test.go.template` - Terratest scaffolding
   - `tests/go.mod.template` - Go module definition
   - `tests/README.md.template` - Test documentation

3. Use placeholder syntax: `{{VARIABLE_NAME}}`

4. Follow best practices:
   - Include variable validation rules
   - Use common tagging strategy
   - Provide comprehensive documentation
   - Include working examples
   - Add test scaffolding

## Template Best Practices

### Resource Definitions (main.tf)
- Use `locals` for common values
- Apply `local.common_tags` to all resources
- Follow naming convention: `{name}-{environment}-{resource-type}`
- Include helpful comments

### Variables (variables.tf)
- Always include: name, environment, tags
- Add validation rules for all inputs
- Provide clear descriptions
- Set sensible defaults where appropriate

### Outputs (outputs.tf)
- Export resource IDs for module composition
- Group related outputs using objects
- Mark sensitive data with `sensitive = true`
- Provide clear descriptions

### Documentation (README.md)
- Include usage examples (basic and advanced)
- Document all inputs and outputs in tables
- List requirements and provider versions
- Explain what the module creates
- Provide testing instructions

### Examples
- Basic: Minimal working configuration
- Complete: All features demonstrated
- Use relative paths: `source = "../.."`
- Include output examples

### Tests
- Use Terratest for integration tests
- Always include cleanup (defer)
- Test in parallel when possible
- Include test documentation

## Testing Templates

Before using a new template:

1. Verify all placeholders are present
2. Check syntax validity (HCL, Markdown, Go)
3. Ensure examples are realistic
4. Test variable substitution manually

## Usage

Templates are used automatically by the `/ipe_module` command:

```bash
/ipe_module custom my-module dev
/ipe_module vpc app-vpc prod
/ipe_module ec2 web-server staging
```

The command will:
1. Load templates for the specified module type
2. Substitute all variables
3. Generate module files
4. Format with terraform fmt
5. Validate with terraform validate

## Reference

See `references/template_substitution.md` for detailed information on:
- Variable substitution algorithm
- Template syntax rules
- Error handling
- Implementation guidelines
