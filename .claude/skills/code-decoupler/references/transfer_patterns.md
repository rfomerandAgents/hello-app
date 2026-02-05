# Transfer Patterns Reference

This document provides detailed transfer strategies for each directory type when decoupling a project repository into a generic template.

## Full Copy Pattern

**Strategy**: Copy entire directory structure recursively with all files intact.

**Use Case**: Directories containing reusable automation, infrastructure code, or development tooling that is not project-specific.

### Directories Using Full Copy

#### `.claude/commands/`
**Description**: All markdown command files that define slash commands for Claude Code CLI.

**What to copy**:
- All `.md` files in commands/
- Subdirectories like `e2e/` for test commands
- Command documentation and examples

**What to exclude**:
- None - all commands are reusable

**Example files**:
- `install.md` - Installation command
- `prime.md` - Project primer
- `bug.md` - Bug workflow
- `feature.md` - Feature workflow
- `chore.md` - Chore workflow
- `e2e/` - End-to-end test commands

---

#### `.claude/agents/`
**Description**: Agent definition files with frontmatter configuration.

**What to copy**:
- All `.md` agent definition files
- Agent configuration with name, description, tools, model

**What to exclude**:
- None - agent definitions are reusable

**Example files**:
- `plan-implementer.md` - Plan implementation agent
- Other custom agents

---

#### `.claude/hooks/`
**Description**: Custom hook scripts and utilities for Claude Code CLI lifecycle events.

**What to copy**:
- All `.py` hook files (pre_tool_use.py, post_tool_use.py, etc.)
- `utils/` subdirectory with LLM utilities
- Hook configuration and helpers

**What to exclude**:
- `__pycache__/` directories (already in .gitignore)

**Example files**:
- `pre_tool_use.py` - Pre-execution hooks
- `post_tool_use.py` - Post-execution hooks
- `notification.py` - Notification hooks
- `stop.py` - Stop hooks
- `utils/` - Hook utilities

---

#### `.claude/skills/`
**Description**: Project-local skills that extend Claude Code capabilities.

**What to copy**:
- All skill directories with SKILL.md files
- Skill references/, scripts/, assets/ subdirectories
- Templates and documentation

**What to exclude**:
- None - skills are designed to be reusable

**Example skills**:
- `terraform-module-architect/`
- `packer-optimizer/`
- `aws-solutions-architect/`
- `python-devops-wrapper-scripts/`

---

#### `adws/`
**Description**: AI Developer Workflow system - complete Python automation framework.

**What to copy**:
- All `adw_*.py` scripts
- `adw_modules/` directory with core modules
- `adw_triggers/` directory with webhook and cron triggers
- `adw_tests/` directory with test suite
- `pyproject.toml` and dependencies
- README.md with documentation

**What to exclude**:
- `__pycache__/` directories
- `.venv/` if present
- `.pytest_cache/` if present

**Purpose**: Complete AI-powered workflow automation system for GitHub issues.

---

#### `app_docs/`
**Description**: Documentation directory with guides, references, and assets.

**What to copy**:
- All `.md` documentation files
- `assets/` directory for images and diagrams
- Architecture documentation
- Troubleshooting guides

**What to exclude**:
- Project-specific screenshots showing "{{PROJECT_NAME}}" content
- Customer-specific documentation

**Strategy**: Copy structure, review images for project-specific content.

---

#### `ipe/`
**Description**: Infrastructure Platform Engineer scripts for Terraform automation.

**What to copy**:
- All `ipe_*.py` scripts
- `ipe_modules/` directory with core modules
- Test files
- pyproject.toml and dependencies
- README.md with documentation

**What to exclude**:
- `__pycache__/` directories
- `.venv/` if present
- Log files (stored in ipe_logs/)

**Purpose**: Terraform workflow automation system.

---

#### `scripts/`
**Description**: Utility scripts for various automation tasks.

**What to copy**:
- All shell scripts (.sh files)
- Python scripts (.py files)
- Utility documentation

**What to exclude**:
- Scripts with hardcoded project-specific paths (document these for customization)

**Note**: Some scripts may need path updates after copy.

---

#### `triggers/`
**Description**: Webhook and cron trigger configurations.

**What to copy**:
- All trigger definition files
- Webhook server configurations
- Cron job definitions

**What to exclude**:
- None - triggers are reusable

---

#### `mcp/`
**Description**: Model Context Protocol server configurations.

**What to copy**:
- All MCP configuration JSON files
- Server definitions

**What to exclude**:
- API keys or secrets (should be in environment variables)

**Example files**:
- `playwright-mcp-config.json`

---

## Structure Only Pattern

**Strategy**: Create empty directory structure with .gitkeep files to preserve directories in git.

**Use Case**: Directories that will be populated with project-specific content by users.

### Directories Using Structure Only

#### `app/`
**Description**: Application code directory (project-specific).

**What to create**:
- `app/.gitkeep` - Preserve empty directory

**Purpose**: Placeholder for Next.js, React, or other application code.

---

#### `ipe_logs/`
**Description**: Infrastructure Platform Engineer log directory.

**What to create**:
- `ipe_logs/.gitkeep` - Preserve empty directory

**Purpose**: Runtime logs from IPE workflows.

---

#### `logs/`
**Description**: Session logs from Claude Code CLI.

**What to create**:
- `logs/.gitkeep` - Preserve empty directory

**Purpose**: Claude CLI session logs.

---

#### `specs/`
**Description**: Specification documents with subdirectories.

**What to create**:
- `specs/high-level/.gitkeep`
- `specs/medium-level/.gitkeep`
- `specs/low-level/.gitkeep`
- `specs/README.md` - Explanation of spec types

**Purpose**: Organized specification documents.

**README.md content**:
```markdown
# Specifications

This directory contains specification documents at different abstraction levels.

## Directory Structure

- `high-level/` - Business requirements, user stories, conceptual designs
- `medium-level/` - Architecture designs, component specifications, API contracts
- `low-level/` - Detailed implementation plans, code-level specifications

## Usage

1. Create high-level spec first (what to build, why)
2. Create medium-level spec (how to architect it)
3. Create low-level spec (detailed implementation plan)
4. Use specs as input for /feature, /bug, /chore commands
```

---

#### `agents/`
**Description**: Agent output directory for autonomous workflows.

**What to create**:
- `agents/.gitkeep` - Preserve empty directory

**Purpose**: Output from AI agents during workflow execution.

---

#### `trees/`
**Description**: Directory tree visualization output.

**What to create**:
- `trees/.gitkeep` - Preserve empty directory

**Purpose**: Tree command output for documentation.

---

## Scaffolding Pattern

**Strategy**: Create template structure with generic placeholders and example configurations.

**Use Case**: Infrastructure code that needs project-specific customization but follows standard patterns.

### Directories Using Scaffolding

#### `io/terraform/`
**Description**: Infrastructure as Code with Terraform and Packer.

**What to create**:

1. **Root Terraform files**:
   - `main.tf` - Generic AWS provider and placeholder resources
   - `variables.tf` - Common variables (region, environment, instance_type, ami_id)
   - `outputs.tf` - Standard outputs (instance_id, public_ip, website_url)
   - `terraform.tf` - Terraform version and backend configuration
   - `.gitignore` - Terraform-specific ignores
   - `README.md` - Terraform usage documentation

2. **Packer subdirectory**:
   - `io/packer/app.pkr.hcl` - Generic Packer AMI builder template
   - `io/packer/scripts/install-nodejs.sh` - Example Node.js provisioner
   - `io/packer/scripts/install-nginx.sh` - Example nginx provisioner
   - `io/packer/scripts/.gitkeep` - For additional provisioner scripts

3. **Scripts subdirectory**:
   - `scripts/build-ami.sh` - Placeholder AMI build script
   - `scripts/deploy.sh` - Placeholder deploy script
   - `scripts/destroy.sh` - Placeholder destroy script
   - `scripts/.gitkeep` - For additional deployment scripts

**Placeholders to use**:
- `{{PROJECT_NAME}}` - Project identifier
- `{{ORGANIZATION}}` - Terraform Cloud organization
- `{{AWS_REGION}}` - AWS region (default: us-east-1)
- `{{AMI_ID}}` - Placeholder AMI ID
- `{{INSTANCE_TYPE}}` - EC2 instance type (default: t2.micro)

**See**: `terraform_scaffolding.md` for complete file templates.

---

## Genericized Pattern

**Strategy**: Copy files with content transformation to remove project-specific details.

**Use Case**: Configuration files and documentation that need project context removed.

### Files Using Genericized Pattern

#### `README.md`
**Source**: Project root README.md

**Transformations**:

| Find | Replace | Context |
|------|---------|---------|
| "{{PROJECT_NAME}}" | `{{PROJECT_NAME}}` | Project name |
| "{{PROJECT_DOMAIN}}" | `{{DOMAIN}}` | Domain name |
| "Miniature Mediterranean Items" | `{{PROJECT_DESCRIPTION}}` | Project description |
| "https://github.com/your-username/{{PROJECT_DOMAIN}}" | `{{GITHUB_REPO_URL}}` | Repository URL |
| "Port 3000" | `{{APP_PORT}}` | Port numbers |
| Specific AWS account IDs | `{{AWS_ACCOUNT_ID}}` | AWS identifiers |

**Sections to preserve**:
- Project structure documentation
- ADW system documentation
- IPE system documentation
- GitHub Actions workflow documentation
- Development setup instructions
- Troubleshooting guides

**Sections to remove**:
- Item breeding program details
- Farm-specific features
- Customer testimonials
- Project-specific deployment URLs

**See**: `readme_template.md` for complete template.

---

#### `.claude/settings.json`
**Source**: .claude/settings.json

**Transformations**:
- Preserve `permissions` structure exactly
- Preserve `hooks` configuration exactly
- Remove any `apiKeys` or `secrets` fields if present
- Keep structure valid JSON

**Example**:
```json
{
  "permissions": {
    "allow": [
      "Bash(mkdir:*)",
      "Bash(uv:*)",
      "Write"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

---

#### `.gitignore`
**Source**: Project root .gitignore

**Strategy**: Copy as-is with comprehensive patterns.

**Includes**:
- Python patterns (__pycache__, .venv, etc.)
- Node patterns (node_modules, .next, etc.)
- Environment files (.env, .env.local)
- IDE files (.vscode, .idea)
- OS files (.DS_Store)
- Log directories (logs/, ipe_logs/)
- Git worktrees (.worktrees/)
- Agent outputs (agents/)
- Terraform state files

**Note**: Generally no transformation needed, copy as-is.

---

## Summary Table

| Directory/File | Pattern | Complexity | Validation |
|----------------|---------|------------|------------|
| `.claude/commands/` | Full Copy | Low | File count |
| `.claude/agents/` | Full Copy | Low | File count |
| `.claude/hooks/` | Full Copy | Low | Python syntax |
| `.claude/skills/` | Full Copy | Medium | Skill structure |
| `.claude/settings.json` | Genericized | Low | JSON validity |
| `adws/` | Full Copy | High | Python imports |
| `app_docs/` | Full Copy | Low | File count |
| `ipe/` | Full Copy | High | Python imports |
| `scripts/` | Full Copy | Medium | Shell syntax |
| `triggers/` | Full Copy | Low | File count |
| `mcp/` | Full Copy | Low | JSON validity |
| `app/` | Structure Only | Low | Directory exists |
| `ipe_logs/` | Structure Only | Low | Directory exists |
| `logs/` | Structure Only | Low | Directory exists |
| `specs/` | Structure Only | Low | Subdirectories |
| `agents/` | Structure Only | Low | Directory exists |
| `trees/` | Structure Only | Low | Directory exists |
| `io/terraform/` | Scaffolding | High | HCL syntax |
| `README.md` | Genericized | Medium | No leaks |
| `.gitignore` | Genericized | Low | Pattern validity |

---

## Edge Cases

### Missing Source Directories

Some directories may not exist in the source repository:
- Skip gracefully with warning message
- Document in validation report
- Continue with remaining directories

### Symlinks

If symlinks are encountered:
- Copy link targets, not the links themselves
- Warn if link points outside source directory
- Document broken links in validation report

### Large Files

app_docs/assets may have large images:
- Consider size limits (e.g., skip files > 10MB)
- Warn about large assets
- Suggest optimizing images

### Binary Files

Exclude these automatically:
- Packer logs (*.log in io/terraform/logs/)
- Compiled Python files (*.pyc, __pycache__/)
- Node modules (node_modules/)
- Git objects (.git/)

### Hidden Files

Handle carefully:
- Exclude: .DS_Store, Thumbs.db
- Include: .gitkeep, .gitignore, .github/
- Preserve: .claude/, .env.example
