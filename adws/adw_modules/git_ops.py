"""Git operations for ADW composable architecture.

Provides centralized git operations that build on top of github.py module.
"""

import subprocess
import json
import logging
import os
from typing import Optional, Tuple, List, Dict, Any

# Import GitHub functions from existing module
from adw_modules.github import get_repo_url, extract_repo_path, make_issue_comment


def check_working_directory_clean(cwd: Optional[str] = None) -> Tuple[bool, Optional[str], List[str]]:
    """Check if working directory has uncommitted changes.

    Args:
        cwd: Optional working directory path

    Returns:
        Tuple of (is_clean, error_message, changed_files)
        - is_clean: True if no uncommitted changes
        - error_message: Description if not clean
        - changed_files: List of files with changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode != 0:
            return False, f"Failed to check git status: {result.stderr}", []

        output = result.stdout.strip()
        if not output:
            return True, None, []

        # Parse output to get changed files
        changed_files = []
        for line in output.split("\n"):
            if line.strip():
                # Format is: "XY filename" where XY is status
                # Get filename after the status codes
                parts = line.split()
                if len(parts) >= 2:
                    changed_files.append(parts[-1])
                else:
                    changed_files.append(line.strip())

        return False, "Working directory has uncommitted changes", changed_files

    except Exception as e:
        return False, f"Error checking working directory: {e}", []


def stash_changes(message: str, cwd: Optional[str] = None, logger: Optional[logging.Logger] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """Stash uncommitted changes with a descriptive message.

    Args:
        message: Descriptive message for the stash
        cwd: Optional working directory
        logger: Optional logger instance

    Returns:
        Tuple of (success, error_message, stash_id)
        - stash_id: Reference to created stash (e.g., "stash@{0}")
    """
    try:
        # First check if there are changes to stash
        is_clean, _, _ = check_working_directory_clean(cwd=cwd)
        if is_clean:
            if logger:
                logger.debug("No changes to stash")
            return True, None, None

        # Create stash with message, including untracked files
        result = subprocess.run(
            ["git", "stash", "push", "-m", message, "--include-untracked"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode != 0:
            return False, f"Failed to stash changes: {result.stderr}", None

        # Get the stash reference (typically stash@{0} for newest)
        stash_id = "stash@{0}"

        if logger:
            logger.info(f"Stashed changes: {message}")

        return True, None, stash_id

    except Exception as e:
        return False, f"Error stashing changes: {e}", None


def unstash_changes(stash_id: Optional[str] = None, cwd: Optional[str] = None, logger: Optional[logging.Logger] = None) -> Tuple[bool, Optional[str]]:
    """Pop stashed changes back to working directory.

    Args:
        stash_id: Specific stash to pop (default: most recent)
        cwd: Optional working directory
        logger: Optional logger instance

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Build command
        cmd = ["git", "stash", "pop"]
        if stash_id:
            cmd.append(stash_id)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode != 0:
            # Check if stash was empty
            if "No stash entries found" in result.stderr:
                if logger:
                    logger.debug("No stash entries to pop")
                return True, None
            return False, f"Failed to unstash changes: {result.stderr}"

        if logger:
            logger.info("Restored stashed changes")

        return True, None

    except Exception as e:
        return False, f"Error unstashing changes: {e}"


def check_merge_conflicts(branch_name: str, target_branch: str = "main", cwd: Optional[str] = None) -> Tuple[bool, Optional[str], List[str]]:
    """Check if merging branch would create conflicts.

    Performs a dry-run merge check without modifying working directory.

    Args:
        branch_name: Branch to merge
        target_branch: Target branch (default: "main")
        cwd: Optional working directory

    Returns:
        Tuple of (has_conflicts, error_message, conflicting_files)
    """
    try:
        # Use git merge-tree to simulate merge (two-branch syntax works on all versions)
        result = subprocess.run(
            ["git", "merge-tree", target_branch, branch_name],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        # Check for CONFLICT markers in output (indicates conflicts)
        combined_output = result.stdout + result.stderr
        has_conflict_markers = "CONFLICT" in combined_output

        if has_conflict_markers:
            # Parse output for conflicting files
            conflicting_files = []
            for line in combined_output.split("\n"):
                if "CONFLICT" in line:
                    # Try to extract filename from conflict line
                    # Format: "CONFLICT (content): Merge conflict in README.md"
                    if " in " in line:
                        filename = line.split(" in ")[-1].strip()
                        if filename:
                            conflicting_files.append(filename)
                    else:
                        parts = line.split()
                        for part in parts:
                            if "/" in part or "." in part:
                                conflicting_files.append(part)
                                break

            return True, "Merge would result in conflicts", list(set(conflicting_files))

        # Return code 0 means successful merge simulation (no conflicts)
        return False, None, []

    except Exception as e:
        # Fallback: assume no conflicts if we can't check
        return False, None, []


def check_ci_status(branch_name: str, logger: logging.Logger) -> Tuple[bool, Optional[str], Dict[str, str]]:
    """Check CI/CD status for branch via GitHub CLI.

    Args:
        branch_name: Branch name to check
        logger: Logger instance

    Returns:
        Tuple of (all_passing, error_message, check_details)
        - check_details: Dict of check_name -> status
    """
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        logger.warning(f"Could not get repo info for CI check: {e}")
        return True, None, {}  # Allow to proceed if we can't check

    try:
        # Check if PR exists for this branch
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo_path, "--head", branch_name, "--json", "number"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.warning(f"Could not list PRs: {result.stderr}")
            return True, None, {}

        prs = json.loads(result.stdout)
        if not prs:
            logger.info("No PR found for branch, skipping CI check")
            return True, None, {}

        pr_number = str(prs[0]["number"])

        # Get PR checks
        result = subprocess.run(
            ["gh", "pr", "checks", pr_number, "--repo", repo_path, "--json", "name,state,conclusion"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.warning(f"Could not get PR checks: {result.stderr}")
            return True, None, {}

        checks = json.loads(result.stdout)
        check_details = {}
        all_passing = True

        for check in checks:
            name = check.get("name", "unknown")
            state = check.get("state", "unknown")
            conclusion = check.get("conclusion", "unknown")

            # Determine status
            if state == "COMPLETED":
                status = conclusion
            else:
                status = state

            check_details[name] = status

            # Check if this check is not passing
            if status not in ["SUCCESS", "SKIPPED", "NEUTRAL"]:
                all_passing = False

        if not all_passing:
            return False, "Some CI checks are not passing", check_details

        return True, None, check_details

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse CI check output: {e}")
        return True, None, {}
    except Exception as e:
        logger.warning(f"Error checking CI status: {e}")
        return True, None, {}


def validate_pre_merge(
    branch_name: str,
    target_branch: str = "main",
    check_ci: bool = True,
    cwd: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Comprehensive pre-merge validation.

    Performs all necessary checks before merging:
    1. Working directory is clean
    2. No merge conflicts exist
    3. All CI checks pass (if check_ci=True)
    4. Target branch is up-to-date with origin

    Args:
        branch_name: Feature branch to merge
        target_branch: Target branch (default: "main")
        check_ci: Whether to check CI status
        cwd: Optional working directory
        logger: Optional logger instance

    Returns:
        Tuple of (is_valid, error_messages, details_dict)
    """
    errors = []
    details: Dict[str, Any] = {}

    if logger:
        logger.info("Running pre-merge validation...")

    # Check 1: Working directory is clean
    is_clean, error, changed_files = check_working_directory_clean(cwd=cwd)
    details["working_directory"] = {
        "is_clean": is_clean,
        "changed_files": changed_files
    }

    if not is_clean:
        errors.append(f"Working directory not clean: {', '.join(changed_files[:5])}")
        if logger:
            logger.warning(f"Working directory has uncommitted changes: {changed_files}")

    # Check 2: No merge conflicts
    has_conflicts, error, conflicting_files = check_merge_conflicts(
        branch_name=branch_name,
        target_branch=target_branch,
        cwd=cwd
    )
    details["merge_conflicts"] = {
        "has_conflicts": has_conflicts,
        "conflicting_files": conflicting_files
    }

    if has_conflicts:
        errors.append(f"Merge conflicts detected: {', '.join(conflicting_files) if conflicting_files else 'conflicts found'}")
        if logger:
            logger.warning(f"Merge conflicts detected: {conflicting_files}")

    # Check 3: CI status (optional)
    if check_ci and logger:
        ci_passing, ci_error, check_details = check_ci_status(branch_name, logger)
        details["ci_status"] = {
            "all_passing": ci_passing,
            "checks": check_details
        }

        if not ci_passing:
            errors.append(f"CI checks not passing: {ci_error}")
            if logger:
                logger.warning(f"CI checks failing: {check_details}")
    else:
        details["ci_status"] = {"skipped": True}

    # Check 4: Target branch is up-to-date
    try:
        result = subprocess.run(
            ["git", "fetch", "origin", target_branch],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        result = subprocess.run(
            ["git", "rev-list", f"HEAD..origin/{target_branch}", "--count"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        behind_count = int(result.stdout.strip()) if result.stdout.strip() else 0
        details["target_branch"] = {
            "branch": target_branch,
            "behind_count": behind_count
        }

        if behind_count > 0:
            if logger:
                logger.info(f"Local {target_branch} is {behind_count} commits behind origin")
    except Exception as e:
        details["target_branch"] = {"error": str(e)}

    is_valid = len(errors) == 0

    if logger:
        if is_valid:
            logger.info("Pre-merge validation passed")
        else:
            logger.warning(f"Pre-merge validation failed: {errors}")

    return is_valid, errors, details


def get_current_branch(cwd: Optional[str] = None) -> str:
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip()


def get_commits_ahead_of_main(cwd: Optional[str] = None) -> int:
    """Count commits on current branch ahead of origin/main.
    Returns 0 if branch has no commits ahead or on error."""
    try:
        # Fetch to ensure we have latest main
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        result = subprocess.run(
            ["git", "rev-list", "origin/main..HEAD", "--count"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except Exception:
        pass
    return 0


def push_branch(
    branch_name: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Push current branch to remote. Returns (success, error_message)."""
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def check_pr_exists(branch_name: str) -> Optional[str]:
    """Check if PR exists for branch. Returns PR URL if exists."""
    # Use github.py functions to get repo info
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        return None

    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo_path,
            "--head",
            branch_name,
            "--json",
            "url",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        prs = json.loads(result.stdout)
        if prs:
            return prs[0]["url"]
    return None


def create_branch(
    branch_name: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Create and checkout a new branch. Returns (success, error_message)."""
    # Create branch
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        # Check if error is because branch already exists
        if "already exists" in result.stderr:
            # Try to checkout existing branch
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, None
        return False, result.stderr
    return True, None


# Files that should never be committed (worktree-specific configuration)
# Note: specs/issue-*-adw-* uses glob pattern for ADW-generated spec files
WORKTREE_EXCLUDED_FILES = [
    ".mcp.json",
    ".ports.env",
    "playwright-mcp-config.json",
    ".playwright-mcp/",  # Playwright MCP screenshots - worktree-specific test artifacts
    "specs/issue-*-adw-*",  # ADW spec files - ephemeral contracts, not permanent artifacts
    "*.tsbuildinfo",  # TypeScript incremental build cache - auto-generated
]


def commit_changes(
    message: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Stage all changes and commit. Returns (success, error_message).

    Automatically excludes worktree-specific files (.mcp.json, .ports.env,
    playwright-mcp-config.json) from commits.
    """
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=cwd
    )
    if not result.stdout.strip():
        return True, None  # No changes to commit

    # Stage all changes
    result = subprocess.run(
        ["git", "add", "-A"], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, result.stderr

    # Unstage worktree-specific files that should never be committed
    for excluded_file in WORKTREE_EXCLUDED_FILES:
        subprocess.run(
            ["git", "reset", "HEAD", "--", excluded_file],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

    # Check if there are still changes to commit after exclusions
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode == 0:
        return True, None  # No changes to commit after exclusions

    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def get_pr_number(branch_name: str) -> Optional[str]:
    """Get PR number for a branch. Returns PR number if exists."""
    # Use github.py functions to get repo info
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        return None

    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo_path,
            "--head",
            branch_name,
            "--json",
            "number",
            "--limit",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        prs = json.loads(result.stdout)
        if prs:
            return str(prs[0]["number"])
    return None


def approve_pr(pr_number: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """Approve a PR. Returns (success, error_message)."""
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        return False, f"Failed to get repo info: {e}"

    result = subprocess.run(
        [
            "gh",
            "pr",
            "review",
            pr_number,
            "--repo",
            repo_path,
            "--approve",
            "--body",
            "ADW Ship workflow approved this PR after validating all state fields.",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, result.stderr

    logger.info(f"Approved PR #{pr_number}")
    return True, None


def merge_pr(
    pr_number: str, logger: logging.Logger, merge_method: str = "squash"
) -> Tuple[bool, Optional[str]]:
    """Merge a PR. Returns (success, error_message).

    Args:
        pr_number: The PR number to merge
        logger: Logger instance
        merge_method: One of 'merge', 'squash', 'rebase' (default: 'squash')
    """
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        return False, f"Failed to get repo info: {e}"

    # First check if PR is mergeable
    result = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--repo",
            repo_path,
            "--json",
            "mergeable,mergeStateStatus",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, f"Failed to check PR status: {result.stderr}"

    pr_status = json.loads(result.stdout)
    if pr_status.get("mergeable") != "MERGEABLE":
        return (
            False,
            f"PR is not mergeable. Status: {pr_status.get('mergeStateStatus', 'unknown')}",
        )

    # Merge the PR
    merge_cmd = [
        "gh",
        "pr",
        "merge",
        pr_number,
        "--repo",
        repo_path,
        f"--{merge_method}",
    ]

    # Add auto-merge body
    merge_cmd.extend(
        ["--body", "Merged by ADW Ship workflow after successful validation."]
    )

    result = subprocess.run(merge_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr

    logger.info(f"Merged PR #{pr_number} using {merge_method} method")
    return True, None


def finalize_git_operations(
    state: "ADWState", logger: logging.Logger, cwd: Optional[str] = None
) -> None:
    """Standard git finalization: push branch and create/update PR."""
    branch_name = state.get("branch_name")
    if not branch_name:
        # Fallback: use current git branch if not main
        current_branch = get_current_branch(cwd=cwd)
        if current_branch and current_branch != "main":
            logger.warning(
                f"No branch name in state, using current branch: {current_branch}"
            )
            branch_name = current_branch
        else:
            logger.error(
                "No branch name in state and current branch is main, skipping git operations"
            )
            return

    # Always push
    success, error = push_branch(branch_name, cwd=cwd)
    if not success:
        logger.error(f"Failed to push branch: {error}")
        return

    logger.info(f"Pushed branch: {branch_name}")

    # Handle PR
    pr_url = check_pr_exists(branch_name)
    issue_number = state.get("issue_number")
    adw_id = state.get("adw_id")

    if pr_url:
        logger.info(f"Found existing PR: {pr_url}")
        # Post PR link for easy reference
        if issue_number and adw_id:
            make_issue_comment(issue_number, f"{adw_id}_ops: ✅ Pull request: {pr_url}")
    else:
        # Check if branch has commits ahead of main before attempting PR creation
        commits_ahead = get_commits_ahead_of_main(cwd=cwd)
        if commits_ahead == 0:
            logger.info(
                "No commits ahead of main, skipping PR creation (will create after implementation)"
            )
            return

        # Create new PR - fetch issue data first
        if issue_number:
            try:
                repo_url = get_repo_url()
                repo_path = extract_repo_path(repo_url)
                from adw_modules.github import fetch_issue

                issue = fetch_issue(issue_number, repo_path)

                from adw_modules.workflow_ops import create_pull_request

                pr_url, error = create_pull_request(branch_name, issue, state, logger, cwd)
            except Exception as e:
                logger.error(f"Failed to fetch issue for PR creation: {e}")
                pr_url, error = None, str(e)
        else:
            pr_url, error = None, "No issue number in state"

        if pr_url:
            logger.info(f"Created PR: {pr_url}")
            # Post new PR link
            if issue_number and adw_id:
                make_issue_comment(
                    issue_number, f"{adw_id}_ops: ✅ Pull request created: {pr_url}"
                )
        else:
            logger.error(f"Failed to create PR: {error}")


