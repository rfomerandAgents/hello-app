# Root Cause Analysis for Issue

> Perform comprehensive root cause analysis for failed or stuck ADW workflows

## Command

`/rca_issue <issue-number>`

## Arguments

- `<issue-number>`: GitHub issue number (integer, required)

## Purpose

Diagnose why an ADW workflow failed or didn't start for a specific GitHub issue. This command analyzes state files, execution logs, git history, and file system artifacts to identify the root cause and provide actionable recommendations.

## Instructions

Follow these steps systematically to perform a comprehensive root cause analysis:

### Step 1: Validate Input

1. Verify the issue number argument is provided and is a valid integer
2. Use `gh issue view <issue-number> --json number,title,state,labels` to:
   - Verify the issue exists in GitHub
   - Get the issue title for context
   - Check issue state (open/closed)
   - Check issue labels
3. If validation fails, output a clear error message and exit

### Step 2: Discover ADW Instances

1. Search for all ADW state files in the agents directory:
   ```bash
   find agents -name "adw_state.json" -type f
   ```

2. For each state file found:
   - Read the JSON content
   - Check if `issue_number` field matches the target issue
   - Collect all matching ADW instances with their adw_id

3. Record findings:
   - Number of ADW instances found
   - ADW IDs for each instance
   - Paths to state files

4. If no instances found, proceed to "Workflow Never Started" analysis (Step 8)

### Step 3: Analyze State Files

For each matching ADW instance:

1. Load and parse the state JSON file at `agents/<adw_id>/adw_state.json`

2. Check for required fields and record their values:
   - `adw_id`: Unique workflow identifier
   - `issue_number`: Should match target issue
   - `branch_name`: Git branch created for this workflow
   - `worktree_path`: Path to isolated worktree
   - `backend_port`: Allocated backend port
   - `frontend_port`: Allocated frontend port
   - `issue_class`: Workflow type (/feature, /bug, /patch, etc.)
   - `plan_file`: Path to plan file (may be null)
   - `all_adws`: List of workflow phases executed

3. Detect state anomalies:
   - Missing required fields
   - Invalid or null values where they shouldn't be
   - Unusual port numbers (outside expected ranges)
   - Corrupted JSON (catch parse errors)
   - Empty or incomplete workflow list

4. Extract timeline information if available:
   - When was the state created?
   - When was it last updated?
   - How long has it been in current phase?

### Step 4: Analyze Execution Logs

For each ADW instance:

1. Check for execution logs in the agent directory structure:
   - Main workflow logs: `agents/<adw_id>/adw_*/execution.log`
   - Phase-specific logs in subdirectories
   - Look for `stdout.log` and `stderr.log` files

2. For each log file found:
   - Read the last 500 lines (use `tail -n 500`) to avoid overwhelming output
   - Search for error patterns:
     - "ERROR", "Error:", "error:"
     - "FAILED", "Failed", "failed"
     - "Exception", "Traceback"
     - "Traceback (most recent call last):"
     - "AssertionError", "ValueError", "KeyError"
     - "git:", "fatal:", "warning:"
     - Specific known errors (see pattern catalog below)

3. Extract error context:
   - Capture the error message and surrounding 3-5 lines
   - Extract stack traces if present
   - Note the timestamp if available
   - Identify which phase/component logged the error

4. Categorize errors by type:
   - Git operation failures
   - Port allocation issues
   - Worktree conflicts
   - Agent execution failures
   - State corruption
   - Webhook/trigger issues
   - Phase-specific failures

### Step 5: Analyze Git History

1. Search for branches related to this issue:
   ```bash
   git branch -a | grep "issue-<issue-number>"
   ```

2. For each branch found:
   - Check if it still exists: `git show-ref --verify refs/heads/<branch-name>`
   - View recent commits: `git log <branch-name> --oneline -n 10`
   - Look for error-related commit messages
   - Check if branch was merged or abandoned

3. Check worktree status:
   ```bash
   git worktree list
   ```
   - Look for worktrees matching the issue number or adw_id
   - Check if worktree paths from state files actually exist
   - Identify orphaned or stuck worktrees

4. Check for uncommitted changes in worktrees (if they exist):
   - For each worktree path from state: `git -C <worktree-path> status --short`
   - Note any uncommitted changes or detached HEAD states

### Step 6: File System Checks

For each ADW instance:

1. Check if worktree directory exists:
   ```bash
   test -d <worktree_path> && echo "EXISTS" || echo "MISSING"
   ```

2. Check if agent directory exists and its contents:
   ```bash
   ls -la agents/<adw_id>/
   ```

3. Detect mismatches:
   - State file says worktree exists but directory is missing
   - Worktree directory exists but not in git worktree list
   - Agent directory missing critical subdirectories
   - Log files missing when they should exist

4. Check for orphaned resources:
   - Worktree directories in `trees/` without corresponding state files
   - Agent directories without state files
   - Very old directories (more than 7 days) that weren't cleaned up

5. Check disk space (for completeness):
   ```bash
   df -h .
   ```

### Step 7: Pattern Matching and Root Cause Determination

Compare collected evidence to known failure patterns:

#### Known Failure Pattern Catalog:

**1. Webhook/Trigger Failures:**
- Symptom: No ADW instances found, no branches created
- Indicators: Issue exists but no workflow artifacts
- Common causes:
  - Missing `ADW_BOT_IDENTIFIER` environment variable
  - Issue not labeled correctly for ADW processing
  - No trigger comment posted to issue
  - Bot loop prevention blocking legitimate trigger
  - Webhook not configured or not receiving events

**2. Worktree Failures:**
- Symptom: Error in logs about worktree, branch exists but worktree missing
- Indicators: "worktree already exists", "fatal: could not create worktree"
- Common causes:
  - Worktree directory already exists from previous run
  - Git fetch failures during worktree creation
  - Branch name conflicts
  - Insufficient permissions
  - Disk space issues

**3. Port Conflicts:**
- Symptom: Error about port allocation, duplicate port numbers
- Indicators: "Address already in use", "port already allocated"
- Common causes:
  - Backend ports (9100-9114) exhausted
  - Frontend ports (9200-9214) exhausted
  - Port allocation collision between multiple ADWs
  - Previous ADW not properly cleaned up

**4. State Corruption:**
- Symptom: JSON parse errors, missing required fields
- Indicators: State file exists but can't be read, fields are null
- Common causes:
  - State file not fully written (process crashed mid-write)
  - Manual editing introduced syntax errors
  - File system corruption
  - Race condition in state updates

**5. Git Operation Failures:**
- Symptom: Errors in git commands in logs
- Indicators: "fatal:", "error: failed to push", "merge conflict"
- Common causes:
  - Authentication failures (GitHub token expired/invalid)
  - Permission denied (no write access to repo)
  - Merge conflicts when creating branch
  - Detached HEAD state
  - Branch already exists on remote

**6. Agent Execution Failures:**
- Symptom: Agent process crashes, timeout errors
- Indicators: "Claude Code authentication failed", "timeout", "JSON parsing error"
- Common causes:
  - Claude Code authentication issues
  - Agent timeout (workflow taking too long)
  - Invalid JSON in agent output
  - Agent process killed by system
  - Rate limiting or API quota exceeded

**7. Phase-Specific Failures:**
- **Plan Phase**: Classification fails, workflow detection fails, plan file not created
- **Build Phase**: Code generation errors, syntax errors in generated code
- **Test Phase**: Test failures, test timeout, test environment setup fails
- **Review Phase**: Review agent blocks changes, review criteria not met
- **Document Phase**: Documentation generation fails, missing context
- **Ship Phase**: PR creation fails, merge conflicts, CI/CD failures

#### Determination Logic:

1. **If no ADW instances found:**
   - PRIMARY: Workflow never started
   - Check: Issue labels, comments, webhook configuration
   - Likely: Trigger issue (webhook, labels, bot identifier)

2. **If state file exists but worktree missing:**
   - PRIMARY: Worktree cleanup or failure during creation
   - Check: Git worktree list, logs for worktree errors
   - Likely: Worktree conflict or manual cleanup

3. **If logs show specific error patterns:**
   - Match error to pattern catalog
   - Assign confidence score based on specificity of match
   - PRIMARY: Highest confidence match
   - SECONDARY: Contributing factors

4. **If multiple errors found:**
   - Identify cascading failures (one failure causing another)
   - Determine initial trigger vs consequences
   - PRIMARY: Initial failure
   - SECONDARY: Cascading effects

5. **If no clear errors but workflow stuck:**
   - Check last activity timestamp
   - Check which phase it's in
   - PRIMARY: Likely timeout or manual intervention
   - SECONDARY: Resource constraints

### Step 8: Special Case - Workflow Never Started

If no ADW instances found:

1. Analyze GitHub issue directly:
   - Read issue body and all comments
   - Look for workflow trigger comments (/feature, /bug, /patch, etc.)
   - Check issue labels for ADW-related labels
   - Check if issue was closed before processing could start

2. Check for webhook logs (if accessible):
   - Search for issue number in any available webhook logs
   - Look for processing attempts or errors

3. Determine why workflow didn't start:
   - **No trigger comment**: User never posted workflow trigger
   - **Wrong trigger format**: Comment doesn't match expected pattern
   - **Bot identifier mismatch**: ADW_BOT_IDENTIFIER prevents bot from commenting
   - **Webhook not configured**: Webhook never received event
   - **Issue closed**: Issue was closed before ADW could process
   - **Repository not configured**: Repo doesn't have ADW enabled
   - **Permissions issue**: Bot doesn't have access to comment/label

4. Provide specific diagnosis for "never started" case

### Step 9: Generate Recommendations

Based on the identified root cause, provide specific, actionable recommendations:

#### Immediate Fix Recommendations by Root Cause:

**Webhook/Trigger Issues:**
- Check ADW_BOT_IDENTIFIER environment variable is set correctly
- Verify webhook is configured in GitHub repository settings
- Post a trigger comment to the issue (/feature, /bug, /patch, etc.)
- Check issue has appropriate labels
- Verify bot has permissions to comment on issues

**Worktree Conflicts:**
- Clean up existing worktree: `git worktree remove trees/<adw_id>`
- If removal fails, force remove: `git worktree remove --force trees/<adw_id>`
- Clean up worktree directory: `rm -rf trees/<adw_id>`
- Run `git worktree prune` to clean up stale entries
- Retry the workflow after cleanup

**Port Conflicts:**
- List active ADW instances to see port usage
- Clean up old/stuck ADW instances to free ports
- Expand port ranges in configuration if frequently exhausted
- Check for processes holding ports: `lsof -i :9100-9214`

**State Corruption:**
- Backup corrupted state: `cp agents/<adw_id>/adw_state.json agents/<adw_id>/adw_state.json.bak`
- Delete corrupted state file: `rm agents/<adw_id>/adw_state.json`
- Restart workflow from beginning (state will be recreated)
- If recurring, check disk space and file system health

**Git Operation Failures:**
- Check GitHub authentication: `gh auth status`
- Re-authenticate if needed: `gh auth login`
- Verify repository write permissions
- Check if branch already exists and delete if needed
- Resolve merge conflicts manually if present

**Agent Execution Failures:**
- Check Claude Code authentication: Run claude code auth status if available
- Increase timeout limits if workflow is legitimately long-running
- Check API quota and rate limits
- Review agent logs for specific error messages
- Retry with smaller scope or different parameters

**Phase-Specific Failures:**
- Review logs for the specific phase that failed
- Check phase-specific requirements (tests exist, docs in place, etc.)
- Retry the specific phase after fixing identified issues
- Consider manual intervention for the failed phase

#### Prevention Recommendations:

- **Add monitoring**: Set up alerts for workflow failures
- **Add validation**: Validate inputs before starting workflows
- **Improve error handling**: Better error messages and recovery
- **Add cleanup**: Automated cleanup of old/stuck workflows
- **Add health checks**: Regular checks for port exhaustion, disk space
- **Improve documentation**: Document common failure modes and fixes
- **Add rate limiting**: Prevent overwhelming the system with too many workflows

#### Reference Links:

- Link to relevant code: `asw/app/adw_modules/*.py`
- Link to workflow orchestration: `asw/app/adw_sdlc_*.py`
- Link to cleanup command: `.claude/commands/cleanup_worktrees.md`
- Link to health check: `.claude/commands/health_check.md`
- Link to similar past issues (if any found in git history)

### Step 10: Format Comprehensive RCA Report

Output the analysis as a well-structured markdown report:

```markdown
# Root Cause Analysis - Issue #<issue-number>

**Analysis Date**: <current-timestamp>
**Issue Title**: <issue-title-from-github>
**Issue State**: <open|closed>

---

## 🔍 Discovery

- **ADW Instances Found**: <count>
- **Workflow IDs**: <list-of-adw-ids>
- **Issue Class**: </feature|/bug|/patch|/chore|etc or "N/A">
- **Branches Created**: <list-of-branch-names>
- **Current Status**: <in_progress|completed|failed|never_started>

---

## 📊 State Analysis

<For each ADW instance, report:>

### ADW Instance: <adw_id>

**State File**: `agents/<adw_id>/adw_state.json`

**Configuration**:
- Branch: `<branch_name>`
- Worktree Path: `<worktree_path>`
- Backend Port: `<backend_port>`
- Frontend Port: `<frontend_port>`
- Workflow Phases: `<all_adws>`

**State Anomalies**:
<List any anomalies found, or "None detected">
- <anomaly-description>

**Timeline**:
- <Timeline information if available>

---

## 📋 Log Analysis

<For each ADW instance with logs:>

### ADW Instance: <adw_id>

**Log Files Found**:
- <list-of-log-files-with-paths>

**Errors Detected**:

<For each error category:>

#### <Error-Category> (e.g., Git Operation Failures)
```
<error-message-with-context>
```
**Source**: `<log-file-path>`
**Approximate Time**: <timestamp-if-available>

<If no errors found: "No errors detected in logs">

---

## 🌳 Git Analysis

**Branches Found**:
- <list-of-branches-related-to-issue>
- <branch-status: merged|open|deleted>

**Worktrees**:
- <list-worktrees-from-git-worktree-list>
- <note-any-orphaned-or-stuck-worktrees>

**Branch Status**:
- <details-about-branch-commits-and-status>

**Inconsistencies**:
<List any mismatches between state and git reality, or "None detected">
- <inconsistency-description>

---

## 💾 File System Analysis

<For each ADW instance:>

### ADW Instance: <adw_id>

**Worktree Directory**: <EXISTS|MISSING>
- Expected: `<worktree_path>`
- Actual: <status>

**Agent Directory**: <EXISTS|MISSING>
- Path: `agents/<adw_id>/`
- Contents: <list-subdirectories-if-exists>

**Orphaned Resources**:
<List any orphaned directories or files, or "None detected">
- <orphaned-resource-description>

**Disk Space**: <available-space>

---

## 🎯 Root Cause

### PRIMARY Root Cause

**Category**: <Webhook|Worktree|Port|State|Git|Agent|Phase-Specific>

**Description**: <clear-description-of-primary-root-cause>

**Evidence**:
- <key-evidence-point-1>
- <key-evidence-point-2>
- <key-evidence-point-3>

**Confidence**: <HIGH|MEDIUM|LOW>

### SECONDARY Contributing Factors

<List any contributing factors or secondary causes, or "None identified">
- <contributing-factor-1>
- <contributing-factor-2>

---

## ✅ Recommendations

### Immediate Actions

<Numbered list of specific commands or steps to fix the issue>

1. <specific-action-with-command>
2. <specific-action-with-command>
3. <specific-action-with-command>

### Prevention Measures

<Bullet list of prevention strategies>

- <prevention-measure-1>
- <prevention-measure-2>
- <prevention-measure-3>

### References

- **Related Code**: <links-to-relevant-code-files>
- **Related Commands**: <links-to-related-slash-commands>
- **Similar Issues**: <git-commits-or-issues-if-found>

---

## 📝 Summary

<2-4 sentence summary of the RCA findings and next steps>

---

**Note**: This analysis is based on available data at the time of analysis. If the issue persists after following recommendations, additional investigation may be needed.
```

## Error Handling

- If issue number is not provided, output: "Error: Issue number is required. Usage: /rca_issue <issue-number>"
- If issue number is not an integer, output: "Error: Issue number must be an integer. Got: <argument>"
- If issue doesn't exist in GitHub, output: "Error: Issue #<issue-number> not found in repository"
- If GitHub CLI is not authenticated, output: "Error: GitHub CLI not authenticated. Run: gh auth login"
- Handle all file read errors gracefully (missing files, permission errors)
- Handle all JSON parse errors gracefully (corrupted state files)
- Handle all git command errors gracefully (missing branches, etc.)
- Never crash - always provide a report even with partial data

## Performance Considerations

- Limit log file reading to last 500 lines per file
- Limit git log to last 100 commits or 30 days
- If more than 10 ADW instances found for an issue, analyze only the 5 most recent
- Summarize older instances rather than full analysis
- Use timeouts for long-running commands (git operations, file searches)

## Security Considerations

- Validate issue number is integer before using in shell commands
- Never use raw input in shell commands without validation
- Only read files in `agents/` and `trees/` directories
- Redact sensitive patterns in logs before displaying:
  - API keys: `sk-ant-*`, `ghp_*`, `gho_*`
  - Tokens: Replace with `[REDACTED-TOKEN]`
  - Passwords: Replace with `[REDACTED-PASSWORD]`
- Respect repository permissions (use `gh` CLI which handles auth)

## Notes

- This command is read-only and makes no modifications to state, worktrees, or git
- It's safe to run multiple times on the same issue
- The more data available (logs, state files, git history), the more accurate the RCA
- If multiple root causes are equally likely, list all with confidence scores
- When in doubt, provide multiple hypotheses rather than guessing
- Always err on the side of providing too much context rather than too little
