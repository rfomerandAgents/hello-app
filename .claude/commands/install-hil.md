---
description: Human-in-the-loop interactive installation workflow
---

# Purpose

Run an interactive installation workflow that guides the user through setup decisions, asking questions and adapting to their specific context.

## Prerequisites

The setup_init hook has already run via `--init` flag. This prompt guides the user through additional configuration and verification.

## Phase 1: Initial Questions

Ask the user the following questions to understand their context:

```
🔧 **Interactive Installation Setup**

I'll help you configure this project. First, a few questions:

1. **Environment Type**: What environment are you setting up?
   - Development (local machine)
   - CI/CD (automated pipeline)
   - Production (deployment target)
   - Sandbox (testing/experimentation)

2. **Installation Scope**: What do you want to install?
   - Full (all dependencies, all features)
   - Minimal (core dependencies only)
   - Custom (let me choose specific components)

3. **Infrastructure**: Do you need infrastructure components?
   - Yes, set up Terraform/Packer
   - No, application code only
   - Not sure, help me decide

4. **Environment Variables**: How should I handle .env configuration?
   - Create from template (copy .env.example)
   - Guided setup (ask me for each value)
   - Skip (I'll configure manually)
```

## Phase 2: Read Installation Log

After getting answers, read the setup log:

```bash
cat .claude/hooks/setup.init.log
```

Analyze what the deterministic hook already completed.

## Phase 3: Environment-Specific Setup

Based on user answers, run appropriate setup:

### For Development Environment

```bash
# Verify local tools
command -v uv && uv --version
command -v node && node --version
command -v terraform && terraform --version

# Check for .env file
if [ ! -f .env ]; then
  echo "No .env file found"
fi
```

### For CI/CD Environment

```bash
# Verify CI-essential tools
command -v git && git --version
command -v uv && uv --version

# Check for secrets configuration
ls -la .github/workflows/ 2>/dev/null
```

### For Infrastructure Setup

```bash
# Check Terraform configuration
ls -la ipe/terraform/*.tf 2>/dev/null

# Check Packer templates
ls -la ipe/packer/*.pkr.hcl 2>/dev/null

# Verify AWS credentials if needed
command -v aws && aws sts get-caller-identity 2>/dev/null || echo "AWS not configured"
```

## Phase 4: Guided .env Setup (if requested)

If the user selected "Guided setup" for environment variables:

1. Read `.env.example` or `.env.template` if it exists
2. For each variable, explain what it's for and ask for the value
3. Write the configured values to `.env`

Example interaction:
```
📝 **Environment Variable Configuration**

Let's configure your environment variables:

**GITHUB_TOKEN** (required)
Used for: GitHub API access for issue tracking and PR creation
Format: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Your value: [user provides]

**AWS_PROFILE** (optional)
Used for: AWS credential profile for infrastructure deployment
Default: default
Your value: [user provides or accepts default]
```

## Phase 5: Verification

Run verification checks based on what was installed:

```bash
# Python environment
uv run python --version 2>/dev/null && echo "✓ Python environment ready"

# Node environment  
node --version 2>/dev/null && echo "✓ Node.js ready"

# Git hooks
ls -la .git/hooks/ 2>/dev/null | head -5

# Test suite
uv run pytest --collect-only 2>/dev/null | tail -5 || echo "No tests found or pytest not available"
```

## Phase 6: Generate Report

Write results to `app_docs/install_results.md`:

```markdown
## Installation Report - [DATE]

**Environment**: [Development/CI/Production/Sandbox]
**Scope**: [Full/Minimal/Custom]
**Status**: SUCCESS | PARTIAL | FAILED

### What was configured
- [list of completed setup steps]

### Environment Variables
| Variable | Status | Notes |
|----------|--------|-------|
| [name]   | ✓/✗    | [note]|

### Verification Results
- Python: [status]
- Node.js: [status]
- Infrastructure: [status]

### Manual Steps Required
1. [any steps the user needs to complete manually]

### Quick Start
To start working:
\`\`\`bash
# [relevant commands based on setup]
\`\`\`
```

## Phase 7: Next Steps

Provide personalized next steps based on what was set up:

```
✅ **Installation Complete!**

Based on your setup, here's what to do next:

1. **Start developing**: [specific command]
2. **Run tests**: [specific command]
3. **Read documentation**: [specific file]

Need help? Run `/prime` to load full project context.
```
