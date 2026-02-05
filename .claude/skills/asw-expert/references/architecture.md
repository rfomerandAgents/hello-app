# ASW Architecture Reference

## System Overview

The Agentic Software Workflow (ASW) system automates both application development and infrastructure operations from GitHub issue to merged PR. It operates as a composable pipeline of Python scripts that orchestrate Claude Code CLI execution in isolated git worktrees.

The system is split into two workflow types:
- **ASW App**: Application development workflows (formerly ADWS)
- **ASW IO**: Infrastructure operations workflows (formerly IPE)

```
GitHub Issue
     |
     v
+---------------------------------------------------------------------+
|                     ASW Orchestration Layer                          |
|  +----------+  +----------+  +----------+  +----------+              |
|  |  Plan    |->|  Build   |->|  Test    |->|  Review  |-> ...        |
|  | Phase    |  | Phase    |  | Phase    |  | Phase    |              |
|  +----------+  +----------+  +----------+  +----------+              |
|       |             |             |             |                    |
|       +-------------+-------------+-------------+                    |
|                         |                                            |
|              ASWAppState / ASWIOState                                |
|        (agents/{id}/asw_app_state.json or asw_io_state.json)         |
+---------------------------------------------------------------------+
     |
     v
 Pull Request
```

## Directory Structure

```
{{PROJECT_DOMAIN}}/
+-- asw/                              # ASW system root
|   +-- app/                          # Application development workflows
|   |   +-- asw_app_plan_iso.py       # Plan phase script
|   |   +-- asw_app_build_iso.py      # Build phase script
|   |   +-- asw_app_test_iso.py       # Test phase script
|   |   +-- asw_app_review_iso.py     # Review phase script
|   |   +-- asw_app_document_iso.py   # Documentation phase
|   |   +-- asw_app_ship_iso.py       # Ship/deploy phase
|   |   +-- asw_app_patch_iso.py      # Direct patching
|   |   +-- asw_app_sdlc_iso.py       # Full SDLC orchestration
|   |   +-- asw_app_sdlc_zte_iso.py   # Zero Touch Execution
|   |   +-- asw_app_plan_build_iso.py # Plan + Build
|   |   +-- ...
|   |
|   +-- io/                           # Infrastructure operations workflows
|   |   +-- asw_io_plan_iso.py        # Infrastructure plan phase
|   |   +-- asw_io_build_iso.py       # Infrastructure build phase
|   |   +-- asw_io_build_ami_iso.py   # AMI build with Packer
|   |   +-- asw_io_test_iso.py        # Infrastructure test phase
|   |   +-- asw_io_review_iso.py      # Infrastructure review phase
|   |   +-- asw_io_document_iso.py    # Infrastructure documentation
|   |   +-- asw_io_ship_iso.py        # Infrastructure ship phase
|   |   +-- asw_io_deploy.py          # Terraform apply
|   |   +-- asw_io_destroy.py         # Terraform destroy
|   |   +-- asw_io_sdlc_iso.py        # Full SDLC for infrastructure
|   |   +-- ...
|   |
|   +-- modules/                      # Shared Python modules
|   |   +-- __init__.py
|   |   +-- agent.py                  # Claude Code CLI execution
|   |   +-- data_types.py             # Pydantic models and types
|   |   +-- git_ops.py                # Git operations
|   |   +-- github.py                 # GitHub API via gh CLI
|   |   +-- cache.py                  # Response caching
|   |   +-- state.py                  # ASWAppState and ASWIOState classes
|   |   +-- utils.py                  # Logging, ID generation
|   |   +-- workflow_ops.py           # High-level operations
|   |   +-- worktree_ops.py           # Worktree management
|   |
|   +-- tests/                        # Test suites
|   |   +-- app/                      # Application workflow tests
|   |   +-- io/                       # Infrastructure workflow tests
|   |
|   +-- triggers/                     # Automation triggers
|       +-- app/                      # App workflow triggers
|       |   +-- trigger_cron.py       # Polling-based monitoring
|       |   +-- trigger_webhook.py    # Webhook server
|       +-- io/                       # IO workflow triggers
|           +-- trigger_cron.py
|           +-- trigger_webhook.py
|
+-- agents/                           # Workflow outputs (per ASW ID)
|   +-- {asw_id}/
|       +-- asw_app_state.json        # App workflow state
|       +-- asw_io_state.json         # IO workflow state
|       +-- sdlc_planner/             # Plan phase outputs
|       |   +-- prompts/
|       |   |   +-- feature.txt       # Prompt sent to Claude
|       |   +-- raw_output.jsonl      # Claude response stream
|       +-- sdlc_implementor/         # Build phase outputs
|       +-- issue_classifier/         # Classification outputs
|       +-- reviewer/                 # Review phase outputs
|       |   +-- review_img/           # Screenshots
|       +-- cache/                    # Cached responses
|       +-- ...
|
+-- trees/                            # Isolated git worktrees
|   +-- {asw_id}/                     # Complete repo copy
|       +-- app/                      # Application code
|       +-- asw/                      # ASW code
|       +-- io/                       # Infrastructure code
|       +-- .ports.env                # Port configuration
|       +-- ...
|
+-- io/                               # Infrastructure code
|   +-- terraform/                    # Terraform configurations
|   +-- packer/                       # Packer templates
|   +-- docs/                         # Infrastructure documentation
|
+-- specs/                            # Specification files
|   +-- high-level/                   # Feature designs
|   +-- medium-level/                 # Implementation plans
|   +-- low-level/                    # Detailed implementation specs
|       +-- plan-{asw_id}-{slug}.md
|
+-- triggers/                         # Unified webhook router
|   +-- trigger_webhook.py            # Main router (port 8001)
|   +-- README.md
|
+-- .claude/
    +-- commands/                     # Slash commands used by ASW
        +-- classify_issue.md
        +-- classify_asw_app.md
        +-- classify_asw_io.md
        +-- generate_branch_name.md
        +-- feature.md
        +-- bug.md
        +-- chore.md
        +-- patch.md
        +-- implement.md
        +-- test.md
        +-- test_e2e.md
        +-- review.md
        +-- document.md
        +-- commit.md
        +-- pull_request.md
        +-- ...
```

## State Management

### ASW State Lifecycle

Both ASWAppState and ASWIOState follow a similar lifecycle:

```
+------------------+
|   New Issue      |
|   (no state)     |
+--------+---------+
         | ensure_asw_app_id() or ensure_asw_io_id()
         v
+------------------+
| State Created    |
| - asw_id         |
| - issue_number   |
+--------+---------+
         | Plan Phase
         v
+------------------+
| Planning Done    |
| - branch_name    |
| - plan_file      |
| - issue_class    |
| - worktree_path  |
| - backend_port   |
| - frontend_port  |
+--------+---------+
         | Build/Test/Review
         v
+------------------+
| Implementation   |
|   Complete       |
+--------+---------+
         | Ship Phase
         v
+------------------+
| Shipped          |
| - shipped_at     |
| - merge_commit   |
| - pr_number      |
+------------------+
```

### State File Formats

**App Workflow State:** `agents/{asw_id}/asw_app_state.json`

```json
{
  "asw_id": "abc12345",
  "issue_number": "42",
  "branch_name": "feature-issue-42-asw-abc12345-add-gallery",
  "plan_file": "specs/low-level/plan-abc12345-add-gallery.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/project/trees/abc12345",
  "backend_port": 9103,
  "frontend_port": 9203,
  "model_set": "base",
  "all_asws": ["abc12345"],
  "shipped_at": null,
  "merge_commit": null,
  "pr_number": null
}
```

**IO Workflow State:** `agents/{asw_id}/asw_io_state.json`

```json
{
  "asw_id": "xyz98765",
  "issue_number": "55",
  "branch_name": "feature-issue-55-asw-xyz98765-add-vpc",
  "plan_file": "specs/low-level/plan-xyz98765-add-vpc.md",
  "issue_class": "/feature",
  "worktree_path": "/path/to/project/trees/xyz98765",
  "model_set": "base",
  "all_asws": ["xyz98765"],
  "terraform_workspace": "dev",
  "plan_output_file": "io/terraform/plan.out",
  "ami_id": null,
  "infrastructure_type": "terraform",
  "shipped_at": null,
  "merge_commit": null,
  "pr_number": null
}
```

## Port Allocation Scheme

ASW uses deterministic port allocation to prevent conflicts between parallel workflows.

```
ASW ID -> Hash -> Index (0-14)
                    |
                    +---> Backend Port:  9100 + index
                    +---> Frontend Port: 9200 + index

Example:
  asw_id = "abc12345"
  index = hash("abc12345") % 15 = 3
  backend_port = 9103
  frontend_port = 9203
```

**Port Ranges:**
- Backend:  9100-9114 (15 slots)
- Frontend: 9200-9214 (15 slots)

If deterministic ports are in use, `find_next_available_ports()` scans for available slots.

## Worktree Isolation Model

Each ASW workflow executes in an isolated git worktree:

```
Main Repo                          Worktree (trees/abc12345/)
+-------------------+              +-------------------+
| branch: main      |              | branch: feature-42|
|                   |   git        |                   |
| app/              | <-worktree-> | app/              |
| asw/              |   add        | asw/              |
| io/               |              | io/               |
| specs/            |              | specs/            |
| .ports.env X      |              | .ports.env Y      |
+-------------------+              +-------------------+
```

**Benefits:**
- Parallel workflows don't interfere
- Main branch stays clean during development
- Each workflow has its own port configuration
- Easy cleanup after completion

## Data Flow

### Issue to PR Flow (App Workflow)

```
1. GitHub Issue Created
        |
        v
2. Webhook/Cron Detects Issue
        |
        v
3. extract_asw_info() parses /asw_app_* command
        |
        v
4. asw_app_plan_iso.py
   - Fetch issue from GitHub
   - Classify: /chore, /bug, /feature, /patch
   - Generate branch name
   - Create worktree in trees/{asw_id}/
   - Run planning command (/feature, /bug, etc.)
   - Save state
        |
        v
5. asw_app_build_iso.py
   - Load state
   - Run /implement in worktree
   - Create commit
   - Create PR
   - Post update to issue
        |
        v
6. asw_app_test_iso.py
   - Run unit tests
   - Run E2E tests
   - Auto-fix failures (up to 3 attempts)
        |
        v
7. asw_app_review_iso.py
   - Compare implementation to spec
   - Capture screenshots
   - Create patches if needed
        |
        v
8. asw_app_document_iso.py
   - Generate app_docs documentation
   - Update PR
        |
        v
9. asw_app_ship_iso.py
   - Merge PR
   - Trigger deployment
   - Clean up worktree
   - Update state with ship metadata
```

### Issue to PR Flow (IO Workflow)

```
1. GitHub Issue Created
        |
        v
2. Webhook/Cron Detects Issue
        |
        v
3. extract_asw_info() parses /asw_io_* command
        |
        v
4. asw_io_plan_iso.py
   - Fetch issue from GitHub
   - Classify issue type
   - Generate branch name
   - Create worktree
   - Run planning command
   - Save state with terraform_workspace
        |
        v
5. asw_io_build_iso.py
   - Load state
   - Run /implement in worktree
   - Run terraform init, validate, plan
   - Create commit
   - Create PR
   - Post update to issue
        |
        v
6. asw_io_test_iso.py
   - Run terraform validate
   - Run terraform plan (dry-run)
   - Run integration tests if applicable
        |
        v
7. asw_io_review_iso.py
   - Compare implementation to spec
   - Review terraform plan output
   - Create patches if needed
        |
        v
8. asw_io_document_iso.py
   - Generate infrastructure documentation
   - Update module READMEs
   - Update runbooks
        |
        v
9. asw_io_ship_iso.py
   - Merge PR
   - Optionally trigger asw_io_deploy.py
   - Clean up worktree
   - Update state
        |
        v
10. asw_io_deploy.py (optional)
    - Run terraform apply
    - Validate deployment
    - Update infrastructure state
```

### Agent Output Structure

Each phase writes to `agents/{asw_id}/{agent_name}/`:

```
agents/abc12345/sdlc_planner/
+-- prompts/
|   +-- feature.txt          # The prompt sent to Claude
+-- raw_output.jsonl          # Claude's streaming response
+-- raw_output.json           # Converted to JSON array

agents/abc12345/reviewer/
+-- prompts/
|   +-- review.txt
+-- raw_output.jsonl
+-- raw_output.json
+-- review_img/               # Screenshots from review
    +-- screenshot_1.png
    +-- screenshot_2.png

agents/abc12345/cache/        # Response caching
+-- classify_issue_hash.json
+-- implement_hash.json
```

## Claude Code Integration

### Execution Pattern

```python
# 1. Create request
request = AgentTemplateRequest(
    agent_name="sdlc_planner",
    slash_command="/feature",
    args=[issue_number, asw_id, issue_json],
    asw_id=asw_id,
    working_dir=worktree_path,
)

# 2. Execute with retry
response = execute_template(request)
# Internally calls: prompt_claude_code_with_retry()

# 3. Response parsed from JSONL
if response.success:
    result = response.output  # Extracted result text
else:
    error = response.output   # Error message
    retry_code = response.retry_code  # For retry decisions
```

### JSONL Output Format

Claude writes streaming responses:

```jsonl
{"type":"system","message":"Starting execution..."}
{"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
{"type":"tool_use","tool":"Edit","input":{...}}
{"type":"tool_result","output":"..."}
{"type":"result","result":"Final output","is_error":false,"session_id":"..."}
```

The `result` type message is extracted as the final output.

## Webhook Automation

### Unified Router Architecture

```
GitHub Webhook (port 443)
        |
        v
Cloudflare Tunnel
        |
        v
Unified Router (port 8001)
        |
        +-- Issue Event
        |   +-- Check for /asw_app_* or /asw_io_* command
        |       +-- ASW App: Spawn asw_app_*.py
        |       +-- ASW IO: Spawn asw_io_*.py
        |
        +-- Issue Comment Event
            +-- Check for /asw_app_* or /asw_io_* command
                +-- (same routing logic)
```

### Loop Prevention

Bot comments include workflow-specific identifiers:

```python
ASW_APP_BOT_IDENTIFIER = "[ASW-APP-AGENTS]"
ASW_IO_BOT_IDENTIFIER = "[ASW-IO-AGENTS]"

def format_issue_message(asw_id, agent_name, message, workflow_type="app"):
    identifier = ASW_APP_BOT_IDENTIFIER if workflow_type == "app" else ASW_IO_BOT_IDENTIFIER
    return f"{identifier} {asw_id}_{agent_name}: {message}"
```

Webhook router checks for these identifiers to skip processing bot-generated comments.

## Environment Configuration

### Required Environment Variables

```bash
# .env file
GITHUB_REPO_URL=https://github.com/owner/repo
CLAUDE_CODE_PATH=/path/to/claude
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-xxx
GITHUB_PAT=ghp_xxx  # Optional, uses gh auth by default

# R2 Storage (for screenshots)
CLOUDFLARE_R2_ACCESS_KEY_ID=xxx
CLOUDFLARE_R2_SECRET_ACCESS_KEY=xxx
CLOUDFLARE_R2_ENDPOINT_URL=xxx
CLOUDFLARE_R2_BUCKET_NAME=xxx
CLOUDFLARE_R2_PUBLIC_DOMAIN=xxx

# AWS (for IO workflows)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_DEFAULT_REGION=us-east-1

# Terraform Cloud (optional)
TF_CLOUD_TOKEN=xxx
TF_CLOUD_ORGANIZATION=xxx
```

### Worktree Port Configuration

Each worktree gets a `.ports.env` file:

```bash
# trees/{asw_id}/.ports.env
BACKEND_PORT=9103
FRONTEND_PORT=9203
VITE_BACKEND_URL=http://localhost:9103
```

## Migration from ADW/IPE

### Naming Changes

| Old Name | New Name |
|----------|----------|
| `adws/` | `asw/app/` |
| `ipe/` | `asw/io/` |
| `adw_modules/` | `asw/modules/` |
| `ipe_modules/` | `asw/modules/` |
| `ADWState` | `ASWAppState` |
| `IPEState` | `ASWIOState` |
| `adw_id` | `asw_id` |
| `ipe_id` | `asw_id` |
| `[ADW]` / `[IPE]` | `[ASW-APP-AGENTS]` / `[ASW-IO-AGENTS]` |

### Backward Compatibility

Legacy aliases are provided for gradual migration:
- `ADWState` = `ASWAppState`
- `IPEState` = `ASWIOState`
- `make_adw_id()` = `make_asw_app_id()`
- `make_ipe_id()` = `make_asw_io_id()`
