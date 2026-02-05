# README Template Reference

This document provides guidance for genericizing the README.md file when creating a template repository.

## Replacement Strategy

### Text Replacements

| Find Pattern | Replace With | Notes |
|--------------|--------------|-------|
| `{{PROJECT_NAME}}` | `{{PROJECT_NAME}}` | Main project name |
| `{{PROJECT_DOMAIN}}` | `{{DOMAIN}}` | Domain name |
| `{{PROJECT_SLUG}}` | `{{PROJECT_NAME_SLUG}}` | Kebab-case identifier |
| `Miniature Mediterranean Items` | `{{PROJECT_DESCRIPTION}}` | Project description |
| `https://github.com/your-username/{{PROJECT_DOMAIN}}` | `{{GITHUB_REPO_URL}}` | Repository URL |
| `your-username` | `{{GITHUB_OWNER}}` | GitHub username/org |
| `Port 3000` | `{{APP_PORT}}` | Application port |
| `Port 18333` | `{{CONTROL_PLANE_PORT}}` | Control plane port |
| Specific AWS account numbers | `{{AWS_ACCOUNT_ID}}` | AWS account identifier |
| Specific AMI IDs (ami-xxxxx) | `{{AMI_ID}}` | AMI placeholder |

### Badge URL Replacements

Replace specific badge URLs with generic placeholders:

**Before**:
```markdown
[![App Deploy](https://github.com/your-username/{{PROJECT_DOMAIN}}/actions/workflows/app-build-deploy.yml/badge.svg)](https://github.com/your-username/{{PROJECT_DOMAIN}}/actions/workflows/app-build-deploy.yml)
```

**After**:
```markdown
[![App Deploy]({{GITHUB_REPO_URL}}/actions/workflows/app-build-deploy.yml/badge.svg)]({{GITHUB_REPO_URL}}/actions/workflows/app-build-deploy.yml)
```

## Sections to Preserve (with genericization)

### 1. Project Components

Keep the structure, replace project-specific names:

**Before**:
```markdown
### 🫏 {{PROJECT_NAME}} Website (`app/`)
A modern, responsive Next.js website showcasing Miniature Mediterranean Items breeding program since 2011.
```

**After**:
```markdown
### 📱 {{PROJECT_NAME}} Application (`app/`)
A modern, responsive Next.js application for {{PROJECT_DESCRIPTION}}.
```

### 2. Prerequisites

Keep all prerequisite sections as-is:
- For {{PROJECT_NAME}} Application
- For AI Developer Workflow
- For Infrastructure Platform Engineer

No changes needed - these are generic.

### 3. Quick Start

Keep all quick start instructions:
- Using Install Command
- Manual Installation
- Development commands

Replace specific port numbers with placeholders.

### 4. ADW System Documentation

**PRESERVE COMPLETELY** - This is reusable automation:
- All ADW features and descriptions
- Prerequisites section
- Environment variables section
- Usage modes (manual, cron, webhook)
- How ADW Works section

Only replace repo URLs with `{{GITHUB_REPO_URL}}`.

### 5. IPE System Documentation

**PRESERVE COMPLETELY** - This is reusable automation:
- Key features
- Workflows (test, ship)
- Prerequisites
- Safety features

No changes needed - completely generic.

### 6. E2B Cloud Sandbox Integration

**PRESERVE COMPLETELY** - Generic feature:
- Key features
- Quick start
- Dependencies
- Alternative (OBOX)

No changes needed.

### 7. GitHub Actions Deployment Workflows

**PRESERVE COMPLETELY** - Generic CI/CD patterns:
- Quick deployment instructions
- Deployment workflows documentation
- Required secrets section
- Workflow features
- Monitoring deployments

Replace specific badge URLs with placeholders.

### 8. Ground Control Console

**PRESERVE COMPLETELY** - Generic infrastructure UI:
- Features list
- Quick start
- Tech stack
- API routes
- Prerequisites

Replace port numbers with `{{CONTROL_PLANE_PORT}}`.

### 9. Project Structure

Keep the tree structure, genericize descriptions:

**Before**:
```markdown
└── app/                    # {{PROJECT_NAME}} Website
```

**After**:
```markdown
└── app/                    # {{PROJECT_NAME}} Application
```

### 10. Build and Deployment Pipeline

**PRESERVE COMPLETELY**:
- All GitHub Actions documentation
- Git worktrees documentation
- Terraform Cloud integration
- Manual deployment with git worktrees
- All deployment steps

Replace specific URLs and project names.

### 11. Troubleshooting

**PRESERVE STRUCTURE**, genericize examples:
- Keep all troubleshooting categories
- Replace project-specific examples
- Keep all command examples as-is

## Sections to Remove Completely

### 1. Project-Specific Feature Descriptions

Remove any content about:
- Item breeding programs
- Farm operations
- Specific business model
- Customer testimonials
- Project-specific case studies

### 2. Specific Deployment URLs

Remove:
- Live website URLs (http://54.123.45.67)
- Production domain references
- Specific IP addresses in examples

Keep as placeholders or example values.

### 3. Project-Specific Screenshots

Remove references to:
- Screenshots showing "{{PROJECT_NAME}}" branding
- Project-specific UI elements
- Customer-specific data

Keep generic screenshots if they show infrastructure patterns.

## Header Template

```markdown
# {{PROJECT_NAME}} - Project Repository

A comprehensive repository containing the {{PROJECT_NAME}} application and AI Developer Workflow (ADW) automation system.

## Project Components

### 📱 {{PROJECT_NAME}} Application (`app/`)
{{PROJECT_DESCRIPTION}}

**Features:**
- 🎨 Modern, responsive design
- 📱 Fully responsive (mobile, tablet, desktop)
- ⚡ Static export for fast deployment
- ♿ Accessibility-focused design

### 🤖 AI Developer Workflow (`adws/`)
Automated GitHub issue processing and implementation system using Claude Code CLI.

**Features:**
- 🔄 Automated issue classification and processing
- 🏗️ Autonomous implementation with git worktrees
- 📝 Automatic PR creation with semantic commits
- 🔍 Issue monitoring via webhook or cron polling

## Prerequisites

### For {{PROJECT_NAME}} Application
- Node.js 18+ or Bun
- npm, yarn, pnpm, or bun package manager

### For AI Developer Workflow
- Python 3.10+
- uv (Python package manager)
- GitHub CLI (`gh`)
- Claude Code CLI
- GitHub authentication

## Quick Start

### Using Install Command (Recommended)

Use the Claude Code CLI install command:

```bash
/install
```

This will install all dependencies for both the application and ADWS system.
```

## Environment Variables Template

Replace specific values with placeholders:

**Before**:
```bash
export GITHUB_REPO_URL="https://github.com/your-username/{{PROJECT_DOMAIN}}"
```

**After**:
```bash
export GITHUB_REPO_URL="{{GITHUB_REPO_URL}}"
export CLAUDE_CODE_OAUTH_TOKEN="your-claude-token-here"
export GITHUB_PAT="your-github-pat-here"
```

## Customization Instructions

Add a section to help users customize the template:

```markdown
## Customizing This Template

After cloning this template, customize the following:

### 1. Replace Placeholders

Search and replace these placeholders throughout the repository:

- `{{PROJECT_NAME}}` - Your project name (e.g., "My App")
- `{{DOMAIN}}` - Your domain name (e.g., "myapp.com")
- `{{PROJECT_DESCRIPTION}}` - Brief project description
- `{{GITHUB_REPO_URL}}` - Your GitHub repository URL
- `{{GITHUB_OWNER}}` - Your GitHub username or organization
- `{{AWS_ACCOUNT_ID}}` - Your AWS account ID
- `{{APP_PORT}}` - Your application port (default: 3000)

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and set:

```bash
GITHUB_REPO_URL=https://github.com/your-username/your-repo
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-...
GITHUB_PAT=ghp_...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### 3. Update Terraform Variables

Edit `io/terraform/terraform.tfvars`:

```hcl
project_name   = "your-project"
environment    = "dev"
aws_region     = "us-east-1"
ssh_public_key = "ssh-rsa AAA..."
```

### 4. Customize Application

Add your application code to `app/` directory.

### 5. Update Documentation

- Review and update this README
- Update badges and URLs
- Add project-specific troubleshooting
- Document your specific features
```

## Validation Checklist

After genericizing README:

- [ ] No occurrences of "{{PROJECT_NAME}}" (except in this checklist)
- [ ] No occurrences of "{{PROJECT_DOMAIN}}"
- [ ] No occurrences of "item" or "items"
- [ ] All GitHub URLs use `{{GITHUB_REPO_URL}}`
- [ ] All ports use placeholder variables
- [ ] ADW documentation preserved completely
- [ ] IPE documentation preserved completely
- [ ] GitHub Actions documentation preserved
- [ ] Project structure section updated
- [ ] Troubleshooting section is generic
- [ ] Customization instructions added

## Example Validation Commands

Search for project-specific content:

```bash
# Search for project name
grep -i "{{PROJECT_SLUG}}" README.md

# Search for domain
grep "{{PROJECT_DOMAIN}}" README.md

# Search for project-specific terms
grep -i "item\|farm\|miniature mediterranean" README.md

# Search for specific URLs
grep "github.com/your-username" README.md

# Search for specific ports (should be variables)
grep -E "Port [0-9]+" README.md
```

## Complete Generic README Template

See `../assets/generic_readme.md` for the complete genericized README template that can be used as-is or further customized.
