---
description: Run setup_init hook and report installation results
argument-hint: [hil]
---

# Purpose

Execute the repository initialization hook (setup_init) which installs all dependencies and discovers the project structure, then summarize and report the results to the user.

## Variables

MODE: $ARGUMENTS (optional - if "true", run interactive mode)

## Workflow

> Execute the following steps in order, top to bottom:

1. **First**, execute `Skill(/prime)` to understand the codebase
2. Check for interactive mode: If MODE is "true", run `Skill(/install-hil)` and ignore the remainder of this prompt
3. Read the log file at `.claude/hooks/setup.init.log` (the hook already ran via `--init` flag)
4. Analyze for successes and failures
5. Write results to `app_docs/install_results.md`
6. Report to user

## Analysis

When analyzing the installation log, look for:

- **Tool Availability**: Which development tools are installed (uv, node, terraform, etc.)
- **Dependency Installation**: Success/failure of uv sync, npm install, etc.
- **Project Discovery**: What subprojects and configurations were found
- **Environment Setup**: Any environment variables that were configured

## Common Issues

If you encounter any of the following issues, follow the steps to resolve them:

### Problem: uv not found
**Solution**: Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`

### Problem: node/npm not found
**Solution**: Install Node.js via nvm (`nvm install --lts`) or directly from nodejs.org

### Problem: terraform not found
**Solution**: Install via `brew install terraform` or from terraform.io/downloads

### Problem: Python dependency conflicts
**Solution**: Delete `.venv` and run `uv sync --all-extras` again

### Problem: Node dependency conflicts
**Solution**: Delete `node_modules` and `package-lock.json`, then run `npm install`

## Report

Write to `app_docs/install_results.md` and respond to user:

```markdown
## Installation Report - [DATE]

**Status**: SUCCESS | PARTIAL | FAILED

### System Tools
| Tool | Status | Version |
|------|--------|---------|
| uv   | ✓/✗    | [ver]   |
| node | ✓/✗    | [ver]   |
| ...  | ...    | ...     |

### Dependencies Installed
- [completed installation actions]

### Project Structure Discovered
- [detected projects and their locations]

### Warnings
- [any warnings or missing tools]

### Errors (if any)
- [errors with context and suggested fixes]

### Next Steps
1. Run `/prime` to load full project context
2. [any additional setup needed]
3. [how to start developing]
```

## Quick Start Commands

After successful installation, suggest relevant commands:

```bash
# For Python projects
uv run pytest                    # Run tests
uv run python -m <module>        # Run module

# For Node projects
npm run dev                      # Start dev server
npm test                         # Run tests

# For ASW workflows
just asw-app <issue>            # Run app workflow
just asw-io <issue>             # Run infrastructure workflow
```
