# Template Variable Substitution

Reference guide for implementing variable substitution in Terraform module generation.

## Overview

Templates use placeholder syntax `{{VARIABLE_NAME}}` which gets replaced with actual values during generation.

## Substitution Algorithm

### 1. Variable Preparation

```python
def prepare_variables(name, module_type, environment, description, provider, version):
    """Prepare substitution variables from user input"""

    # Get git user info
    author = subprocess.run(
        ['git', 'config', 'user.name'],
        capture_output=True,
        text=True
    ).stdout.strip() or 'Platform Engineering Team'

    # Get current date in ISO 8601
    date = datetime.now().isoformat()

    # Prepare all variables
    variables = {
        'MODULE_NAME': name,
        'MODULE_NAME_UNDERSCORED': name.replace('-', '_'),
        'MODULE_TYPE': module_type,
        'ENVIRONMENT': environment or 'dev',
        'DESCRIPTION': description or f'{module_type.upper()} module',
        'AUTHOR': author,
        'DATE': date,
        'TERRAFORM_VERSION': version or '>= 1.0',
        'PROVIDER': provider or 'aws',
    }

    return variables
```

### 2. Template Loading

```python
def load_templates(module_type):
    """Load all template files for a module type"""

    template_dir = f'.claude/skills/terraform-module-architect/templates/{module_type}'
    templates = {}

    # Walk directory tree
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.template'):
                # Get full path
                template_path = os.path.join(root, file)

                # Read template content
                with open(template_path, 'r') as f:
                    content = f.read()

                # Calculate relative path from template_dir
                rel_path = os.path.relpath(template_path, template_dir)

                # Store template
                templates[rel_path] = content

    return templates
```

### 3. Variable Substitution

```python
def substitute_variables(template_content, variables):
    """Replace all {{PLACEHOLDER}} with actual values"""

    result = template_content

    # Replace each variable
    for key, value in variables.items():
        placeholder = f'{{{{{key}}}}}'  # {{VARIABLE_NAME}}
        result = result.replace(placeholder, str(value))

    return result
```

### 4. File Generation

```python
def generate_files(templates, variables, output_path):
    """Generate all files from templates"""

    for template_path, template_content in templates.items():
        # Remove .template extension
        output_file = template_path.replace('.template', '')

        # Full output path
        full_output_path = os.path.join(output_path, output_file)

        # Create directory if needed
        os.makedirs(os.path.dirname(full_output_path), exist_ok=True)

        # Substitute variables
        rendered_content = substitute_variables(template_content, variables)

        # Write file
        with open(full_output_path, 'w') as f:
            f.write(rendered_content)

        print(f'  ✓ Generated {output_file}')
```

## Variable Reference

### MODULE_NAME
- **Source:** User input (name parameter)
- **Format:** kebab-case (lowercase, hyphens only)
- **Validation:** `^[a-z0-9-]+$`
- **Example:** `app-vpc`, `web-server`, `data-bucket`
- **Usage:** File names, resource names, documentation

### MODULE_NAME_UNDERSCORED
- **Source:** Derived from MODULE_NAME
- **Format:** snake_case (lowercase, underscores only)
- **Transformation:** `name.replace('-', '_')`
- **Example:** `app_vpc`, `web_server`, `data_bucket`
- **Usage:** Terraform resource identifiers (must be valid HCL identifiers)

### MODULE_TYPE
- **Source:** User input (type parameter)
- **Format:** lowercase string
- **Values:** custom, vpc, ec2, s3, rds, iam, eks, lambda, api-gateway
- **Example:** `vpc`, `ec2`, `s3`
- **Usage:** Template selection, documentation, tagging

### ENVIRONMENT
- **Source:** User input (environment parameter) or default
- **Format:** lowercase string
- **Values:** dev, staging, prod
- **Default:** `dev`
- **Example:** `prod`, `staging`
- **Usage:** Resource naming, tagging, conditional logic

### DESCRIPTION
- **Source:** User input (description parameter) or auto-generated
- **Format:** Plain text string
- **Default:** `{MODULE_TYPE} module`
- **Example:** `VPC module for application`, `S3 bucket module`
- **Usage:** README headers, documentation, comments

### AUTHOR
- **Source:** Git configuration (`git config user.name`)
- **Format:** Plain text string
- **Default:** `Platform Engineering Team` (if git user not set)
- **Example:** `John Doe`, `Platform Engineering Team`
- **Usage:** Documentation, file headers, attribution

### DATE
- **Source:** Current timestamp
- **Format:** ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)
- **Generation:** `datetime.now().isoformat()`
- **Example:** `2025-11-17T15:30:00Z`
- **Usage:** File headers, CHANGELOG, README

### TERRAFORM_VERSION
- **Source:** User input (version parameter) or default
- **Format:** Terraform version constraint
- **Default:** `>= 1.0`
- **Example:** `>= 1.0`, `>= 1.5`
- **Usage:** versions.tf, README requirements table

### PROVIDER
- **Source:** User input (provider parameter) or default
- **Format:** lowercase provider name
- **Values:** aws, azure, gcp
- **Default:** `aws`
- **Example:** `aws`, `azure`
- **Usage:** Provider configuration, resource prefixes

## Template Syntax Rules

### Valid Placeholder Format
```
{{VARIABLE_NAME}}
```

### Rules:
1. Double curly braces
2. Variable name in UPPERCASE
3. Underscores for multi-word variables
4. No spaces inside braces

### Valid Examples:
- `{{MODULE_NAME}}`
- `{{MODULE_NAME_UNDERSCORED}}`
- `{{TERRAFORM_VERSION}}`

### Invalid Examples:
- `{ {MODULE_NAME} }` (spaces)
- `{{module_name}}` (lowercase)
- `{{MODULE-NAME}}` (hyphens)
- `{{ MODULE_NAME }}` (internal spaces)

## Testing Substitution

### Test Case 1: VPC Module
```
Input:
  name: app-vpc
  type: vpc
  environment: prod
  description: Application VPC
  provider: aws
  version: >= 1.0

Variables:
  MODULE_NAME: app-vpc
  MODULE_NAME_UNDERSCORED: app_vpc
  MODULE_TYPE: vpc
  ENVIRONMENT: prod
  DESCRIPTION: Application VPC
  AUTHOR: John Doe
  DATE: 2025-11-17T15:30:00Z
  TERRAFORM_VERSION: >= 1.0
  PROVIDER: aws

Template:
  resource "aws_vpc" "{{MODULE_NAME_UNDERSCORED}}" {
    cidr_block = var.cidr_block
    tags = {
      Name = "{{MODULE_NAME}}"
      Type = "{{MODULE_TYPE}}"
    }
  }

Output:
  resource "aws_vpc" "app_vpc" {
    cidr_block = var.cidr_block
    tags = {
      Name = "app-vpc"
      Type = "vpc"
    }
  }
```

### Test Case 2: README Header
```
Template:
  # {{MODULE_NAME}} - Terraform Module

  {{DESCRIPTION}}

  Created on {{DATE}} by {{AUTHOR}}

Output:
  # app-vpc - Terraform Module

  Application VPC

  Created on 2025-11-17T15:30:00Z by John Doe
```

## Error Handling

### Missing Variables
- **Issue:** Template references {{UNDEFINED_VAR}}
- **Detection:** After substitution, check for remaining `{{`
- **Resolution:** Warn user, leave placeholder in place

### Special Characters
- **Issue:** Variable value contains special characters
- **Examples:** quotes, backslashes, newlines
- **Resolution:** Escape for Terraform HCL if needed

### Empty Values
- **Issue:** Variable is empty string or None
- **Resolution:** Use default value, never leave empty

## Implementation Checklist

- [ ] Variable preparation function created
- [ ] Template loading function created
- [ ] Substitution function created
- [ ] File generation function created
- [ ] All 9 variables supported
- [ ] Validation for kebab-case names
- [ ] Git user retrieval with fallback
- [ ] ISO 8601 date formatting
- [ ] Recursive template directory scanning
- [ ] .template extension handling
- [ ] Directory creation for nested paths
- [ ] Error handling for missing templates
- [ ] Warning for undefined variables
- [ ] Test cases pass
