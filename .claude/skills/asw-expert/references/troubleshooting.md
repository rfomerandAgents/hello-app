# ASW Troubleshooting Guide

This guide covers troubleshooting for both ASW App (application development) and ASW IO (infrastructure operations) workflows.

## Quick Diagnostics

### Check ASW App State

```bash
# View app workflow state file
cat agents/{asw_id}/asw_app_state.json | jq

# Check if worktree exists
ls -la trees/{asw_id}/

# Verify worktree in git
git worktree list | grep {asw_id}
```

### Check ASW IO State

```bash
# View io workflow state file
cat agents/{asw_id}/asw_io_state.json | jq

# Check terraform workspace
cat agents/{asw_id}/asw_io_state.json | jq -r '.terraform_workspace'

# Check infrastructure type
cat agents/{asw_id}/asw_io_state.json | jq -r '.infrastructure_type'
```

### Check Logs

```bash
# Find app workflow log files
ls logs/asw_app_*.log

# Tail latest app log
tail -f logs/asw_app_plan_iso_*.log

# Find io workflow log files
ls logs/asw_io_*.log

# Tail latest io log
tail -f logs/asw_io_plan_iso_*.log
```

---

## Common Issues (Both App and IO)

### 1. Worktree Creation Failures

**Symptom:** Plan phase fails with "Failed to create worktree"

**Possible Causes:**

**A. Branch already exists locally**
```bash
# Error: branch 'feature-issue-42-asw-abc12345' already exists
```

**Solution:**
```bash
# Delete the local branch
git branch -D feature-issue-42-asw-abc12345

# Or force create worktree
git worktree add --force trees/abc12345 feature-issue-42-asw-abc12345
```

**B. Worktree directory already exists**
```bash
# Error: 'trees/abc12345' already exists
```

**Solution:**
```bash
# Remove existing worktree
git worktree remove trees/abc12345 --force

# Clean up worktree list
git worktree prune
```

**C. Dirty worktree preventing operations**
```bash
# Error: changes would be overwritten
```

**Solution:**
```bash
# Force remove with changes
rm -rf trees/abc12345
git worktree prune
```

---

### 2. Port Conflicts

**Symptom:** Workflow fails to start with "Address already in use"

**Diagnostics:**
```bash
# Check what's using the port
lsof -i :9103
lsof -i :9203

# List all ASW port range usage
lsof -i :9100-9114
lsof -i :9200-9214
```

**Solutions:**

**A. Kill orphan processes**
```bash
# Find and kill process using port
kill $(lsof -t -i:9103)
```

**B. Use different ASW ID**
The port is deterministically derived from ASW ID. A different ID will try different ports.

**C. Manual port override**
```bash
# In .ports.env, use next available
BACKEND_PORT=9105
FRONTEND_PORT=9205
```

**D. Check for zombie worktrees**
```bash
# List all worktrees
git worktree list

# Remove completed/failed ones
git worktree remove trees/old_asw_id --force
```

---

### 3. State Corruption

**Symptom:** Workflow fails with "KeyError" or "missing required field"

**Diagnostics:**
```bash
# Validate JSON syntax (app)
python -m json.tool agents/{asw_id}/asw_app_state.json

# Validate JSON syntax (io)
python -m json.tool agents/{asw_id}/asw_io_state.json

# Check for missing fields
cat agents/{asw_id}/asw_app_state.json | jq 'keys'
```

**Common Missing Fields:**

| Field | Required By | Fix |
|-------|-------------|-----|
| `plan_file` | Build phase | Re-run plan phase |
| `branch_name` | All phases | Re-run plan phase |
| `worktree_path` | Isolated phases | Check worktree exists |
| `issue_class` | Commit/PR | Re-run classification |
| `terraform_workspace` | IO workflows | Re-run IO plan phase |

**Solutions:**

**A. Manually fix state**
```bash
# Edit state file
cat agents/{asw_id}/asw_app_state.json | jq '. + {"plan_file": "specs/low-level/plan.md"}' > tmp.json
mv tmp.json agents/{asw_id}/asw_app_state.json
```

**B. Re-run from plan phase (App)**
```bash
# Delete state and start fresh
rm -rf agents/{asw_id}
rm -rf trees/{asw_id}
uv run asw/app/asw_app_plan_iso.py {issue_number}
```

**C. Re-run from plan phase (IO)**
```bash
# Delete state and start fresh
rm -rf agents/{asw_id}
rm -rf trees/{asw_id}
uv run asw/io/asw_io_plan_iso.py {issue_number}
```

---

### 4. GitHub API Rate Limiting

**Symptom:** "API rate limit exceeded" or 403 errors

**Diagnostics:**
```bash
# Check rate limit status
gh api rate_limit | jq '.resources.core'
```

**Solutions:**

**A. Wait for reset**
```bash
# Check when limit resets
gh api rate_limit | jq '.resources.core.reset | strftime("%Y-%m-%d %H:%M:%S")'
```

**B. Use authenticated requests**
Ensure `GITHUB_PAT` is set or `gh auth status` shows logged in.

**C. Reduce API calls**
ASW uses minimal payloads. Check for loops causing excessive calls.

---

### 5. Claude Code CLI Errors

**Symptom:** "Claude Code error" with various subtypes

**RetryCode Reference:**

| Code | Meaning | Retryable? |
|------|---------|------------|
| `CLAUDE_CODE_ERROR` | General CLI error | Yes |
| `TIMEOUT_ERROR` | Command timed out | Yes |
| `EXECUTION_ERROR` | Subprocess failed | Yes |
| `ERROR_DURING_EXECUTION` | Agent crashed | Yes |
| `NONE` | Success or non-retryable | No |

**Solutions:**

**A. Check Claude Code installation**
```bash
claude --version
which claude
```

**B. Verify environment**
```bash
# Check OAuth token is set
echo $CLAUDE_CODE_OAUTH_TOKEN | head -c 20
```

**C. Check MCP config**
```bash
# Ensure .mcp.json exists in worktree
ls trees/{asw_id}/.mcp.json
```

**D. Increase timeout**
Default is 5 minutes. For complex operations, modify in `agent.py`.

**E. Check JSONL output for details**
```bash
# View raw Claude output
cat agents/{asw_id}/sdlc_planner/raw_output.jsonl | jq -r '.result // .message.content[0].text // empty' | tail -20
```

---

### 6. Branch Naming Collisions

**Symptom:** "Branch already exists" when creating new workflow

**Cause:** Same issue processed multiple times with different ASW IDs.

**Diagnostics:**
```bash
# List branches for this issue
git branch -a | grep "issue-42"
```

**Solutions:**

**A. Use existing branch (App)**
```bash
# Find the ASW ID from branch name
# branch: feature-issue-42-asw-abc12345-...
# ASW ID: abc12345

# Resume with that ASW ID
uv run asw/app/asw_app_build_iso.py 42 abc12345
```

**B. Use existing branch (IO)**
```bash
# Resume with that ASW ID
uv run asw/io/asw_io_build_iso.py 42 abc12345
```

**C. Force new branch**
Delete existing state and branches:
```bash
git branch -D feature-issue-42-asw-abc12345-*
rm -rf agents/abc12345
uv run asw/app/asw_app_plan_iso.py 42
```

---

### 7. Plan File Path Resolution

**Symptom:** "No such file or directory" for plan file

**Cause:** Path confusion between absolute/relative paths or main repo vs worktree.

**Diagnostics:**
```bash
# Check what path is in state (app)
cat agents/{asw_id}/asw_app_state.json | jq -r '.plan_file'

# Check what path is in state (io)
cat agents/{asw_id}/asw_io_state.json | jq -r '.plan_file'

# Check if it exists
ls -la "$(cat agents/{asw_id}/asw_app_state.json | jq -r '.plan_file')"

# Check in worktree
ls -la "trees/{asw_id}/$(cat agents/{asw_id}/asw_app_state.json | jq -r '.plan_file')"
```

**Solutions:**

**A. Fix path in state**
Ensure path is relative to worktree root:
```bash
# Should be: specs/low-level/plan-xxx.md
# Not: /absolute/path/to/specs/...
```

**B. Copy plan to worktree**
```bash
cp specs/low-level/plan-{asw_id}-*.md trees/{asw_id}/specs/low-level/
```

---

### 8. Webhook Loop Prevention

**Symptom:** Infinite workflow spawning from same issue

**Cause:** Bot comments not being detected/filtered.

**Diagnostics:**
```bash
# Check issue comments for app bot identifier
gh issue view {issue_number} --comments | grep "ASW-APP-AGENTS"

# Check issue comments for io bot identifier
gh issue view {issue_number} --comments | grep "ASW-IO-AGENTS"

# Check webhook logs
tail -f logs/webhook_router.log
```

**Solutions:**

**A. Verify bot identifier in comments**
All ASW comments must include the appropriate identifier:
```python
# App workflows
comment = format_issue_message(asw_id, "builder", "Build complete", workflow_type="app")
# Result: "[ASW-APP-AGENTS] abc12345_builder: Build complete"

# IO workflows
comment = format_issue_message(asw_id, "builder", "Build complete", workflow_type="io")
# Result: "[ASW-IO-AGENTS] abc12345_builder: Build complete"
```

**B. Check webhook filter logic**
In `trigger_webhook.py`, ensure bot comments are filtered:
```python
if ASW_APP_BOT_IDENTIFIER in comment_body or ASW_IO_BOT_IDENTIFIER in comment_body:
    logger.info("Skipping bot comment")
    return
```

---

### 9. E2E Test Failures (App Workflows)

**Symptom:** E2E tests fail with browser/Playwright errors

**Diagnostics:**
```bash
# Check Playwright installation
npx playwright --version

# Check browser binaries
npx playwright install --dry-run

# View test output
cat agents/{asw_id}/e2e_tester/raw_output.jsonl | jq -r '.result // empty'
```

**Solutions:**

**A. Install browsers**
```bash
cd trees/{asw_id}/app
npx playwright install chromium
```

**B. Check MCP Playwright config**
```bash
cat trees/{asw_id}/.mcp.json | jq '.mcpServers.playwright'
```

**C. Run with headed browser for debugging**
Temporarily modify test to use `headless: false`.

---

### 10. Review Phase Screenshot Issues

**Symptom:** Screenshots not captured or uploaded

**Diagnostics:**
```bash
# Check review_img directory
ls -la agents/{asw_id}/reviewer/review_img/

# Check R2 upload config
echo $CLOUDFLARE_R2_BUCKET_NAME
echo $CLOUDFLARE_R2_PUBLIC_DOMAIN
```

**Solutions:**

**A. Ensure MCP Playwright is working**
Screenshots are captured via MCP Playwright tool.

**B. Check R2 credentials**
```bash
# Verify R2 access
aws s3 ls s3://${CLOUDFLARE_R2_BUCKET_NAME}/ --endpoint-url=${CLOUDFLARE_R2_ENDPOINT_URL}
```

**C. Manual screenshot test**
```bash
# Test screenshot capture
npx playwright screenshot --url http://localhost:9203 test.png
```

---

## IO-Specific Issues

### 11. Terraform State Lock Issues

**Symptom:** "Error acquiring the state lock" or workflow hangs

**Diagnostics:**
```bash
# Check for existing lock
cd trees/{asw_id}/io/terraform
terraform force-unlock -help

# Check state lock info
cat .terraform/terraform.tfstate | jq '.lineage'
```

**Solutions:**

**A. Wait for existing operation**
Another terraform process may be running. Wait or check for orphan processes.

**B. Force unlock (use with caution)**
```bash
cd trees/{asw_id}/io/terraform
terraform force-unlock LOCK_ID
```

**C. Check for remote state lock**
If using Terraform Cloud or S3 backend:
```bash
# S3 backend - check DynamoDB lock table
aws dynamodb scan --table-name terraform-locks
```

---

### 12. Terraform Provider Authentication Failures

**Symptom:** "Error: No valid credential sources found" or provider errors

**Diagnostics:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check environment
echo $AWS_ACCESS_KEY_ID | head -c 5
echo $AWS_DEFAULT_REGION
```

**Solutions:**

**A. Set AWS credentials**
```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_DEFAULT_REGION=us-east-1
```

**B. Use AWS profile**
```bash
export AWS_PROFILE=your-profile
```

**C. Check .env file**
Ensure credentials are in `.env` and loaded properly.

---

### 13. Terraform Plan/Apply Failures

**Symptom:** "Error: Resource already exists" or "Error: Invalid value"

**Diagnostics:**
```bash
# View plan output
cd trees/{asw_id}/io/terraform
terraform plan -out=plan.out

# Check state
terraform state list
terraform state show aws_instance.example
```

**Solutions:**

**A. Import existing resource**
```bash
terraform import aws_instance.example i-1234567890abcdef0
```

**B. Refresh state**
```bash
terraform refresh
```

**C. Check for drift**
```bash
terraform plan -refresh-only
```

---

### 14. Packer Build Failures (AMI Builds)

**Symptom:** "Error building AMI" or timeout during provisioning

**Diagnostics:**
```bash
# Check Packer logs
cat agents/{asw_id}/packer_builder/raw_output.jsonl

# Check AMI state
aws ec2 describe-images --image-ids ami-xxx
```

**Solutions:**

**A. Check source AMI availability**
```bash
aws ec2 describe-images --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-*"
```

**B. Verify security group allows SSH**
Packer needs SSH access to configure the instance.

**C. Increase build timeout**
Modify Packer template `communicator` settings.

**D. Check provisioner scripts**
Ensure shell scripts are executable and have correct paths.

---

### 15. Terraform Workspace Issues (IO)

**Symptom:** "Workspace not found" or wrong workspace

**Diagnostics:**
```bash
# List available workspaces
cd trees/{asw_id}/io/terraform
terraform workspace list

# Check current workspace
terraform workspace show

# Check state for workspace
cat agents/{asw_id}/asw_io_state.json | jq -r '.terraform_workspace'
```

**Solutions:**

**A. Create missing workspace**
```bash
terraform workspace new dev
```

**B. Switch to correct workspace**
```bash
terraform workspace select dev
```

**C. Update state file**
```bash
cat agents/{asw_id}/asw_io_state.json | jq '. + {"terraform_workspace": "dev"}' > tmp.json
mv tmp.json agents/{asw_id}/asw_io_state.json
```

---

## Recovery Procedures

### Full Workflow Reset (App)

When everything is broken, start fresh:

```bash
# 1. Clean up worktree
git worktree remove trees/{asw_id} --force
git worktree prune

# 2. Clean up state
rm -rf agents/{asw_id}

# 3. Clean up branch
git branch -D {branch_name}

# 4. Restart from issue
uv run asw/app/asw_app_plan_iso.py {issue_number}
```

### Full Workflow Reset (IO)

```bash
# 1. Clean up worktree
git worktree remove trees/{asw_id} --force
git worktree prune

# 2. Clean up state
rm -rf agents/{asw_id}

# 3. Clean up branch
git branch -D {branch_name}

# 4. Restart from issue
uv run asw/io/asw_io_plan_iso.py {issue_number}
```

### Resume from Specific Phase (App)

```bash
# Resume from build (requires plan complete)
uv run asw/app/asw_app_build_iso.py {issue_number} {asw_id}

# Resume from test (requires build complete)
uv run asw/app/asw_app_test_iso.py {issue_number} {asw_id}

# Resume from review (requires test complete)
uv run asw/app/asw_app_review_iso.py {issue_number} {asw_id}

# Resume from ship (requires review complete)
uv run asw/app/asw_app_ship_iso.py {issue_number} {asw_id}
```

### Resume from Specific Phase (IO)

```bash
# Resume from build (requires plan complete)
uv run asw/io/asw_io_build_iso.py {issue_number} {asw_id}

# Resume from test (requires build complete)
uv run asw/io/asw_io_test_iso.py {issue_number} {asw_id}

# Resume from review (requires test complete)
uv run asw/io/asw_io_review_iso.py {issue_number} {asw_id}

# Resume from ship (requires review complete)
uv run asw/io/asw_io_ship_iso.py {issue_number} {asw_id}

# Deploy infrastructure (after ship)
uv run asw/io/asw_io_deploy.py {issue_number} {asw_id}
```

### Manual PR Merge

If ship phase fails but PR is ready:

```bash
# Merge manually
gh pr merge {pr_number} --squash --delete-branch

# Update state manually (app)
cat agents/{asw_id}/asw_app_state.json | jq '. + {
  "shipped_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "pr_number": "{pr_number}"
}' > tmp.json
mv tmp.json agents/{asw_id}/asw_app_state.json

# Update state manually (io)
cat agents/{asw_id}/asw_io_state.json | jq '. + {
  "shipped_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "pr_number": "{pr_number}"
}' > tmp.json
mv tmp.json agents/{asw_id}/asw_io_state.json

# Clean up worktree
git worktree remove trees/{asw_id}
```

---

## Preventive Measures

### Pre-Flight Checklist

Before running ASW workflows:

- [ ] `gh auth status` shows authenticated
- [ ] `claude --version` works
- [ ] `.env` file has all required variables
- [ ] No conflicting processes on port 9100-9214
- [ ] Git is on main branch with clean status
- [ ] `git fetch origin` completes successfully

**Additional checks for IO workflows:**
- [ ] `aws sts get-caller-identity` succeeds
- [ ] `terraform --version` works
- [ ] `packer --version` works (if building AMIs)

### Health Check Script

```bash
#!/bin/bash
# asw_health_check.sh

echo "=== ASW Health Check ==="

# Check gh auth
echo -n "GitHub CLI: "
gh auth status &>/dev/null && echo "OK" || echo "FAIL (run: gh auth login)"

# Check Claude
echo -n "Claude CLI: "
claude --version &>/dev/null && echo "OK" || echo "FAIL (check CLAUDE_CODE_PATH)"

# Check ports
echo -n "Port 9100-9114: "
lsof -i :9100-9114 &>/dev/null && echo "WARNING (in use)" || echo "OK (free)"

# Check worktrees
echo -n "Worktrees: "
count=$(git worktree list | wc -l)
echo "$count active"

# Check env
echo -n "Environment: "
[[ -f .env ]] && echo "OK" || echo "FAIL (missing .env)"

echo ""
echo "=== IO-Specific Checks ==="

# Check AWS
echo -n "AWS CLI: "
aws sts get-caller-identity &>/dev/null && echo "OK" || echo "FAIL (check AWS credentials)"

# Check Terraform
echo -n "Terraform: "
terraform --version &>/dev/null && echo "OK" || echo "FAIL (install terraform)"

# Check Packer
echo -n "Packer: "
packer --version &>/dev/null && echo "OK" || echo "FAIL (install packer)"
```
