# Infrastructure Platform Engineer (IPE) Workflows

This directory contains the Infrastructure Platform Engineer (IPE) workflow system for managing Terraform infrastructure and AMI builds using isolated git worktrees and AI-assisted development.

## Overview

IPE provides a composable workflow system that follows the Software Development Lifecycle (SDLC) pattern:
- **Plan**: Create implementation plans for infrastructure changes
- **Build**: Implement Terraform code or build AMIs
- **Test**: Validate infrastructure and run tests
- **Review**: Code review and approval
- **Document**: Generate documentation
- **Ship**: Deploy infrastructure changes

## Core Scripts

### Planning Phase

#### `ipe_plan_iso.py`
Creates isolated worktree and generates implementation plan for infrastructure changes.

```bash
uv run ipe/ipe_plan_iso.py <issue-number> <ipe-id>
```

**Prerequisites:**
- GitHub issue with infrastructure requirements
- GitHub CLI authenticated

**Creates:**
- Git worktree at `trees/<ipe-id>/`
- Implementation plan in `specs/low-level/`
- IPE state in `agents/<ipe-id>/ipe_state.json`

### Build Phase

#### `ipe_build_iso.py`
Implements Terraform infrastructure code in isolated worktree.

```bash
uv run ipe/ipe_build_iso.py <issue-number> <ipe-id>
```

**Prerequisites:**
- Requires `ipe_plan_iso.py` to have run first
- IPE state must exist

**Performs:**
- Implements Terraform code based on plan
- Runs `terraform fmt -recursive`
- Runs `terraform validate` (non-blocking)
- Commits and pushes changes

#### `ipe_build_ami_iso.py` (NEW)
Triggers GitHub Actions AMI builds from isolated worktree context.

```bash
uv run ipe/ipe_build_ami_iso.py <issue-number> <ipe-id>
```

**Prerequisites:**
- Requires `ipe_plan_iso.py` to have run first
- IPE state must exist with `environment` and `branch_name`
- GitHub CLI authenticated

**Workflow:**
1. Loads IPEState and validates worktree
2. Extracts environment and version from state
3. Triggers `infrastructure-deploy.yml` in `build-ami-only` mode
4. Polls GitHub Actions until completion
5. Extracts AMI ID from artifacts
6. Saves results to `agents/<ipe-id>/ami_build_result.json`
7. Posts updates to GitHub issue

**State Requirements:**
- `branch_name`: Git branch to build from (required)
- `environment`: dev, staging, or prod (required)
- `worktree_path`: Path to worktree (required)
- `issue_number`: GitHub issue for updates (required)
- `ami_version`: Custom AMI version (optional)
- `version_strategy`: git-describe, semantic, commit-hash, or timestamp (optional, default: git-describe)
- `build_timeout`: Build timeout in minutes (optional, default: 45)

**Outputs:**
- AMI build results in `agents/<ipe-id>/ami_build_result.json`:
  ```json
  {
    "ami_id": "ami-xxxxx",
    "ami_name": "my-app-v1.0.0",
    "ami_version": "v1.0.0",
    "run_id": "12345",
    "run_url": "https://github.com/owner/repo/actions/runs/12345",
    "environment": "dev",
    "duration_seconds": 600,
    "timestamp": 1234567890.0,
    "success": true
  }
  ```

**Behavioral Differences from `ipe_build.py`:**
- **State Management**: Uses full IPEState vs CLI args only
- **GitHub Integration**: Posts issue comments vs none
- **Branch Selection**: Uses state.branch_name vs --branch flag
- **Workflow Chaining**: Part of SDLC chain vs standalone
- **Error Handling**: Posts to GitHub issues + state vs exit codes only
- **Execution Context**: Runs in isolated worktree vs main repo

**Integration with Other Workflows:**
- Can be called directly: `uv run ipe/ipe_build_ami_iso.py 123 ipe-abc123`
- Or via webhook: Comment `ipe_build_ami_iso` on GitHub issue
- Typically follows `ipe_plan_iso.py` in workflow chain
- AMI results can be used by `ipe_deploy.py` for deployment

**Error Handling:**
- Posts errors to GitHub issue with IPE ID
- Saves partial state on failure
- Provides clear error messages with remediation steps
- GitHub CLI auth failures detected early

**Example Workflow Chain:**
```bash
# 1. Plan the infrastructure
uv run ipe/ipe_plan_iso.py 123 ipe-abc123

# 2. Build the AMI (if needed)
uv run ipe/ipe_build_ami_iso.py 123 ipe-abc123

# 3. Implement Terraform
uv run ipe/ipe_build_iso.py 123 ipe-abc123

# 4. Test the infrastructure
uv run ipe/ipe_test_iso.py 123 ipe-abc123

# 5. Deploy
uv run ipe/ipe_deploy.py deploy --ami-id=ami-xxxxx
```

### Standalone Build

#### `ipe_build.py`
Standalone GitHub Actions AMI builder (non-worktree).

```bash
# Build with defaults
uv run ipe/ipe_build.py --environment=dev

# Build with custom version
uv run ipe/ipe_build.py --version=v2.0.0 --environment=staging

# Build without waiting
uv run ipe/ipe_build.py --no-wait --environment=prod
```

**Options:**
- `--version=<version>`: Custom AMI version
- `--version-strategy=<strategy>`: git-describe, semantic, commit-hash, timestamp
- `--environment=<env>`: dev, staging, prod (default: dev)
- `--branch=<branch>`: Git branch to build from (default: main)
- `--wait` / `--no-wait`: Wait for build completion (default: --wait)
- `--timeout=<minutes>`: Build timeout in minutes (default: 45)
- `--poll-interval=<seconds>`: Status poll interval (default: 15)
- `--ipe-id=<id>`: IPE workflow ID for tracking
- `--output-format=<format>`: json or text (default: text)

## Full SDLC Workflow

### `ipe_sdlc_iso.py`
Runs complete SDLC workflow in isolated worktree.

```bash
uv run ipe/ipe_sdlc_iso.py <issue-number>
```

**Phases:**
1. Plan: Generate implementation plan
2. Build: Implement Terraform code
3. Test: Validate infrastructure
4. Review: AI-assisted code review
5. Document: Generate documentation
6. Ship: Deploy to environment

## Deployment

### `ipe_deploy.py`
Deploy infrastructure using Terraform.

```bash
# Deploy with specific AMI
uv run ipe/ipe_deploy.py deploy --ami-id=ami-xxxxx

# Plan only
uv run ipe/ipe_deploy.py plan --environment=staging
```

### `ipe_destroy.py`
Destroy infrastructure (destructive operation).

```bash
uv run ipe/ipe_destroy.py <environment>
```

**Warning:** This is a destructive operation. Use with caution.

## State Management

IPE uses persistent state stored in `agents/<ipe-id>/ipe_state.json`:

```json
{
  "ipe_id": "abc12345",
  "issue_number": "123",
  "branch_name": "ipe/abc12345-feature",
  "spec_file": "specs/low-level/plan-feature.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/trees/abc12345",
  "environment": "dev",
  "terraform_dir": "io/terraform/environments/dev",
  "model_set": "base",
  "all_ipes": ["ipe_plan_iso", "ipe_build_ami_iso", "ipe_build_iso"]
}
```

## Webhook Integration

All IPE workflows can be triggered via GitHub issue comments using the webhook system:

```
# Trigger via comment
ipe_plan_iso
ipe_build_ami_iso
ipe_build_iso
ipe_test_iso
ipe_sdlc_iso
```

**Workflow Detection Order:**
Workflows are detected by specificity (longest/most-specific first) to prevent substring matching bugs:
1. `ipe_sdlc_iso`
2. `ipe_document_iso`
3. `ipe_build_ami_iso` (NEW - must come before `ipe_build_iso`)
4. `ipe_review_iso`
5. `ipe_build_iso`
6. `ipe_test_iso`
7. `ipe_plan_iso`
8. `ipe_ship_iso`
9. `ipe_patch_iso`
10. `ipe_destroy`
11. `ipe_deploy`

## Module Structure

### `ipe_modules/`
Shared modules for IPE workflows:

- `ipe_state.py`: State management with file persistence
- `ipe_worktree_ops.py`: Git worktree operations
- `ipe_github.py`: GitHub API interactions
- `ipe_git_ops.py`: Git operations (commit, push, PR)
- `ipe_utils.py`: Utility functions and logging
- `ipe_workflow_ops.py`: Workflow orchestration
- `ipe_data_types.py`: Pydantic models for type safety
- `terraform_ops.py`: Terraform-specific operations
- `ipe_aws_ops.py`: AWS operations
- `ipe_packer_ops.py`: Packer operations

## Environment Variables

Required environment variables:
- `GITHUB_PAT`: GitHub Personal Access Token
- `CLAUDE_CODE_OAUTH_TOKEN`: Claude API key

Optional:
- `AWS_ACCESS_KEY_ID`: AWS credentials for infrastructure operations
- `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AWS_REGION`: Default AWS region

## Testing

Each IPE workflow includes comprehensive error handling:
- GitHub CLI authentication checks
- Worktree validation
- State validation
- GitHub issue updates on success/failure

## Architecture

IPE follows the composable architecture pattern:
1. **Isolated Execution**: Each workflow runs in isolated git worktree
2. **State Persistence**: All state persists to filesystem
3. **GitHub Integration**: Progress updates posted to issues
4. **AI Assistance**: Claude integration for planning and implementation
5. **Terraform Focus**: Infrastructure-as-Code with Terraform
6. **AMI Building**: GitHub Actions + Packer for AMI creation

## Differences from ADW

While IPE is similar to ADW (Application Development Workflow), it has key differences:

| Feature | ADW | IPE |
|---------|-----|-----|
| Focus | Application code | Infrastructure code |
| Primary Language | Python, TypeScript | Terraform (HCL) |
| Build Output | Application artifacts | Infrastructure + AMIs |
| Formatting | Language-specific | `terraform fmt` |
| Validation | Linters, tests | `terraform validate`, `terraform plan` |
| Deployment | Application deploy | Infrastructure provisioning |

## Common Issues

### GitHub CLI Not Authenticated
```bash
gh auth login
```

### Worktree Already Exists
```bash
# Remove old worktree
git worktree remove trees/<ipe-id>
```

### AMI Build Timeout
Increase timeout in state or via command line:
```json
{
  "build_timeout": 60
}
```

## Examples

### Build AMI for Development
```bash
# Via isolated workflow
uv run ipe/ipe_plan_iso.py 123 ipe-dev001
uv run ipe/ipe_build_ami_iso.py 123 ipe-dev001

# Via standalone
uv run ipe/ipe_build.py --environment=dev
```

### Deploy Infrastructure
```bash
# Build AMI first
uv run ipe/ipe_build_ami_iso.py 123 ipe-staging001

# Deploy with AMI
uv run ipe/ipe_deploy.py deploy --ami-id=ami-xxxxx --environment=staging
```

### Full SDLC Workflow
```bash
# Run complete workflow
uv run ipe/ipe_sdlc_iso.py 123

# Or trigger via GitHub issue comment
# Comment: ipe_sdlc_iso
```

## Contributing

When adding new IPE workflows:
1. Follow the `*_iso.py` naming convention for worktree-based workflows
2. Update `AVAILABLE_IPE_WORKFLOWS` in `triggers/trigger_webhook.py`
3. Add to `IPE_DEPENDENT_WORKFLOWS` if it requires IPE ID
4. Update this README with usage examples
5. Include comprehensive docstrings
6. Add state validation
7. Post updates to GitHub issues

## Support

For issues or questions:
- Check the execution logs in `agents/<ipe-id>/*/execution.log`
- Review state in `agents/<ipe-id>/ipe_state.json`
- Check GitHub issue comments for workflow progress
- Verify GitHub CLI authentication: `gh auth status`
