# Hello App

A simple Hello World web application built with the Agentic Template.

## Quick Start

```bash
# See all available commands
just

# Install dependencies (deterministic)
just init

# Install with agent validation
just install

# Interactive setup (asks questions)
just install-hil
```

Or use Claude Code directly:
```bash
claude --init "/install"
```

## The Pattern

This template implements the **install-and-maintain pattern** — combining deterministic scripts with agentic oversight:

```
┌─────────────────────────────────────────────────────────┐
│   DETERMINISTIC    →    AGENTIC    →    INTERACTIVE    │
│   (hooks)               (prompts)       (prompts)      │
│                                                         │
│   just init          just install    just install-hil  │
│   - Fast             - Supervised    - Asks questions  │
│   - CI-friendly      - Diagnostic    - Adapts          │
│   - Predictable      - Reports       - Context-aware   │
└─────────────────────────────────────────────────────────┘
```

## Core Systems

| System | Directory | Description |
|--------|-----------|-------------|
| 📱 Application | [`app/`](app/) | Your application code |
| 🤖 ASW App | [`asw/app/`](asw/README.md) | Agentic workflows for application development |
| 🏗️ ASW IO | [`asw/io/`](asw/README.md) | Agentic workflows for infrastructure operations |
| ⚙️ Modules | [`asw/modules/`](asw/modules/) | Shared automation modules |

## ASW - Agentic Software Workflow

The ASW system automates the full software development lifecycle:

**Plan → Build → Test → Review → Document → Ship**

### For Application Code (ASW App)

```bash
# Full SDLC workflow
just asw-app <issue-number>

# Or directly
uv run asw/app/asw_app_sdlc_iso.py <issue-number>
```

### For Infrastructure Code (ASW IO)

```bash
# Full SDLC workflow  
just asw-io <issue-number>

# Or directly
uv run asw/io/asw_io_sdlc_iso.py <issue-number>
```

### How It Works

1. **Issue-driven**: Point ASW at a GitHub issue
2. **Isolated worktrees**: Each workflow runs in `trees/<asw-id>/`
3. **State tracking**: Progress saved to `agents/<asw-id>/`
4. **Automatic PRs**: Creates PRs with semantic commits

## Commands (justfile)

| Command | Description |
|---------|-------------|
| `just` | List all commands |
| `just init` | Deterministic setup (CI-friendly) |
| `just install` | Agentic setup (validates + reports) |
| `just install-hil` | Interactive setup (asks questions) |
| `just maintain` | Agentic maintenance (checks updates) |
| `just asw-app <issue>` | Run app workflow for issue |
| `just asw-io <issue>` | Run infrastructure workflow |
| `just test` | Run all tests |
| `just health` | Check system health |

## Claude Code Commands

| Command | Description |
|---------|-------------|
| `/install` | Install dependencies and discover project |
| `/install true` | Interactive installation |
| `/prime` | Load project context |
| `/feature <issue>` | Implement a feature |
| `/bug <issue>` | Fix a bug |
| `/chore <issue>` | Maintenance task |
| `/maintenance` | Run maintenance checks |

## Project Structure

```
{{PROJECT_NAME_SLUG}}/
├── app/                      # Your application code
├── asw/                      # Agentic Software Workflow
│   ├── app/                  # Application workflows
│   │   ├── asw_app_sdlc_iso.py
│   │   └── ...
│   ├── io/                   # Infrastructure workflows
│   │   ├── asw_io_sdlc_iso.py
│   │   └── ...
│   └── modules/              # Shared modules
├── ipe/                      # Infrastructure code
│   ├── terraform/            # Terraform configurations
│   └── packer/               # Packer templates
├── .claude/
│   ├── commands/             # Claude Code commands
│   ├── hooks/                # Lifecycle hooks
│   │   ├── setup_init.py     # Init hook (claude --init)
│   │   └── setup_maintenance.py
│   └── skills/               # Project-local skills
├── .github/workflows/        # GitHub Actions
├── specs/                    # Feature specifications
├── app_docs/                 # Documentation
├── justfile                  # Command runner
└── README.md
```

## Getting Started with This Template

### 1. Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [just](https://github.com/casey/just) - Command runner
- [Claude Code](https://code.claude.com/) - AI coding assistant
- Node.js 18+ (if using frontend)
- Terraform (if using infrastructure)

### 2. Clone and Install

```bash
git clone {{GITHUB_REPO_URL}}
cd {{PROJECT_NAME_SLUG}}

# Run interactive setup
just install-hil
```

### 3. Replace Placeholders

Search and replace throughout the repository:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{PROJECT_NAME}}` | Project display name | "My App" |
| `{{PROJECT_NAME_SLUG}}` | Kebab-case identifier | "my-app" |
| `{{PROJECT_DESCRIPTION}}` | Brief description | "A web application for..." |
| `{{DOMAIN}}` | Your domain | "myapp.com" |
| `{{GITHUB_OWNER}}` | GitHub username/org | "myusername" |
| `{{GITHUB_REPO_URL}}` | Repository URL | "https://github.com/..." |
| `{{TF_ORGANIZATION}}` | Terraform Cloud org | "my-tf-org" |
| `{{TF_PROJECT}}` | Terraform Cloud project | "my-project" |

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Start Developing

```bash
# Load project context
claude "/prime"

# Start working on an issue
just asw-app <issue-number>
```

## Maintenance

```bash
# Check for updates and issues
just maintain

# Or directly
claude --maintenance "/maintenance"
```

Maintenance checks:
- Dependency updates (Python, Node.js)
- Security vulnerabilities (npm audit)
- Git status and sync
- Stale files and worktrees

## Infrastructure

### Terraform

```bash
# Deploy to development
just deploy-dev

# Or run ASW IO workflow
just asw-io <issue-number>
```

### Packer (AMI builds)

```bash
just build-ami
```

## Documentation

- **ASW System**: [asw/README.md](asw/README.md)
- **Application**: [app/README.md](app/README.md)
- **Infrastructure**: [ipe/terraform/README.md](ipe/terraform/README.md)
- **CI/CD**: [.github/workflows/README.md](.github/workflows/README.md)

## Links

- **Live**: [{{DOMAIN}}](https://{{DOMAIN}})
- **Repository**: [{{GITHUB_REPO_URL}}]({{GITHUB_REPO_URL}})
- **Actions**: [GitHub Actions]({{GITHUB_REPO_URL}}/actions)

---

Built with the [Agentic Template](https://github.com/rfomerand/agentic_template) — deterministic scripts + agentic oversight.
