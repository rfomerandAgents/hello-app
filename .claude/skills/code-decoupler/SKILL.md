---
name: code-decoupler
description: Expert code decoupling skill for extracting reusable backend automation patterns from project repositories into clean, genericized GitHub templates. Use when creating template repositories from existing projects, separating project-specific code from reusable infrastructure, scaffolding new automation projects, or preparing codebases for open-source release. Includes transfer pattern documentation, Terraform scaffolding templates, README genericization rules, and validation scripts for ensuring template quality.
---

# Code Decoupler

## Overview

This skill provides expert guidance for extracting reusable backend automation patterns from project-specific repositories into clean, genericized GitHub templates. It enables the systematic separation of infrastructure code, automation workflows, and development tooling from project-specific implementations.

## Core Philosophy

### Separation Principles

1. **Preserve Reusable Patterns** - Extract automation systems (ADW, IPE), infrastructure patterns (Terraform, Packer), and development workflows
2. **Remove Project Context** - Strip project-specific content while maintaining documentation structure and examples
3. **Create Clean Scaffolds** - Provide empty directory structures and placeholder templates for new projects
4. **Enable Quick Starts** - Generate templates that work out-of-the-box with minimal configuration
5. **Maintain Quality** - Ensure extracted templates pass validation and are production-ready

## Transfer Strategy

The decoupling process categorizes directories into four transfer types:

### 1. Full Copy Pattern

Copy entire directory structure with all files intact. Used for:
- `.claude/commands/` - Command definitions
- `.claude/agents/` - Agent configurations
- `.claude/hooks/` - Custom hooks and utilities
- `.claude/skills/` - Project-local skills
- `adws/` - AI Developer Workflow system
- `app_docs/` - Documentation (excluding project-specific screenshots)
- `ipe/` - Infrastructure Platform Engineer workflows
- `scripts/` - Utility scripts
- `triggers/` - Webhook and cron triggers
- `mcp/` - Model Context Protocol configuration

### 2. Structure Only Pattern

Create empty directory structure with .gitkeep files. Used for:
- `app/` - Application directory (project-specific)
- `ipe_logs/` - Log directory
- `logs/` - Session logs
- `specs/` - Specification documents (with subdirectories: high-level/, medium-level/, low-level/)
- `agents/` - Agent output directory
- `trees/` - Tree visualization directory

### 3. Scaffolding Pattern

Create template structure with generic placeholders. Used for:
- `io/terraform/` - Infrastructure as Code templates
  - Generic main.tf, variables.tf, outputs.tf, terraform.tf
  - Packer templates with placeholder AMI configurations
  - Deployment scripts with configurable paths

### 4. Genericized Pattern

Copy with content transformation. Used for:
- `README.md` - Replace project-specific content with placeholders
- `.claude/settings.json` - Clear secrets, preserve structure
- `.gitignore` - Standard patterns for all file types

## Decoupling Workflow

### Step 1: Source Validation
- Verify source directory exists and is a git repository
- Confirm presence of key directories (.claude/, adws/, io/terraform/)
- Check for clean git status (warn if uncommitted changes)

### Step 2: Target Preparation
- Create target directory if it doesn't exist
- Initialize git repository in target
- Verify target is empty or get user confirmation to overwrite

### Step 3: Full Copy Directories
- Copy .claude/ subdirectories (commands, agents, hooks, skills)
- Copy automation systems (adws/, ipe/)
- Copy documentation (app_docs/)
- Copy utility directories (scripts/, triggers/, mcp/)
- Preserve file permissions and structure

### Step 4: Create Empty Structures
- Create app/ with .gitkeep
- Create log directories (ipe_logs/, logs/)
- Create specs/ with subdirectories
- Create agents/ and trees/ directories

### Step 5: Generate Terraform Scaffolding
- Create io/terraform/ directory structure
- Generate generic main.tf with AWS provider
- Create variables.tf with common variables (aws_region, environment, instance_type)
- Create outputs.tf with placeholder outputs
- Create terraform.tf with backend configuration template
- Create io/packer/app.pkr.hcl with generic AMI builder
- Create io/packer/scripts/ and scripts/ with .gitkeep files
- Add io/terraform/.gitignore for state files

### Step 6: Genericize Files
- Transform README.md:
  - Replace "{{PROJECT_NAME}}" with {{PROJECT_NAME}}
  - Replace "{{PROJECT_DOMAIN}}" with {{DOMAIN}}
  - Replace specific descriptions with {{PROJECT_DESCRIPTION}}
  - Preserve automation system documentation (ADW, IPE)
  - Update badge URLs to placeholders
- Transform .claude/settings.json:
  - Preserve permissions structure
  - Preserve hooks configuration
  - Clear any API tokens or secrets
- Copy .gitignore with standard patterns

### Step 7: Create Root Files
- Copy or create CLAUDE.md with placeholder instructions
- Create .env.example (never copy .env)
- Create LICENSE if deparentAd
- Create basic package.json or pyproject.toml if needed

### Step 8: Validation
- Run validation script (validate_template.py)
- Check all required directories exist
- Verify no project-specific content leaked
- Confirm .claude/settings.json is valid JSON
- Optionally validate Terraform syntax
- Generate validation report

### Step 9: Documentation
- Create template README with usage instructions
- Document customization points
- List placeholder variables to replace
- Include setup checklist

## Directory Mapping

| Source | Target | Transfer Type | Notes |
|--------|--------|---------------|-------|
| `.claude/commands/` | `.claude/commands/` | Full Copy | All command definitions |
| `.claude/agents/` | `.claude/agents/` | Full Copy | Agent configurations |
| `.claude/hooks/` | `.claude/hooks/` | Full Copy | Custom hooks |
| `.claude/skills/` | `.claude/skills/` | Full Copy | Project-local skills |
| `.claude/settings.json` | `.claude/settings.json` | Genericized | Clear secrets |
| `adws/` | `adws/` | Full Copy | Complete workflow system |
| `app_docs/` | `app_docs/` | Full Copy | Documentation |
| `ipe/` | `ipe/` | Full Copy | Infrastructure workflows |
| `scripts/` | `scripts/` | Full Copy | Utility scripts |
| `triggers/` | `triggers/` | Full Copy | Webhook triggers |
| `mcp/` | `mcp/` | Full Copy | MCP configuration |
| `app/` | `app/` | Structure Only | Empty with .gitkeep |
| `ipe_logs/` | `ipe_logs/` | Structure Only | Empty with .gitkeep |
| `logs/` | `logs/` | Structure Only | Empty with .gitkeep |
| `specs/` | `specs/` | Structure Only | With subdirectories |
| `agents/` | `agents/` | Structure Only | Empty with .gitkeep |
| `trees/` | `trees/` | Structure Only | Empty with .gitkeep |
| `io/terraform/` | `io/terraform/` | Scaffolding | Generic templates |
| `README.md` | `README.md` | Genericized | Placeholder content |
| `.gitignore` | `.gitignore` | Genericized | Standard patterns |

## Terraform Scaffolding Details

### Files Created

1. **io/terraform/main.tf** - AWS provider and placeholder resources
2. **io/terraform/variables.tf** - Common variables (region, environment, instance_type, ami_id)
3. **io/terraform/outputs.tf** - Standard outputs (instance_id, public_ip, website_url)
4. **io/terraform/terraform.tf** - Terraform version and backend configuration
5. **io/terraform/.gitignore** - Terraform-specific ignores
6. **io/terraform/io/packer/app.pkr.hcl** - Generic Packer AMI builder
7. **io/terraform/io/packer/scripts/install-nodejs.sh** - Example provisioner script
8. **io/terraform/io/packer/scripts/install-nginx.sh** - Example provisioner script
9. **io/terraform/scripts/build-ami.sh** - Placeholder build script
10. **io/terraform/scripts/deploy.sh** - Placeholder deploy script

### Placeholders Used

- `{{PROJECT_NAME}}` - For resource naming
- `{{ORGANIZATION}}` - For Terraform Cloud organization
- `{{AWS_REGION}}` - Default AWS region
- Comments explaining what to customize

## README Genericization

### Content to Replace

| Original | Replacement | Example |
|----------|-------------|---------|
| "{{PROJECT_NAME}}" | `{{PROJECT_NAME}}` | "{{PROJECT_NAME}} Website" → "{{PROJECT_NAME}} Website" |
| "{{PROJECT_DOMAIN}}" | `{{DOMAIN}}` | "{{PROJECT_DOMAIN}}" → "{{DOMAIN}}" |
| "Miniature Mediterranean Items" | `{{PROJECT_DESCRIPTION}}` | Description field |
| Specific GitHub URLs | `{{GITHUB_REPO_URL}}` | https://github.com/owner/repo |
| Badge URLs | Placeholder badges | Generic status badges |
| Port numbers | Configurable variables | Port 3000 → `{{APP_PORT}}` |

### Sections to Preserve

- Project structure documentation
- ADW system documentation
- IPE system documentation
- Terraform and Packer integration guides
- GitHub Actions workflow documentation
- Development commands
- Troubleshooting structure

### Sections to Remove

- Project-specific feature descriptions (items, farm details)
- Specific deployment URLs
- Project-specific screenshots
- Customer/business-specific content

## Validation Checklist

After decoupling, the template should pass these checks:

- [ ] All required directories exist
- [ ] .claude/settings.json is valid JSON
- [ ] README.md has no project-specific content
- [ ] Terraform files are syntactically valid
- [ ] No secrets or API tokens present
- [ ] .gitignore includes all necessary patterns
- [ ] Git repository initialized
- [ ] No broken symlinks
- [ ] Python packages have valid dependencies
- [ ] All .gitkeep files present in empty directories

## How to Use

### Manual Invocation

Use the skill when creating a template repository from an existing project:

```
"Decouple this repository's backend automation to ../agentic_coding_template"
```

### Using the Script

The automation script can be run directly:

```bash
# Basic usage
python .claude/skills/code-decoupler/scripts/decouple.py \
  --source /path/to/source \
  --target /path/to/target

# Dry run to preview actions
python .claude/skills/code-decoupler/scripts/decouple.py \
  --source /path/to/source \
  --target /path/to/target \
  --dry-run

# Verbose output
python .claude/skills/code-decoupler/scripts/decouple.py \
  --source /path/to/source \
  --target /path/to/target \
  --verbose
```

### Validation

After decoupling, validate the template:

```bash
python .claude/skills/code-decoupler/scripts/validate_template.py /path/to/target
```

## Customization Points

After generating a template, customize these areas:

1. **README.md** - Replace all `{{PLACEHOLDER}}` variables
2. **io/terraform/terraform.tfvars** - Set project-specific values
3. **io/terraform/io/packer/app.pkr.hcl** - Update AMI configuration
4. **CLAUDE.md** - Add project-specific instructions
5. **.env.example** - Document required environment variables
6. **app/** - Add your application code
7. **specs/** - Add your specifications

## Common Use Cases

### Creating an Open-Source Template

Extract reusable automation from a client project:
1. Run decoupler with source as client repo
2. Validate template output
3. Review and test automation workflows
4. Publish to GitHub as public template

### Starting a New Project

Use existing template as foundation:
1. Clone the generated template
2. Replace placeholders in README
3. Configure Terraform variables
4. Add application code to app/
5. Customize Claude instructions

### Migrating Infrastructure Patterns

Extract just the infrastructure code:
1. Use decoupler on existing project
2. Keep only io/terraform/, scripts/, ipe/ directories
3. Integrate into new project structure
4. Update variable names and paths

## Security Considerations

### Secrets Management

- Never copy .env files (use .env.example)
- Clear all API tokens from .claude/settings.json
- Remove SSH keys from Terraform variables
- Exclude terraform.tfstate files
- Strip AWS credentials from scripts

### Content Validation

The validation script searches for:
- Project-specific names (case-insensitive)
- Specific email addresses
- API token patterns
- AWS account IDs
- Specific domain names

## Related Skills

- `terraform-module-architect` - For creating Terraform modules
- `aws-solutions-architect` - For AWS infrastructure patterns
- `python-devops-wrapper-scripts` - For automation script patterns

## References

See the `references/` directory for detailed documentation:
- `transfer_patterns.md` - Detailed transfer strategy for each directory type
- `terraform_scaffolding.md` - Complete Terraform scaffold templates
- `readme_template.md` - README genericization guide
- `workflow.md` - Step-by-step decoupling workflow

## Scripts

Available in `scripts/` directory:
- `decouple.py` - Main decoupling automation script
- `validate_template.py` - Template validation and quality checks

## Assets

Template files in `assets/` directory:
- `generic_readme.md` - Complete generic README template
- `generic_claude_md.md` - Template CLAUDE.md file
- `generic_gitignore` - Comprehensive .gitignore template
