# Prime

> Load essential project context based on discovered project structure.

## Prerequisites

If you haven't run `/install` yet, run it first to discover the project structure and install dependencies.

## Phase 1: Project Discovery

Run discovery to understand what exists in this project:

```bash
echo "=== PROJECT STRUCTURE ==="

# Get file tree (limited depth)
echo "--- Directory Structure ---"
find . -maxdepth 3 -type d -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.worktrees/*" -not -path "*/.terraform/*" 2>/dev/null | head -50

# Find all README files for documentation
echo "--- Documentation Files ---"
find . -name "README.md" -not -path "*/node_modules/*" -not -path "*/.worktrees/*" 2>/dev/null

# Detect project types
echo "--- Project Types ---"

# Node.js/Frontend projects
echo "Node.js projects:"
find . -name "package.json" -not -path "*/node_modules/*" -not -path "*/.worktrees/*" -exec dirname {} \; 2>/dev/null

# Python projects
echo "Python projects:"
find . -name "pyproject.toml" -not -path "*/.worktrees/*" -exec dirname {} \; 2>/dev/null

# Terraform infrastructure
echo "Terraform directories:"
find . -name "*.tf" -not -path "*/.terraform/*" -not -path "*/.worktrees/*" -exec dirname {} \; 2>/dev/null | sort -u

# Packer templates
echo "Packer templates:"
find . \( -name "*.pkr.hcl" -o -name "*.pkr.json" \) 2>/dev/null

# GitHub workflows
echo "GitHub workflows:"
ls -la .github/workflows/*.yml 2>/dev/null || echo "No workflows found"

# Claude configuration
echo "Claude commands:"
ls .claude/commands/*.md 2>/dev/null | head -20 || echo "No commands found"
```

## Phase 2: Read Core Documentation

Read the root README.md first:

```
README.md
```

Then read each discovered README.md file to understand the project components.

## Phase 3: Identify Key Systems

Based on discovery, identify and document:

1. **Application Code**: Directories with package.json or web frameworks
2. **Backend/API**: Python projects, API directories
3. **Automation/Workflows**: Python scripts, CI/CD, automation tools
4. **Infrastructure**: Terraform, Packer, deployment configurations
5. **Documentation**: All README files and doc directories

## Phase 4: Generate Context Summary

After discovery and reading documentation, provide:

### Project Overview
- Project name and description (from root README or package.json)
- Primary technologies detected
- Key directories and their purposes

### Development Workflow
- How to run the application (from discovered package.json scripts)
- How to run tests
- Any automation workflows discovered

### Documentation Map
- List all README files and what they cover
- Point to relevant docs for specific tasks

### Available Commands
List discovered Claude commands:
```bash
ls .claude/commands/*.md 2>/dev/null | xargs -I {} basename {} .md
```

### Quick Reference
Based on discovered package.json scripts, pyproject.toml scripts, or Makefile targets:
```bash
# Show npm/bun scripts if package.json exists
cat package.json 2>/dev/null | grep -A 50 '"scripts"' | head -30 || echo "No package.json scripts"

# Show Python commands if pyproject.toml exists
cat pyproject.toml 2>/dev/null | grep -A 20 '\[project.scripts\]' || echo "No Python scripts defined"
```

---

## Context Summary Template

After completing discovery, summarize in this format:

```
## Project: [Name]

### Key Systems
| System | Directory | Technology | README |
|--------|-----------|------------|--------|
| [name] | [path]    | [tech]     | [link] |

### Quick Start
- Dev server: [command]
- Tests: [command]
- Build: [command]

### Documentation
- [path]: [description]

### Automation
- [workflow/script]: [description]

### Next Steps
1. Read [specific README] for [task type]
2. Use [command] to [action]
```

---

## Available Skills

List specialized skills for enhanced domain expertise:

```bash
bash .claude/commands/scripts/list_skills.sh 2>/dev/null || echo "No skills script found"
```

If skills are available, list them all for the user.
