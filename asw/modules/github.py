#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
GitHub Operations Module - ASW (Agentic Software Workflow)

This module contains all GitHub-related operations including:
- Issue fetching and manipulation
- Comment posting
- Repository path extraction
- Issue status management

Supports both application (app) and infrastructure (io) workflows.
"""

import subprocess
import sys
import os
import json
import time
import logging
from typing import Dict, List, Optional, Callable, TypeVar
from .data_types import GitHubIssue, GitHubIssueListItem, GitHubComment

T = TypeVar('T')

# Bot identifiers to prevent webhook loops and filter bot comments
ASW_APP_BOT_IDENTIFIER = "[ASW-APP-AGENTS]"
ASW_IO_BOT_IDENTIFIER = "[ASW-IO-AGENTS]"

# Legacy aliases for backward compatibility
ADW_BOT_IDENTIFIER = ASW_APP_BOT_IDENTIFIER
IPE_BOT_IDENTIFIER = ASW_IO_BOT_IDENTIFIER


def get_github_env() -> Optional[dict]:
    """Get environment with GitHub token set up. Returns None if no GITHUB_PAT.

    Subprocess env behavior:
    - env=None -> Inherits parent's environment (default)
    - env={} -> Empty environment (no variables)
    - env=custom_dict -> Only uses specified variables

    So this will work with gh authentication:
    # These are equivalent:
    result = subprocess.run(cmd, capture_output=True, text=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=None)

    But this will NOT work (no PATH, no auth):
    result = subprocess.run(cmd, capture_output=True, text=True, env={})
    """
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        return None

    # Only create minimal env with GitHub token
    env = {
        "GH_TOKEN": github_pat,
        "PATH": os.environ.get("PATH", ""),
    }
    return env


def is_retryable_github_error(stderr: str) -> tuple[bool, str]:
    """Classify a GitHub CLI error and determine if it's retryable.

    Args:
        stderr: The stderr output from gh CLI command

    Returns:
        Tuple of (is_retryable, error_category)
        - is_retryable: True if the error is likely transient
        - error_category: One of 'network', 'timeout', 'rate_limit', 'server', 'auth', 'not_found', 'unknown'
    """
    stderr_lower = stderr.lower()

    # Network connectivity errors - RETRYABLE
    network_indicators = [
        "error connecting",
        "connection refused",
        "connection reset",
        "connection timed out",
        "network is unreachable",
        "no route to host",
        "dns resolution failed",
        "temporary failure in name resolution",
        "could not resolve host",
        "getaddrinfo",
    ]

    for indicator in network_indicators:
        if indicator in stderr_lower:
            return True, "network"

    # Timeout errors - RETRYABLE
    if "timeout" in stderr_lower or "timed out" in stderr_lower:
        return True, "timeout"

    # Rate limiting - RETRYABLE (with longer delay)
    if "rate limit" in stderr_lower or "api rate limit" in stderr_lower:
        return True, "rate_limit"

    # Server errors (5xx) - RETRYABLE
    if "500" in stderr or "502" in stderr or "503" in stderr or "504" in stderr:
        return True, "server"
    if "internal server error" in stderr_lower or "bad gateway" in stderr_lower:
        return True, "server"

    # Authentication errors - NOT RETRYABLE
    if "authentication" in stderr_lower or "401" in stderr or "403" in stderr:
        if "rate limit" not in stderr_lower:  # 403 for rate limit is retryable
            return False, "auth"

    # Not found errors - NOT RETRYABLE
    if "404" in stderr or "not found" in stderr_lower:
        return False, "not_found"

    # Unknown error - default to NOT RETRYABLE
    return False, "unknown"


def github_operation_with_retry(
    operation: Callable[[], T],
    operation_name: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    logger: logging.Logger = None,
) -> T:
    """Execute a GitHub operation with exponential backoff retry logic.

    Args:
        operation: Callable that performs the GitHub operation
        operation_name: Human-readable name for logging (e.g., "post comment")
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 30.0)
        logger: Optional logger for retry messages

    Returns:
        The result of the operation

    Raises:
        RuntimeError: If operation fails after all retries
    """
    last_error = None

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            return operation()
        except RuntimeError as e:
            error_str = str(e)
            is_retryable, error_category = is_retryable_github_error(error_str)

            if not is_retryable:
                # Non-retryable error - fail immediately
                raise

            last_error = e

            if attempt < max_retries:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                # Add extra delay for rate limiting
                if error_category == "rate_limit":
                    delay = min(delay * 4, max_delay * 2)  # Longer delay for rate limits

                if logger:
                    logger.warning(
                        f"GitHub {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}, "
                        f"category: {error_category}). Retrying in {delay:.1f}s..."
                    )
                else:
                    print(
                        f"Warning: GitHub {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {delay:.1f}s..."
                    )

                time.sleep(delay)
            else:
                # Final attempt failed
                if logger:
                    logger.error(
                        f"GitHub {operation_name} failed after {max_retries + 1} attempts: {error_str}"
                    )

    # Should not reach here, but raise last error if we do
    raise last_error or RuntimeError(f"GitHub {operation_name} failed after retries")


def get_repo_url() -> str:
    """Get GitHub repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(
            "No git remote 'origin' found. Please ensure you're in a git repository with a remote."
        )
    except FileNotFoundError:
        raise ValueError("git command not found. Please ensure git is installed.")


def extract_repo_path(github_url: str) -> str:
    """Extract owner/repo from GitHub URL."""
    # Handle both https://github.com/owner/repo and https://github.com/owner/repo.git
    return github_url.replace("https://github.com/", "").replace(".git", "")


def fetch_issue(
    issue_number: str,
    repo_path: str,
    logger: logging.Logger = None,
    max_retries: int = 3,
) -> GitHubIssue:
    """Fetch GitHub issue using gh CLI and return typed model with retry logic.

    Args:
        issue_number: The issue number to fetch
        repo_path: Repository path (owner/repo)
        logger: Optional logger for retry messages
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        GitHubIssue object

    Raises:
        SystemExit: If gh CLI is not installed or JSON parsing fails
        RuntimeError: If fetch fails after all retries
    """
    # Use JSON output for structured data
    cmd = [
        "gh",
        "issue",
        "view",
        issue_number,
        "-R",
        repo_path,
        "--json",
        "number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    def _fetch():
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            issue_data = json.loads(result.stdout)
            return GitHubIssue(**issue_data)
        else:
            raise RuntimeError(f"Failed to fetch issue: {result.stderr}")

    try:
        return github_operation_with_retry(
            operation=_fetch,
            operation_name=f"fetch issue #{issue_number}",
            max_retries=max_retries,
            logger=logger,
        )
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        print("\nTo install gh:", file=sys.stderr)
        print("  - macOS: brew install gh", file=sys.stderr)
        print(
            "  - Linux: See https://github.com/cli/cli#installation",
            file=sys.stderr,
        )
        print(
            "  - Windows: See https://github.com/cli/cli#installation", file=sys.stderr
        )
        print("\nAfter installation, authenticate with: gh auth login", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing issue data: {e}", file=sys.stderr)
        sys.exit(1)


def _make_issue_comment_internal(
    issue_id: str,
    comment: str,
    repo_path: str,
    env: Optional[dict]
) -> None:
    """Internal function to post a comment to a GitHub issue.

    This is the actual implementation; use make_issue_comment() for retry-wrapped version.
    """
    # Build command
    cmd = [
        "gh",
        "issue",
        "comment",
        issue_id,
        "-R",
        repo_path,
        "--body",
        comment,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"Successfully posted comment to issue #{issue_id}")
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            raise RuntimeError(f"Failed to post comment: {result.stderr}")
    except FileNotFoundError:
        raise RuntimeError("GitHub CLI (gh) is not installed")


def make_issue_comment(
    issue_id: str,
    comment: str,
    logger: logging.Logger = None,
    max_retries: int = 3,
    bot_identifier: str = None,
) -> None:
    """Post a comment to a GitHub issue using gh CLI with retry logic.

    Args:
        issue_id: The issue number to comment on
        comment: The comment body
        logger: Optional logger for retry messages
        max_retries: Maximum retry attempts (default: 3)
        bot_identifier: Bot identifier to prepend (default: ASW_APP_BOT_IDENTIFIER)
    """
    # Get repo information from git remote
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Use provided bot identifier or default
    identifier = bot_identifier or ASW_APP_BOT_IDENTIFIER

    # Ensure comment has bot identifier to prevent webhook loops
    if not comment.startswith(identifier) and not comment.startswith(ASW_APP_BOT_IDENTIFIER) and not comment.startswith(ASW_IO_BOT_IDENTIFIER):
        comment = f"{identifier} {comment}"

    # Set up environment with GitHub token if available
    env = get_github_env()

    # Use retry wrapper
    github_operation_with_retry(
        operation=lambda: _make_issue_comment_internal(issue_id, comment, repo_path, env),
        operation_name=f"post comment to issue #{issue_id}",
        max_retries=max_retries,
        logger=logger,
    )


def mark_issue_in_progress(issue_id: str) -> None:
    """Mark issue as in progress by adding label and comment."""
    # Get repo information from git remote
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Add "in_progress" label
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-label",
        "in_progress",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    # Try to add label (may fail if label doesn't exist)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Note: Could not add 'in_progress' label: {result.stderr}")

    # Assign to self (optional)
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-assignee",
        "@me",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"Assigned issue #{issue_id} to self")


def fetch_open_issues(
    repo_path: str,
    logger: logging.Logger = None,
    max_retries: int = 3,
) -> List[GitHubIssueListItem]:
    """Fetch all open issues from the GitHub repository with retry logic.

    Args:
        repo_path: Repository path (owner/repo)
        logger: Optional logger for retry messages
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        List of GitHubIssueListItem objects, empty list on failure
    """
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo_path,
        "--state",
        "open",
        "--json",
        "number,title,body,labels,createdAt,updatedAt",
        "--limit",
        "1000",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    def _fetch():
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            issues_data = json.loads(result.stdout)
            return [GitHubIssueListItem(**issue_data) for issue_data in issues_data]
        else:
            raise RuntimeError(f"Failed to fetch issues: {result.stderr}")

    try:
        issues = github_operation_with_retry(
            operation=_fetch,
            operation_name="fetch open issues",
            max_retries=max_retries,
            logger=logger,
        )
        print(f"Fetched {len(issues)} open issues")
        return issues
    except RuntimeError as e:
        print(f"ERROR: Failed to fetch issues: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse issues JSON: {e}", file=sys.stderr)
        return []


def fetch_issue_comments(
    repo_path: str,
    issue_number: int,
    logger: logging.Logger = None,
    max_retries: int = 3,
) -> List[Dict]:
    """Fetch all comments for a specific issue with retry logic.

    Args:
        repo_path: Repository path (owner/repo)
        issue_number: Issue number to fetch comments for
        logger: Optional logger for retry messages
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        List of comment dictionaries, empty list on failure
    """
    cmd = [
        "gh",
        "issue",
        "view",
        str(issue_number),
        "--repo",
        repo_path,
        "--json",
        "comments",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    def _fetch():
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            comments = data.get("comments", [])
            # Sort comments by creation time
            comments.sort(key=lambda c: c.get("createdAt", ""))
            return comments
        else:
            raise RuntimeError(f"Failed to fetch comments: {result.stderr}")

    try:
        return github_operation_with_retry(
            operation=_fetch,
            operation_name=f"fetch comments for issue #{issue_number}",
            max_retries=max_retries,
            logger=logger,
        )
    except RuntimeError as e:
        print(
            f"ERROR: Failed to fetch comments for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Failed to parse comments JSON for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []


def find_keyword_from_comment(keyword: str, issue: GitHubIssue, bot_identifiers: List[str] = None) -> Optional[GitHubComment]:
    """Find the latest comment containing a specific keyword.

    Args:
        keyword: The keyword to search for in comments
        issue: The GitHub issue containing comments
        bot_identifiers: List of bot identifiers to skip (default: ASW bot identifiers)

    Returns:
        The latest GitHubComment containing the keyword, or None if not found
    """
    if bot_identifiers is None:
        bot_identifiers = [ASW_APP_BOT_IDENTIFIER, ASW_IO_BOT_IDENTIFIER]

    # Sort comments by created_at date (newest first)
    sorted_comments = sorted(issue.comments, key=lambda c: c.created_at, reverse=True)

    # Search through sorted comments (newest first)
    for comment in sorted_comments:
        # Skip bot comments to prevent loops
        skip = False
        for identifier in bot_identifiers:
            if identifier in comment.body:
                skip = True
                break
        if skip:
            continue

        if keyword in comment.body:
            return comment

    return None


def get_issue_description(issue_number: str) -> Optional[str]:
    """Fetch GitHub issue description using gh CLI.

    Args:
        issue_number: The issue number to fetch

    Returns:
        The issue body/description text, or None if error occurs
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "view", issue_number, "--json", "body", "-q", ".body"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: Could not fetch issue description: {e}")
        return None
