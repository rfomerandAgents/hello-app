# Agentic Template - Command Runner
# https://github.com/casey/just
set dotenv-load := true

# List all recipes
default:
  @just --list

# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLATION & SETUP
# ═══════════════════════════════════════════════════════════════════════════════

# Deterministic codebase setup (CI-friendly, no agent)
init:
  claude --model opus --dangerously-skip-permissions --init

# Agentic codebase setup (hook + agent validates/reports)
install:
  claude --model opus --dangerously-skip-permissions --init "/install"

# Interactive codebase setup (agent asks questions)
install-hil:
  claude --model opus --dangerously-skip-permissions --init "/install true"

# ═══════════════════════════════════════════════════════════════════════════════
# MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════════════

# Deterministic maintenance (CI-friendly, no agent)
maintenance:
  claude --model opus --dangerously-skip-permissions --maintenance

# Agentic maintenance (hook + agent validates/reports)
maintain:
  claude --model opus --dangerously-skip-permissions --maintenance "/maintenance"

# ═══════════════════════════════════════════════════════════════════════════════
# DEVELOPMENT
# ═══════════════════════════════════════════════════════════════════════════════

# Prime the agent with codebase context
prime:
  claude --model opus "/prime"

# Start an interactive session with project context
start:
  claude --model opus "/start"

# ═══════════════════════════════════════════════════════════════════════════════
# ASW WORKFLOWS (Agentic Software Workflow)
# ═══════════════════════════════════════════════════════════════════════════════

# Run ASW App workflow for a GitHub issue
asw-app issue:
  uv run asw/app/asw_app_sdlc_iso.py {{issue}}

# Run ASW IO workflow for infrastructure
asw-io issue:
  uv run asw/io/asw_io_sdlc_iso.py {{issue}}

# Watch and auto-process GitHub issues
watch-issues:
  uv run shared/watch_issue.py

# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

# Run all tests
test:
  uv run pytest -v

# Run tests with coverage
test-cov:
  uv run pytest --cov=. --cov-report=html

# ═══════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE (Terraform/Packer)
# ═══════════════════════════════════════════════════════════════════════════════

# Deploy to development environment
deploy-dev:
  cd ipe/terraform && terraform init && terraform apply -auto-approve -var-file="envs/dev.tfvars"

# Build AMI with Packer
build-ami:
  cd ipe/packer && packer build .

# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════

# Reset installation artifacts (for retesting)
reset:
  rm -rf .venv
  rm -rf node_modules
  rm -rf .claude/hooks/*.log
  rm -rf app_docs/install_results.md
  rm -rf app_docs/maintenance_results.md

# Clean up worktrees
cleanup-worktrees:
  claude --model opus "/cleanup_worktrees"

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

# Show health status
health:
  claude --model opus "/health_check"

# Track agentic KPIs
kpis:
  claude --model opus "/track_agentic_kpis"
