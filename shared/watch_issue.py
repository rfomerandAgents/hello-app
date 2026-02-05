#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "schedule",
#     "python-dotenv",
#     "pydantic",
# ]
# ///

"""
Watch a GitHub issue until completion.

Polls a specific GitHub issue at regular intervals and displays
status changes until the issue is closed or user interrupts.

Usage:
    uv run shared/watch_issue.py <issue-number>
"""

import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import schedule
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import GitHub operations from unified ASW modules
from asw.modules import (
    fetch_issue,
    get_repo_url,
    extract_repo_path,
)


def parse_arguments() -> int:
    """Parse and validate command-line arguments.

    Returns:
        int: The issue number to watch

    Raises:
        SystemExit: If arguments are invalid or help is requested
    """
    if len(sys.argv) < 2:
        print("Error: Issue number is required", file=sys.stderr)
        print("\nUsage: uv run shared/watch_issue.py <issue-number>", file=sys.stderr)
        print("\nExample: uv run shared/watch_issue.py 42", file=sys.stderr)
        sys.exit(1)

    # Support --help flag
    if sys.argv[1] in ["--help", "-h"]:
        print(__doc__)
        print("\nUsage: uv run shared/watch_issue.py <issue-number>")
        print("\nArguments:")
        print("  <issue-number>  GitHub issue number to watch")
        print("\nOptions:")
        print("  --help, -h     Show this help message")
        print("\nExample:")
        print("  uv run shared/watch_issue.py 42")
        print("\nThe script will poll the issue every 30 seconds and display")
        print("status updates until the issue is closed or you press Ctrl+C.")
        sys.exit(0)

    # Validate issue number is integer
    try:
        issue_number = int(sys.argv[1])
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")
        return issue_number
    except ValueError as e:
        print(f"Error: Invalid issue number '{sys.argv[1]}'", file=sys.stderr)
        print(f"Issue number must be a positive integer", file=sys.stderr)
        sys.exit(1)


def detect_changes(old_issue, new_issue) -> Dict[str, Any]:
    """Detect what changed between two issue states.

    Args:
        old_issue: Previous issue state (None for first fetch)
        new_issue: Current issue state (GitHubIssue model)

    Returns:
        Dictionary of changes with keys:
            - changed (bool): Whether any changes were detected
            - fields (list): List of field names that changed
            - messages (list): Human-readable change messages
    """
    if old_issue is None:
        return {
            "changed": True,
            "fields": ["initial"],
            "messages": [f"Started watching issue #{new_issue.number}: {new_issue.title}"]
        }

    changes = {
        "changed": False,
        "fields": [],
        "messages": []
    }

    # Check state change (open -> closed, etc.)
    if old_issue.state != new_issue.state:
        changes["changed"] = True
        changes["fields"].append("state")
        changes["messages"].append(
            f"State changed: {old_issue.state} → {new_issue.state}"
        )

    # Check assignees
    old_assignees = {a.get("login") for a in (old_issue.assignees or [])}
    new_assignees = {a.get("login") for a in (new_issue.assignees or [])}
    if old_assignees != new_assignees:
        changes["changed"] = True
        changes["fields"].append("assignees")
        added = new_assignees - old_assignees
        removed = old_assignees - new_assignees
        if added:
            changes["messages"].append(f"Assigned to: {', '.join(added)}")
        if removed:
            changes["messages"].append(f"Unassigned from: {', '.join(removed)}")

    # Check labels
    old_labels = {label.get("name") for label in (old_issue.labels or [])}
    new_labels = {label.get("name") for label in (new_issue.labels or [])}
    if old_labels != new_labels:
        changes["changed"] = True
        changes["fields"].append("labels")
        added = new_labels - old_labels
        removed = old_labels - new_labels
        if added:
            changes["messages"].append(f"Labels added: {', '.join(added)}")
        if removed:
            changes["messages"].append(f"Labels removed: {', '.join(removed)}")

    # Check comments count
    old_comment_count = len(old_issue.comments or [])
    new_comment_count = len(new_issue.comments or [])
    if old_comment_count != new_comment_count:
        changes["changed"] = True
        changes["fields"].append("comments")
        diff = new_comment_count - old_comment_count
        changes["messages"].append(f"New comments: {diff} comment(s) added")

        # Show preview of latest comment
        if new_issue.comments:
            latest = new_issue.comments[-1]
            author = latest.get("author", {}).get("login", "unknown")
            body_preview = latest.get("body", "")[:100]
            if len(latest.get("body", "")) > 100:
                body_preview += "..."
            changes["messages"].append(f"  └─ {author}: {body_preview}")

    # Check updated_at timestamp (catch-all for other changes)
    if old_issue.updated_at != new_issue.updated_at and not changes["changed"]:
        changes["changed"] = True
        changes["fields"].append("updated")
        changes["messages"].append("Issue was updated (timestamp changed)")

    return changes


# Graceful shutdown flag
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully.

    Args:
        signum: Signal number received
        frame: Current stack frame
    """
    global shutdown_requested
    signal_name = "SIGINT" if signum == signal.SIGINT else f"Signal {signum}"
    print(f"\n\nReceived {signal_name}, stopping watch...")
    print("Gracefully shutting down...")
    shutdown_requested = True


# Global state for tracking
previous_issue_state = None
repo_path = ""
issue_number_global = 0
poll_count = 0

def poll_issue():
    """Poll the GitHub issue and display any changes.

    This function is called periodically by the scheduler. It fetches the
    current issue state, compares it to the previous state, and displays
    any changes detected.
    """
    global previous_issue_state, poll_count, shutdown_requested

    if shutdown_requested:
        return

    poll_count += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Fetch current issue state
        current_issue = fetch_issue(str(issue_number_global), repo_path)

        # Detect changes
        changes = detect_changes(previous_issue_state, current_issue)

        # Display changes if any
        if changes["changed"]:
            print(f"\n[{timestamp}] Poll #{poll_count} - Changes detected:")
            for msg in changes["messages"]:
                print(f"  • {msg}")

            # Check if issue was closed
            if current_issue.state == "CLOSED":
                print(f"\n✓ Issue #{issue_number_global} has been closed!")
                print(f"  Title: {current_issue.title}")
                print(f"  Closed at: {current_issue.closed_at or 'unknown'}")
                print(f"\nStopping watch...")
                shutdown_requested = True
                return
        else:
            # No changes - print minimal output
            print(f"[{timestamp}] Poll #{poll_count} - No changes (state: {current_issue.state})", end="\r")
            sys.stdout.flush()

        # Update previous state
        previous_issue_state = current_issue

    except Exception as e:
        print(f"\n[{timestamp}] Poll #{poll_count} - Error: {e}", file=sys.stderr)
        # Don't shutdown on errors - keep trying


def main():
    """Main entry point for issue watcher.

    Sets up the issue watching session, registers signal handlers,
    schedules periodic polling, and runs the main event loop.
    """
    global repo_path, issue_number_global

    # Parse arguments
    issue_number_global = parse_arguments()

    # Get repository information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Print banner
    print("=" * 60)
    print(f"GitHub Issue Watcher")
    print("=" * 60)
    print(f"Repository: {repo_path}")
    print(f"Issue Number: #{issue_number_global}")
    print(f"Poll Interval: 30 seconds")
    print(f"Press Ctrl+C to stop watching")
    print("=" * 60)
    print()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Schedule polling every 30 seconds
    schedule.every(30).seconds.do(poll_issue)

    # Run initial poll immediately
    print("Fetching initial issue state...")
    poll_issue()

    # Check if already closed on first fetch
    if shutdown_requested:
        return

    # Main loop
    print("\nWatching for changes...\n")
    while not shutdown_requested:
        schedule.run_pending()
        time.sleep(1)

    # Cleanup message
    print("\n" + "=" * 60)
    print(f"Watched issue #{issue_number_global} for {poll_count} polls")
    print("Watch session ended")
    print("=" * 60)

if __name__ == "__main__":
    main()
