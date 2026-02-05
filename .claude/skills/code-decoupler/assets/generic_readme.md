# {{PROJECT_NAME}} - Project Repository

A comprehensive repository containing the {{PROJECT_NAME}} application and AI Developer Workflow (ADW) automation system.

## Project Components

### 📱 {{PROJECT_NAME}} Application (`app/`)
{{PROJECT_DESCRIPTION}}

**Features:**
- 🎨 Modern, responsive design
- 📱 Fully responsive (mobile, tablet, desktop)
- ⚡ Optimized for fast deployment
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

### Manual Installation

#### {{PROJECT_NAME}} Application

```bash
cd app/
bun install
# or
npm install
```

Start development server:
```bash
bun dev
# or
npm run dev
```

Visit [http://localhost:{{APP_PORT}}](http://localhost:{{APP_PORT}})

#### AI Developer Workflow

```bash
cd adws/
uv sync --all-extras
```

See [`adws/README.md`](adws/README.md) for usage instructions.

## Development

### {{PROJECT_NAME}} Application Commands

```bash
cd app/

# Development
bun dev                    # Start dev server with hot reload
npm run dev                # Alternative with npm

# Production
bun run build             # Build static export
npm run build             # Alternative with npm

# Linting
bun run lint              # Run Next.js linter
npm run lint              # Alternative with npm
```

### Adding Content to Application

1. **Add Assets**: Place files in `app/public/`
2. **Update Components**: Edit components in `app/components/`
3. **Customize Styles**: Modify `app/globals.css` or `app/tailwind.config.js`

See [`app/README.md`](app/README.md) for detailed documentation.

## Build and Deployment Pipeline

### GitHub Actions Deployment Workflows (Recommended)

The project uses automated GitHub Actions workflows for streamlined deployments with intelligent caching and better reliability.

[![App Deploy]({{GITHUB_REPO_URL}}/actions/workflows/app-build-deploy.yml/badge.svg)]({{GITHUB_REPO_URL}}/actions/workflows/app-build-deploy.yml)

#### Quick Deployment

**Automated (Recommended):**
```bash
# Push to a branch ending in '-deploy' to trigger deployment
git checkout -b main-deploy
git push origin main-deploy
```

**Manual via GitHub UI:**
1. Go to repository → Actions tab
2. Select "App Build and Deploy"
3. Click "Run workflow"
4. Select environment and run

#### Deployment Workflows

**1. App Build and Deploy** (`.github/workflows/app-build-deploy.yml`)
- Triggered by push to `*-deploy` branches or manual dispatch
- Builds application, creates AMI, deploys infrastructure, updates DNS
- **Performance:** 4-5 minutes (cached), 8-10 minutes (cold build)

**2. Infrastructure Deploy** (`.github/workflows/infrastructure-deploy.yml`)
- Manual only, flexible deployment modes:
  - **deploy** - Build new AMI and deploy
  - **deploy-latest-ami** - Reuse most recent AMI
  - **deploy-custom-ami** - Specify AMI ID
  - **plan-only** - Preview changes without applying
- **Performance:** 2-3 minutes (AMI reuse), 8-10 minutes (new AMI)

**3. Destroy Infrastructure** (`.github/workflows/destroy-infrastructure.yml`)
- Manual only, requires typing "DESTROY" to confirm
- Safely removes all infrastructure resources
- Optional AMI and snapshot cleanup

#### Required Secrets

Configure these in GitHub Settings → Secrets and variables → Actions:
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `CLOUDFLARE_API_TOKEN` - Cloudflare API token for DNS (if using)
- `CLOUDFLARE_ZONE_ID` - Zone ID for your domain (if using)
- `SSH_PUBLIC_KEY` - SSH key for EC2 access
- `TF_API_TOKEN` - Terraform Cloud API token

### Manual Deployment with Git Worktrees

Anytime a code change is made to the application, the deployment pipeline ensures quality and validates the infrastructure before going live. All Packer and Terraform operations are automatically executed within isolated git worktrees to prevent conflicts and keep your main branch clean.

**Infrastructure State Management:** This project uses **Terraform Cloud** for remote state management. State is stored securely in the cloud with encryption, state locking, and audit logs. See [`io/terraform/README.md`](io/terraform/README.md) for Terraform Cloud configuration details.

### Git Worktrees for Isolated Operations

All build, deploy, and destroy operations run in dedicated git worktrees:

- **Isolation**: Each operation has its own worktree directory (`.worktrees/<operation-name>`)
- **No Conflicts**: Main working directory remains unchanged during long-running operations
- **Parallel Operations**: Multiple builds/deploys can run simultaneously
- **Automatic Cleanup**: Successful operations automatically remove their worktrees
- **Debug Support**: Failed operations keep worktrees for investigation

**Key Points:**
- Worktrees are automatically created and managed by the scripts
- `.worktrees/` directory is in `.gitignore` (never committed)
- View active worktrees: `git worktree list`
- Clean up failed worktrees: `git worktree remove .worktrees/<operation-name>`

See [`io/terraform/README.md`](io/terraform/README.md) for detailed worktree management instructions.

## Project Structure

```
{{PROJECT_NAME_SLUG}}/      # Project root
├── app/                    # {{PROJECT_NAME}} Application
│   ├── app/                # Application directory
│   │   ├── globals.css     # Styles and theme
│   │   ├── layout.tsx      # Root layout with metadata
│   │   └── page.tsx        # Home page
│   ├── components/         # React components
│   ├── public/             # Public assets
│   ├── README.md           # Application documentation
│   ├── package.json        # Dependencies
│   ├── next.config.js      # Next.js configuration
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   └── tsconfig.json       # TypeScript configuration
│
├── adws/                   # AI Developer Workflow System
│   ├── adw_*.py            # Workflow scripts
│   ├── adw_modules/        # Core modules
│   │   ├── agent.py        # Agent orchestration
│   │   ├── git_ops.py      # Git operations
│   │   ├── github.py       # GitHub API integration
│   │   ├── workflow_ops.py # Workflow operations
│   │   └── worktree_ops.py # Git worktree management
│   ├── adw_triggers/       # Webhook & cron triggers
│   └── adw_tests/          # Test suite
│
├── ipe/                    # Infrastructure Platform Engineer
│   ├── ipe_*.py            # IPE workflow scripts
│   └── ipe_modules/        # Core modules
│
├── .claude/
│   ├── commands/           # Claude Code CLI commands
│   │   ├── install.md      # Installation command
│   │   ├── prime.md        # Project primer
│   │   ├── bug.md          # Bug workflow
│   │   ├── feature.md      # Feature workflow
│   │   └── chore.md        # Chore workflow
│   ├── hooks/              # Custom hooks
│   ├── skills/             # Project-local skills
│   └── settings.json       # Claude Code configuration
│
├── io/terraform/              # Infrastructure as Code
│   ├── main.tf             # Main infrastructure
│   ├── variables.tf        # Input variables
│   ├── outputs.tf          # Output values
│   ├── terraform.tf        # Backend configuration
│   ├── io/packer/             # Packer AMI templates
│   └── scripts/            # Deployment scripts
│
├── app_docs/               # Documentation
├── mcp/                    # MCP server configurations
├── logs/                   # Session logs
├── specs/                  # Feature specifications
├── .env                    # Environment variables
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Documentation

- **[app/README.md](app/README.md)** - Comprehensive application documentation
- **[adws/README.md](adws/README.md)** - AI Developer Workflow documentation
- **[ipe/README.md](ipe/README.md)** - Infrastructure Platform Engineer documentation
- **[io/terraform/README.md](io/terraform/README.md)** - Terraform infrastructure documentation

## AI Developer Workflow (ADW)

The ADW system is a comprehensive automation framework that integrates GitHub issues with Claude Code CLI to classify issues, generate implementation plans, and automatically create pull requests.

### Prerequisites

- **GitHub CLI**: `brew install gh` (macOS) or equivalent
- **Claude Code CLI**: Install from [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
- **Python with uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **GitHub authentication**: `gh auth login`

### Environment Variables

```bash
export GITHUB_REPO_URL="{{GITHUB_REPO_URL}}"
export CLAUDE_CODE_OAUTH_TOKEN="your-claude-token-here"
export GITHUB_PAT="your-github-pat-here"
```

### Usage Modes

#### 1. Manual Processing
```bash
cd adws/
uv run adw_plan_build_iso.py <issue-number>
```

#### 2. Automated Monitoring
```bash
cd adws/
uv run trigger_cron.py
```

#### 3. Webhook Server
```bash
cd adws/
uv run trigger_webhook.py
```

### How ADW Works

1. **Issue Classification**: Analyzes GitHub issues and determines type (`/chore`, `/bug`, `/feature`)
2. **Planning**: Generates detailed implementation plans using Claude Code CLI
3. **Implementation**: Executes the plan by making code changes
4. **Integration**: Creates git commits and pull requests

For more information, see [`adws/README.md`](adws/README.md).

## Infrastructure Platform Engineer Workflow (IPE)

The IPE system extends the ADW pattern to Terraform infrastructure code.

### Key Features

- 🏗️ Terraform Workflows: Automated plan, test, and ship
- 🔒 Safety First: Default manual apply mode
- 🧪 Comprehensive Testing: Terraform validate, tflint, security scanning
- 🌳 Worktree Isolation: Each workflow runs in isolated git worktree

### Workflows

#### Test Infrastructure (Safe - Read Only)
```bash
cd ipe/
uv run ipe_test_iso.py <issue-number> <workflow-id>
```

#### Ship Infrastructure (Manual Apply)
```bash
uv run ipe_ship_iso.py <issue-number> <workflow-id>
```

For more information, see [`ipe/README.md`](ipe/README.md).

## Customizing This Template

After cloning this template, customize the following:

### 1. Replace Placeholders

Search and replace these placeholders throughout the repository:

- `{{PROJECT_NAME}}` - Your project name (e.g., "My App")
- `{{PROJECT_NAME_SLUG}}` - Kebab-case identifier (e.g., "my-app")
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

## Troubleshooting

### Application Issues

**Development server won't start:**
- Check Node.js version: `node --version` (requires 18+)
- Clear dependencies: `rm -rf node_modules && npm install`
- Check port is available: `lsof -i :{{APP_PORT}}`

**Build errors:**
- Verify all dependencies installed
- Check for TypeScript errors: `npm run lint`
- Clear build cache: `rm -rf .next`

### AI Developer Workflow Issues

**ADWS errors:**
- Verify GitHub CLI authenticated: `gh auth status`
- Check environment variables are set
- Ensure Python 3.10+: `python --version`
- Verify Claude Code CLI installed: `claude --version`

### Infrastructure Issues

**Terraform deployment fails:**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify Terraform Cloud token is set
- Review Terraform logs

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
