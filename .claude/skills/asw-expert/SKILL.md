---
name: asw-expert
description: Expert ASW engineer for analyzing, troubleshooting, and improving the Agentic Software Workflow system. Use when debugging ASW workflows (both app and io), optimizing phase execution, implementing new workflow patterns, improving state management, or enhancing webhook automation. Covers application development (asw/app) and infrastructure operations (asw/io) workflows. Provides opinionated best practices and improvement suggestions.
---

# ASW Expert

Expert guidance from a senior ASW engineer who has architected and maintained the Agentic Software Workflow system. Deep knowledge of composable workflows for both application development (ASW App) and infrastructure operations (ASW IO), state management patterns, Claude Code CLI integration, and isolated worktree execution.

## Engineering Philosophy

**"Automation should be invisible until it fails. When it fails, diagnostics should be crystal clear."**

### Core Beliefs

1. **State is sacred** - Every workflow step must persist state; lost state means lost work
2. **Isolation prevents disasters** - Worktrees keep parallel workflows from corrupting each other
3. **Fail loudly, recover gracefully** - RetryCode patterns enable automatic recovery
4. **Composability over monoliths** - Small, focused scripts that chain together beat one giant script
5. **Claude Code is a subprocess** - Treat it like any external process: timeouts, retries, output parsing
6. **Bot identifiers prevent loops** - Every automated comment must include `[ASW-APP-AGENTS]` or `[ASW-IO-AGENTS]` to prevent webhook recursion
7. **Plans are contracts** - The spec file is the source of truth between plan and implementation phases
8. **Ports are precious** - Deterministic port allocation (9100-9114, 9200-9214) prevents conflicts

---

## ASW Module Deep-Dive

### `asw/modules/state.py` - The State Containers

The ASW system provides two state classes for different workflow types:

**`ASWAppState`** - For application development workflows
**`ASWIOState`** - For infrastructure operations workflows

**Key Fields (both share similar structure):**
```python
{
    "asw_id": str,           # Unique 8-char workflow ID
    "issue_number": str,     # GitHub issue being processed
    "branch_name": str,      # Git branch for this workflow
    "plan_file": str,        # Path to specification file
    "issue_class": str,      # "/chore", "/bug", "/feature", "/patch"
    "worktree_path": str,    # Absolute path to isolated worktree
    "backend_port": int,     # Port 9100-9114
    "frontend_port": int,    # Port 9200-9214
    "model_set": str,        # "base" or "heavy"
    "all_asws": List[str],   # Tracking for multi-ASW orchestration
    "shipped_at": str,       # ISO timestamp when shipped
    "merge_commit": str,     # Git commit hash of merge
    "pr_number": str,        # PR number that was merged
}
```

**IO-Specific State Fields:**
```python
{
    "terraform_workspace": str,   # Active Terraform workspace
    "plan_output_file": str,      # Path to terraform plan output
    "ami_id": str,                # Built AMI ID (for Packer workflows)
    "infrastructure_type": str,   # "terraform" or "packer"
}
```

**State File Locations:**
```
agents/{asw_id}/asw_app_state.json  # App workflows
agents/{asw_id}/asw_io_state.json   # IO workflows
```

**Critical Methods:**
- `state.get_working_directory()` - Returns worktree path if set, else main repo
- `state.save(workflow_step)` - Persist to appropriate state file
- `ASWAppState.load(asw_id, logger)` / `ASWIOState.load(asw_id, logger)` - Restore state from disk
- `state.update(**kwargs)` - Update state with core fields only

### `asw/modules/agent.py` - Claude Code Execution

Handles all Claude Code CLI interactions with retry logic and output parsing.

**Key Functions:**
- `execute_template(request)` - Execute slash command with automatic model selection
- `prompt_claude_code_with_retry(request, max_retries=3)` - Auto-retry on transient errors
- `get_claude_env()` - Build safe subprocess environment from `.env`
- `parse_jsonl_output(output_file)` - Extract result from Claude's JSONL stream

**Model Selection:**
The `SLASH_COMMAND_MODEL_MAP` maps each command to models by set:
```python
{
    "/implement": {"base": "sonnet", "heavy": "opus"},
    "/review": {"base": "sonnet", "heavy": "opus"},
    # ... etc
}
```

### `asw/modules/workflow_ops.py` - Core Operations

High-level workflow operations that orchestrate the SDLC phases.

**Key Functions:**
- `classify_issue(issue, asw_id, logger)` - Determine issue type via `/classify_issue`
- `build_plan(issue, command, asw_id, logger, working_dir)` - Execute planning slash command
- `implement_plan(plan_file, asw_id, logger, working_dir)` - Execute `/implement`
- `create_commit(agent_name, issue, issue_class, asw_id, logger, working_dir)` - Git commit
- `create_pull_request(branch, issue, state, logger, working_dir)` - PR creation
- `format_issue_message(asw_id, agent_name, message)` - Format with bot identifier

**Available ASW App Workflows (ordered by specificity):**
```python
AVAILABLE_ASW_APP_WORKFLOWS = [
    "asw_app_plan_build_test_review_iso",
    "asw_app_plan_build_document_iso",
    "asw_app_plan_build_review_iso",
    "asw_app_plan_build_test_iso",
    "asw_app_plan_build_iso",
    "asw_app_sdlc_ZTE_iso",
    "asw_app_sdlc_iso",
    "asw_app_document_iso",
    "asw_app_review_iso",
    "asw_app_build_iso",
    "asw_app_patch_iso",
    "asw_app_test_iso",
    "asw_app_plan_iso",
    "asw_app_ship_iso",
]
```

**Available ASW IO Workflows:**
```python
AVAILABLE_ASW_IO_WORKFLOWS = [
    "asw_io_plan_build_test_review_iso",
    "asw_io_plan_build_document_iso",
    "asw_io_plan_build_review_iso",
    "asw_io_plan_build_test_iso",
    "asw_io_plan_build_iso",
    "asw_io_sdlc_ZTE_iso",
    "asw_io_sdlc_iso",
    "asw_io_document_iso",
    "asw_io_review_iso",
    "asw_io_build_iso",
    "asw_io_build_ami_iso",
    "asw_io_patch_iso",
    "asw_io_test_iso",
    "asw_io_plan_iso",
    "asw_io_ship_iso",
    "asw_io_deploy",
    "asw_io_destroy",
]
```

### `asw/modules/worktree_ops.py` - Isolation Management

Git worktree creation and port allocation.

**Key Functions:**
- `create_worktree(asw_id, branch_name, logger)` - Create isolated `trees/{asw_id}/`
- `validate_worktree(asw_id, state)` - Three-way validation (state, filesystem, git)
- `get_ports_for_asw(asw_id)` - Deterministic port assignment
- `find_next_available_ports(asw_id)` - Fall back if ports in use
- `setup_worktree_environment(path, backend_port, frontend_port)` - Create `.ports.env`

**Port Allocation:**
```
Backend:  9100-9114 (15 slots)
Frontend: 9200-9214 (15 slots)
Mapping:  hash(asw_id) % 15 -> slot index
```

### `asw/modules/data_types.py` - Type Definitions

Pydantic models for type safety and validation.

**Core Types:**
- `ASWAppStateData` / `ASWIOStateData` - State persistence schemas
- `AgentPromptRequest` / `AgentPromptResponse` - Claude Code I/O
- `AgentTemplateRequest` - Slash command execution request
- `GitHubIssue`, `GitHubComment` - GitHub API models
- `ReviewResult`, `ReviewIssue` - Review workflow output
- `RetryCode` - Error categorization for retry logic

**Literals:**
```python
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature", "/patch"]
ModelSet = Literal["base", "heavy"]
ASWAppWorkflow = Literal["asw_app_plan_iso", "asw_app_build_iso", ...]
ASWIOWorkflow = Literal["asw_io_plan_iso", "asw_io_build_iso", ...]
```

### `asw/modules/github.py` - GitHub Integration

GitHub API operations via `gh` CLI.

**Key Functions:**
- `get_issue(issue_number)` - Fetch issue with comments
- `add_issue_comment(issue_number, comment)` - Post comment
- `create_pr(branch, title, body)` - Create pull request
- `get_repo_url()` / `extract_repo_path()` - Repository info

**Bot Identifiers:**
```python
ASW_APP_BOT_IDENTIFIER = "[ASW-APP-AGENTS]"  # Prevents webhook loops for app workflows
ASW_IO_BOT_IDENTIFIER = "[ASW-IO-AGENTS]"    # Prevents webhook loops for io workflows
```

### `asw/modules/utils.py` - Utilities

Common utilities shared across modules.

**Key Functions:**
- `make_asw_app_id()` / `make_asw_io_id()` - Generate 8-char unique IDs
- `get_safe_subprocess_env()` - Build minimal subprocess environment
- `setup_logging(asw_id, script_name)` - Configure file + console logging
- `parse_json(text, expected_type)` - Extract JSON from markdown code blocks

### `asw/modules/git_ops.py` - Git Operations

Git operations for branch and commit management.

**Key Functions:**
- `get_current_branch(cwd)` - Get current branch name
- `create_branch(branch_name, cwd)` - Create and checkout branch
- `push_branch(branch_name, cwd)` - Push to origin

---

## Workflow Phase Analysis

### Plan Phase (`asw_app_plan_iso.py` / `asw_io_plan_iso.py`)

**Purpose:** Create specification file from GitHub issue

**Flow:**
1. Fetch issue from GitHub
2. Classify issue -> `/chore`, `/bug`, `/feature`, `/patch`
3. Generate branch name -> `{type}-issue-{num}-asw-{id}-{slug}`
4. Create worktree in `trees/{asw_id}/`
5. Execute planning command in worktree
6. Save state with `plan_file`, `branch_name`, `worktree_path`

**Output:** `specs/low-level/plan-{id}-{slug}.md`

### Build Phase (`asw_app_build_iso.py` / `asw_io_build_iso.py`)

**Purpose:** Implement the specification

**Dependencies:** Requires plan phase state

**Flow:**
1. Load state, validate worktree exists
2. Execute `/implement {plan_file}` in worktree
3. Create commit via `/commit` command
4. Create PR via `/pull_request` command
5. Post implementation summary to GitHub issue

**IO-Specific Build Notes:**
- May invoke `terraform init`, `terraform plan`, `terraform apply`
- May invoke Packer builds for AMI creation
- Handles infrastructure-specific validation

### Test Phase (`asw_app_test_iso.py` / `asw_io_test_iso.py`)

**Purpose:** Run tests appropriate to workflow type

**App Workflow:**
1. Execute `/test` command for unit tests
2. On failure: Run `/resolve_failed_test` loop (max 3 attempts)
3. Execute `/test_e2e` command for browser tests
4. On failure: Run `/resolve_failed_e2e_test` loop
5. Report results to GitHub issue

**IO Workflow:**
1. Run `terraform validate` for syntax checking
2. Run `terraform plan` for dry-run validation
3. Run integration tests if applicable
4. Report results to GitHub issue

### Review Phase (`asw_app_review_iso.py` / `asw_io_review_iso.py`)

**Purpose:** Verify implementation matches specification

**Flow:**
1. Find spec file from state or git diff
2. Execute `/review` command
3. Parse `ReviewResult` from output
4. If issues found: Create patch and re-implement
5. Upload screenshots to R2, post results to issue

### Document Phase (`asw_app_document_iso.py` / `asw_io_document_iso.py`)

**Purpose:** Generate documentation

**App Workflow:**
- Create `app_docs/{type}-{id}-{slug}.md`

**IO Workflow:**
- Update `io/docs/` with infrastructure documentation
- Generate Terraform module documentation
- Update runbooks if applicable

### Ship Phase (`asw_app_ship_iso.py` / `asw_io_ship_iso.py`)

**Purpose:** Merge PR and trigger deployment

**Flow:**
1. Validate all required state fields present
2. Merge PR via `gh pr merge`
3. Optionally trigger deployment workflow
4. Update state with `shipped_at`, `merge_commit`, `pr_number`
5. Clean up worktree

### IO-Specific Phases

**Deploy Phase (`asw_io_deploy.py`):**
- Execute `terraform apply` with auto-approve (after review)
- Update infrastructure state
- Validate deployment success

**Destroy Phase (`asw_io_destroy.py`):**
- Execute `terraform destroy` with safety checks
- Require explicit confirmation
- Update state and documentation

**AMI Build Phase (`asw_io_build_ami_iso.py`):**
- Execute Packer build
- Validate AMI creation
- Update state with AMI ID

### Orchestration Scripts

**App Workflows:**
- `asw_app_sdlc_iso.py` - Full: Plan -> Build -> Test -> Review -> Document -> Ship
- `asw_app_sdlc_zte_iso.py` - Zero Touch Execution: Auto-merge if all phases pass
- `asw_app_plan_build_iso.py` - Plan + Build only
- `asw_app_plan_build_test_iso.py` - Plan + Build + Test
- `asw_app_patch_iso.py` - Direct patch without planning phase

**IO Workflows:**
- `asw_io_sdlc_iso.py` - Full: Plan -> Build -> Test -> Review -> Document -> Ship
- `asw_io_sdlc_zte_iso.py` - Zero Touch Execution for infrastructure
- `asw_io_plan_build_iso.py` - Plan + Build for infrastructure
- `asw_io_deploy.py` - Infrastructure deployment
- `asw_io_destroy.py` - Infrastructure teardown

---

## Anti-Patterns to Avoid

### 1. Hardcoded Paths

```python
# BAD - Breaks in worktrees
plan_file = "specs/low-level/plan.md"

# GOOD - Use state working directory
working_dir = state.get_working_directory()
plan_file = os.path.join(working_dir, state.get("plan_file"))
```

### 2. Missing State Persistence

```python
# BAD - State changes lost if script crashes
state.update(branch_name=branch)
# ... do work ...

# GOOD - Persist immediately after updates
state.update(branch_name=branch)
state.save("create_branch")
# ... do work ...
```

### 3. Ignoring Retry Codes

```python
# BAD - Ignores transient failures
response = prompt_claude_code(request)
if not response.success:
    raise Error(response.output)

# GOOD - Check retry codes for recovery
response = prompt_claude_code_with_retry(request)
if not response.success:
    if response.retry_code == RetryCode.TIMEOUT_ERROR:
        logger.warning("Timed out, may succeed on retry")
    raise Error(response.output)
```

### 4. Bypassing Worktree Isolation

```python
# BAD - Runs in main repo, can corrupt state
result = subprocess.run(["git", "commit", "-m", "msg"])

# GOOD - Use working_dir from state
working_dir = state.get_working_directory()
result = subprocess.run(["git", "commit", "-m", "msg"], cwd=working_dir)
```

### 5. Direct Subprocess Without Environment

```python
# BAD - Missing required env vars
result = subprocess.run([CLAUDE_PATH, "-p", prompt])

# GOOD - Use safe environment
env = get_claude_env()
result = subprocess.run([CLAUDE_PATH, "-p", prompt], env=env)
```

### 6. Missing Bot Identifier

```python
# BAD - Causes webhook infinite loop
comment = f"Build complete for {asw_id}"
add_issue_comment(issue_number, comment)

# GOOD - Include bot identifier
comment = format_issue_message(asw_id, "builder", "Build complete")
add_issue_comment(issue_number, comment)
```

### 7. State Field Access Without Defaults

```python
# BAD - KeyError if field missing
port = state.data["backend_port"]

# GOOD - Use get() with default
port = state.get("backend_port", 9100)
```

### 8. Absolute Paths in Plan Files

```python
# BAD - Plan files should use relative paths
implement_plan("/Users/user/project/specs/plan.md", ...)

# GOOD - Validate and correct paths
plan_file = state.get("plan_file")
if os.path.isabs(plan_file):
    # Convert to relative from worktree
    plan_file = os.path.relpath(plan_file, working_dir)
```

### 9. Terraform State Lock Issues (IO-Specific)

```python
# BAD - Running terraform commands without lock handling
result = subprocess.run(["terraform", "apply"])

# GOOD - Handle state locking properly
result = subprocess.run(
    ["terraform", "apply", "-lock-timeout=5m"],
    cwd=working_dir
)
if "state lock" in result.stderr:
    # Wait and retry, or notify user
    handle_state_lock(result.stderr)
```

### 10. Provider Authentication Failures (IO-Specific)

```python
# BAD - Assuming credentials are always available
result = subprocess.run(["terraform", "plan"])

# GOOD - Verify credentials before running
if not verify_aws_credentials():
    logger.error("AWS credentials not configured")
    return False, "Missing AWS credentials"
result = subprocess.run(["terraform", "plan"], env=get_terraform_env())
```

---

## Usage Examples

### Debug a Failing ASW App Workflow

```
"Using asw-expert skill, analyze why ASW App workflow abc12345 is stuck at the test phase.
The state file shows plan_file but tests keep failing with timeout errors."
```

### Debug a Failing ASW IO Workflow

```
"Using asw-expert skill, analyze why ASW IO workflow xyz98765 is stuck at the terraform plan phase.
The state file shows plan_file but terraform keeps failing with provider errors."
```

### Review ASW Code for Anti-Patterns

```
"Review asw_app_build_iso.py using asw-expert skill. Check for:
- Missing state persistence calls
- Hardcoded paths
- Improper error handling
Provide specific line numbers and fixes."
```

### Design a New Workflow Phase

```
"Using asw-expert skill, help me design a new 'security-scan' phase that:
- Runs after build phase
- Uses Semgrep for static analysis
- Reports findings to GitHub issue
- Can block ship phase on critical findings"
```

### Design Infrastructure Automation Phase

```
"Using asw-expert skill, help me design a new 'terraform-drift-detection' phase that:
- Runs scheduled checks for infrastructure drift
- Reports findings to GitHub issue
- Can trigger remediation workflows"
```

### Optimize Workflow Performance

```
"Analyze ASW workflow performance using asw-expert skill:
- Which phases take longest?
- Can any phases run in parallel?
- What caching opportunities exist?"
```

### Troubleshoot Webhook Issues

```
"Using asw-expert skill, debug why webhook automation is creating duplicate ASW workflows.
I see multiple asw_app_plan_iso.py processes starting from the same issue comment."
```

### Infrastructure Deployment Troubleshooting

```
"Using asw-expert skill, debug why ASW IO deploy is failing.
Terraform plan succeeds but apply fails with 'resource already exists' error."
```

---

## Cross-References

This skill complements:

- **terraform-module-architect**: For designing Terraform modules used by ASW IO workflows
- **hashicorp-best-practices**: For Terraform and Packer best practices in ASW IO
- **packer-optimizer**: For optimizing AMI builds in ASW IO workflows
- **aws-solutions-architect**: For AWS infrastructure patterns used by ASW IO
- **ci-engineer-unit-test-suggester**: For improving ASW App test coverage

## Key Resources

### Reference Files

- `references/architecture.md` - System architecture and data flow
- `references/troubleshooting.md` - Common issues and solutions
- `references/improvement_patterns.md` - Optimization and enhancement catalog

---

*"Good automation makes humans faster. Great automation makes humans unnecessary for the boring parts."*
