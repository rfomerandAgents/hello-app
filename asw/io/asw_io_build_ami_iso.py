#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ASW IO Build AMI Iso - Worktree-Based AMI Builder

Triggers GitHub Actions AMI builds from isolated worktree context.

Usage: uv run asw_io_build_ami_iso.py <issue-number> <asw-id>

Workflow:
1. Load IPEState and validate worktree
2. Extract environment and version from state
3. Trigger infrastructure-deploy.yml in build-ami-only mode
4. Poll until completion
5. Extract AMI ID from artifacts
6. Update state with results
7. Post to GitHub issue

BEHAVIORAL DIFFERENCES FROM ipe_build.py:
- State Management: Full IPEState vs CLI args only
- GitHub Integration: Posts issue comments vs none
- Branch Selection: Uses state.branch_name vs --branch flag
- Workflow Chaining: Part of SDLC chain vs standalone
- Error Handling: GitHub comments + state vs exit codes
- Execution Context: Runs in isolated worktree vs main repo

This workflow REQUIRES that asw_io_plan_iso.py has been run first
to create the worktree and state. It cannot create worktrees itself.
"""

import sys
import os
import logging
import json
import subprocess
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Add paths for imports
repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'ipe'))

from ipe.ipe_modules.ipe_state import IPEState
from ipe.ipe_modules.ipe_worktree_ops import validate_worktree
from ipe.ipe_modules.ipe_github import make_issue_comment, get_repo_url, extract_repo_path
from ipe.ipe_modules.ipe_utils import setup_logger, check_env_vars

# Reuse from standalone ipe_build.py
from ipe.ipe_build import (
    check_github_cli,
    trigger_build_ami_workflow,
    poll_workflow_status,
    get_build_details_from_workflow,
    BuildOptions,
    BuildResult
)

# Constants
AGENT_AMI_BUILDER = "ipe_build_ami_iso"
DEFAULT_BUILD_TIMEOUT_MINUTES = 45
DEFAULT_POLL_INTERVAL_SECONDS = 15
VALID_VERSION_STRATEGIES = ["git-describe", "semantic", "commit-hash", "timestamp"]
VALID_ENVIRONMENTS = ["dev", "staging", "prod", "sandbox"]


def format_issue_message(ipe_id: str, agent: str, message: str) -> str:
    """Format message for GitHub issue comment.

    Args:
        ipe_id: The IPE workflow ID
        agent: Agent identifier (e.g., "ops", "ami_builder")
        message: Message content

    Returns:
        Formatted message string
    """
    return f"{ipe_id}_{agent}: {message}"


def validate_state_for_ami_build(
    state: IPEState,
    logger: logging.Logger
) -> tuple[bool, Optional[str]]:
    """Validate state has required fields for AMI building.

    Required: branch_name, environment, worktree_path, issue_number
    Optional: ami_version, version_strategy

    Args:
        state: IPE state object
        logger: Logger instance

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["branch_name", "environment", "worktree_path", "issue_number"]

    for field in required_fields:
        if not state.get(field):
            error_msg = f"Missing required field: {field}"
            logger.error(error_msg)
            return False, error_msg

    environment = state.get("environment")
    if environment not in VALID_ENVIRONMENTS:
        error_msg = f"Invalid environment '{environment}'. Must be one of: {VALID_ENVIRONMENTS}"
        logger.error(error_msg)
        return False, error_msg

    version_strategy = state.get("version_strategy")
    if version_strategy and version_strategy not in VALID_VERSION_STRATEGIES:
        error_msg = f"Invalid version_strategy '{version_strategy}'. Must be one of: {VALID_VERSION_STRATEGIES}"
        logger.error(error_msg)
        return False, error_msg

    logger.info("State validation passed for AMI build")
    return True, None


def build_options_from_state(state: IPEState, logger: logging.Logger) -> BuildOptions:
    """Convert IPEState to BuildOptions for ipe_build.py functions.

    Args:
        state: IPE state object
        logger: Logger instance

    Returns:
        BuildOptions object configured from state
    """
    options = BuildOptions(
        version=state.get("ami_version"),
        version_strategy=state.get("version_strategy", "git-describe"),
        environment=state.get("environment", "sandbox"),
        branch=state.get("branch_name", "main"),
        wait=True,  # Always wait in worktree mode
        timeout=state.get("build_timeout", DEFAULT_BUILD_TIMEOUT_MINUTES),
        poll_interval=DEFAULT_POLL_INTERVAL_SECONDS,
        ipe_id=state.get("ipe_id"),
        output_format="text"
    )

    logger.info(f"Built options from state: env={options.environment}, branch={options.branch}, version_strategy={options.version_strategy}")
    return options


def trigger_ami_build_with_state(
    state: IPEState,
    logger: logging.Logger
) -> BuildResult:
    """Trigger AMI build using state configuration and post updates to GitHub.

    Args:
        state: IPE state object
        logger: Logger instance

    Returns:
        BuildResult with success status and AMI details
    """
    issue_number = state.get("issue_number")
    ipe_id = state.get("ipe_id")

    # Post initial status
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_AMI_BUILDER, "Starting AMI build workflow")
    )

    # Check GitHub CLI
    if not check_github_cli(logger):
        error_msg = "GitHub CLI not available or not authenticated"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_AMI_BUILDER, f"❌ {error_msg}")
        )
        return BuildResult(
            success=False,
            environment=state.get("environment", "sandbox"),
            error_message=error_msg
        )

    # Build options from state
    options = build_options_from_state(state, logger)

    # Log configuration
    logger.info("=" * 60)
    logger.info("ASW IO Build AMI Iso - Worktree-Based AMI Builder")
    logger.info("=" * 60)
    logger.info(f"IPE ID:           {ipe_id}")
    logger.info(f"Issue:            #{issue_number}")
    logger.info(f"Environment:      {options.environment}")
    logger.info(f"Branch:           {options.branch}")
    logger.info(f"Version Strategy: {options.version_strategy}")
    if options.version:
        logger.info(f"Custom Version:   {options.version}")
    logger.info(f"Worktree:         {state.get('worktree_path')}")
    logger.info("=" * 60)

    make_issue_comment(
        issue_number,
        format_issue_message(
            ipe_id,
            AGENT_AMI_BUILDER,
            f"Configuration:\n- Environment: {options.environment}\n- Branch: {options.branch}\n- Version Strategy: {options.version_strategy}"
        )
    )

    # Trigger workflow
    start_time = time.time()
    run_id = trigger_build_ami_workflow(options, logger)

    if not run_id:
        error_msg = "Failed to trigger GitHub Actions workflow"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_AMI_BUILDER, f"❌ {error_msg}")
        )
        return BuildResult(
            success=False,
            environment=options.environment,
            error_message=error_msg
        )

    # Get run URL
    try:
        repo_result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True, text=True
        )
        repo_name = repo_result.stdout.strip() if repo_result.returncode == 0 else "unknown"
        run_url = f"https://github.com/{repo_name}/actions/runs/{run_id}"

        logger.info(f"Workflow URL: {run_url}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_AMI_BUILDER, f"Workflow triggered: {run_url}")
        )
    except Exception as e:
        logger.warning(f"Failed to get workflow URL: {e}")
        run_url = None

    # Poll for completion
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_AMI_BUILDER, "Polling workflow status...")
    )

    success, conclusion = poll_workflow_status(
        run_id, options.timeout, options.poll_interval, logger
    )

    duration = int(time.time() - start_time)

    if not success:
        error_msg = f"Workflow failed: {conclusion}"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_AMI_BUILDER, f"❌ {error_msg}")
        )
        return BuildResult(
            success=False,
            run_id=run_id,
            run_url=run_url,
            environment=options.environment,
            error_message=error_msg,
            duration_seconds=duration
        )

    # Extract build details
    logger.info("Workflow completed successfully, extracting AMI details...")
    details = get_build_details_from_workflow(run_id, logger)

    result = BuildResult(
        success=True,
        ami_id=details.get("ami_id"),
        ami_name=details.get("ami_name"),
        version=details.get("version") or options.version,
        run_id=run_id,
        run_url=run_url,
        environment=options.environment,
        duration_seconds=duration
    )

    # Post success message
    duration_min = duration // 60
    duration_sec = duration % 60
    success_msg = f"✅ AMI build completed successfully!\n"
    if result.ami_id:
        success_msg += f"- AMI ID: {result.ami_id}\n"
    if result.ami_name:
        success_msg += f"- AMI Name: {result.ami_name}\n"
    success_msg += f"- Environment: {result.environment}\n"
    success_msg += f"- Duration: {duration_min}m {duration_sec}s\n"
    if run_url:
        success_msg += f"- Workflow: {run_url}"

    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_AMI_BUILDER, success_msg)
    )

    logger.info("AMI build completed successfully")
    return result


def update_state_with_ami_result(
    state: IPEState,
    result: BuildResult,
    logger: logging.Logger
) -> None:
    """Save AMI build results to artifact file.

    Note: IPEState schema doesn't support AMI fields, so we save to a separate artifact file.

    Args:
        state: IPE state object
        result: Build result to save
        logger: Logger instance
    """
    ipe_id = state.get("ipe_id")

    # Determine agents directory location
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ami_results_path = os.path.join(project_root, "agents", ipe_id, "ami_build_result.json")

    # Ensure directory exists
    os.makedirs(os.path.dirname(ami_results_path), exist_ok=True)

    # Save AMI results
    ami_data = {
        "ami_id": result.ami_id,
        "ami_name": result.ami_name,
        "ami_version": result.version,
        "run_id": result.run_id,
        "run_url": result.run_url,
        "environment": result.environment,
        "duration_seconds": result.duration_seconds,
        "timestamp": time.time(),
        "success": result.success,
    }

    with open(ami_results_path, "w") as f:
        json.dump(ami_data, f, indent=2)

    logger.info(f"Saved AMI build results to {ami_results_path}")

    # Track that this workflow ran
    state.append_asw_id(AGENT_AMI_BUILDER)
    state.save(AGENT_AMI_BUILDER)
    logger.info("Updated state with AMI builder workflow")


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 3:
        print("Usage: uv run asw_io_build_ami_iso.py <issue-number> <asw-id>")
        print("\nError: Both issue-number and ipe-id are required")
        print("Run asw_io_plan_iso.py first to create the worktree and state")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2]

    # Setup logger
    logger = setup_logger(ipe_id, AGENT_AMI_BUILDER)
    logger.info(f"ASW IO Build AMI Iso starting - ID: {ipe_id}, Issue: #{issue_number}")

    # Validate environment
    try:
        check_env_vars(logger)
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        sys.exit(1)

    # Load existing state
    state = ASWIOState.load(ipe_id, logger)
    if not state:
        error_msg = f"No state found for IPE ID: {ipe_id}"
        logger.error(error_msg)
        logger.error("Run asw_io_plan_iso.py first to create the worktree and state")
        print(f"\nError: {error_msg}")
        print("Run asw_io_plan_iso.py first to create the worktree and state")
        sys.exit(1)

    # Update issue number in case it's different
    if state.get("issue_number") != issue_number:
        logger.info(f"Updating issue number from state: {state.get('issue_number')} -> {issue_number}")
        state.update(issue_number=issue_number)

    # Post initial comment
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", f"🔍 Found existing state - resuming AMI build\n```json\n{json.dumps(state.data, indent=2)}\n```")
    )

    # Validate worktree exists
    valid, error = validate_worktree(ipe_id, state)
    if not valid:
        error_msg = f"Worktree validation failed: {error}"
        logger.error(error_msg)
        logger.error("Run asw_io_plan_iso.py first to create the worktree")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error_msg}\nRun asw_io_plan_iso.py first")
        )
        sys.exit(1)

    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")

    # Validate state has required fields for AMI build
    valid, error = validate_state_for_ami_build(state, logger)
    if not valid:
        error_msg = f"State validation failed: {error}"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    # Post start message
    make_issue_comment(
        issue_number,
        format_issue_message(
            ipe_id,
            "ops",
            f"✅ Starting AMI build phase\n🏠 Worktree: {worktree_path}\n🌍 Environment: {state.get('environment')}"
        )
    )

    # Trigger AMI build
    logger.info("Triggering AMI build with state configuration")
    result = trigger_ami_build_with_state(state, logger)

    if not result.success:
        logger.error(f"AMI build failed: {result.error_message}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ AMI build phase failed: {result.error_message}")
        )
        sys.exit(1)

    # Update state with results
    logger.info("Updating state with AMI build results")
    update_state_with_ami_result(state, result, logger)

    # Post completion message
    logger.info("AMI build phase completed successfully")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", "✅ AMI build phase completed")
    )

    # Post final state summary
    make_issue_comment(
        issue_number,
        f"{ipe_id}_ops: 📋 Final state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )

    logger.info(f"ASW IO Build AMI Iso completed - ID: {ipe_id}")


if __name__ == "__main__":
    main()
