#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "claude-agent-sdk"]
# ///

"""
ASW IO Build Iso - Infrastructure Platform Engineer workflow for agentic building in isolated worktrees

Usage:
  uv run asw_io_build_iso.py <issue-number> <asw-id>

Workflow:
1. Load state and validate worktree exists
2. Find existing plan (from state)
3. Implement the infrastructure solution based on plan in worktree
4. Run terraform fmt and validate after implementation
5. Commit implementation in worktree
6. Push and update PR

This workflow REQUIRES that asw_io_plan_iso.py or asw_io_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.

BEHAVIORAL DIFFERENCES FROM ADW:
- No port allocation (infrastructure vs application)
- Uses spec_file instead of plan_file
- Automatically runs terraform fmt and validate after implementation
- Uses AGENT_BUILDER instead of AGENT_IMPLEMENTOR terminology
- Bot identifier is [🤖 IPE] instead of [🤖 ADW]
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional
from dotenv import load_dotenv

# Add paths for imports
repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'ipe'))

from ipe.ipe_modules.ipe_state import IPEState
from ipe.ipe_modules.ipe_git_ops import commit_changes, finalize_git_operations, get_current_branch
from ipe.ipe_modules.ipe_github import fetch_issue, make_issue_comment, get_repo_url, extract_repo_path
from ipe.ipe_modules.ipe_workflow_ops import (
    implement_plan,
    create_commit,
    format_issue_message,
    AGENT_BUILDER,
)
from ipe.ipe_modules.ipe_utils import setup_logger, check_env_vars
from ipe.ipe_modules.ipe_data_types import GitHubIssue
from ipe.ipe_modules.ipe_worktree_ops import validate_worktree




def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    # INTENTIONAL: ipe-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run asw_io_build_iso.py <issue-number> <asw-id>")
        print("\nError: ipe-id is required to locate the worktree and plan file")
        print("Run asw_io_plan_iso.py or asw_io_patch_iso.py first to create the worktree")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2]

    # Try to load existing state
    temp_logger = setup_logger(ipe_id, "ipe_build_iso")
    state = ASWIOState.load(ipe_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            f"{ipe_id}_ops: 🔍 Found existing state - resuming isolated build\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )
    else:
        # No existing state found
        logger = setup_logger(ipe_id, "ipe_build_iso")
        logger.error(f"No state found for IPE ID: {ipe_id}")
        logger.error("Run asw_io_plan_iso.py first to create the worktree and state")
        print(f"\nError: No state found for IPE ID: {ipe_id}")
        print("Run asw_io_plan_iso.py first to create the worktree and state")
        sys.exit(1)

    # Track that this IPE workflow has run
    state.append_asw_id("ipe_build_iso")

    # Set up logger with IPE ID from command line
    logger = setup_logger(ipe_id, "ipe_build_iso")
    logger.info(f"ASW IO Build Iso starting - ID: {ipe_id}, Issue: {issue_number}")

    # Validate environment
    check_env_vars(logger)

    # Validate worktree exists
    valid, error = validate_worktree(ipe_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        logger.error("Run asw_io_plan_iso.py or asw_io_patch_iso.py first")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ Worktree validation failed: {error}\n"
                               "Run asw_io_plan_iso.py or asw_io_patch_iso.py first")
        )
        sys.exit(1)

    # Get worktree path for explicit context
    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Ensure we have required state fields
    if not state.get("branch_name"):
        error_msg = "No branch name in state - run asw_io_plan_iso.py first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    if not state.get("spec_file"):
        error_msg = "No spec file in state - run asw_io_plan_iso.py first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    # Checkout the branch in the worktree
    branch_name = state.get("branch_name")
    result = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True, cwd=worktree_path)
    if result.returncode != 0:
        logger.error(f"Failed to checkout branch {branch_name} in worktree: {result.stderr}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ Failed to checkout branch {branch_name} in worktree")
        )
        sys.exit(1)
    logger.info(f"Checked out branch in worktree: {branch_name}")

    # Get the spec file from state (IPE uses spec_file not plan_file)
    spec_file = state.get("spec_file")
    logger.info(f"Using spec file: {spec_file}")

    # Get environment information for display
    environment = state.get("environment", "sandbox")

    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", f"✅ Starting isolated implementation phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🌍 Environment: {environment}")
    )

    # Implement the plan (executing in worktree)
    logger.info("Implementing infrastructure solution in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_BUILDER, "✅ Implementing infrastructure solution in isolated environment")
    )

    implement_response = implement_plan(spec_file, ipe_id, logger, working_dir=worktree_path)

    if not implement_response.success:
        logger.error(f"Error implementing solution: {implement_response.output}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_BUILDER, f"❌ Error implementing solution: {implement_response.output}")
        )
        sys.exit(1)

    logger.debug(f"Implementation response: {implement_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_BUILDER, "✅ Infrastructure solution implemented")
    )

    # Run terraform fmt to ensure proper formatting
    logger.info("Running terraform fmt")
    terraform_dir = state.get("terraform_dir") or "io/terraform"
    terraform_path = os.path.join(worktree_path, terraform_dir)

    if os.path.exists(terraform_path):
        fmt_result = subprocess.run(
            ["terraform", "fmt", "-recursive"],
            capture_output=True,
            text=True,
            cwd=terraform_path
        )
        if fmt_result.returncode == 0:
            logger.info("Terraform formatting completed")
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, "ops", "✅ Terraform formatting applied")
            )
        else:
            logger.warning(f"Terraform fmt warning: {fmt_result.stderr}")
    else:
        logger.info(f"No terraform directory found at {terraform_path}, skipping fmt")

    # Run terraform validate
    logger.info("Running terraform validate")
    if os.path.exists(terraform_path):
        # Set TF_WORKSPACE to avoid interactive prompt with Terraform Cloud
        env = os.environ.copy()
        workspace_name = f"{{{{PROJECT_SLUG}}}}-{environment}"
        env["TF_WORKSPACE"] = workspace_name
        logger.info(f"Using TFC workspace: {workspace_name}")

        # Initialize with Terraform Cloud backend
        init_result = subprocess.run(
            ["terraform", "init", "-input=false"],
            capture_output=True,
            text=True,
            cwd=terraform_path,
            env=env
        )

        if init_result.returncode != 0:
            logger.warning(f"Terraform init warning: {init_result.stderr}")

        validate_result = subprocess.run(
            ["terraform", "validate"],
            capture_output=True,
            text=True,
            cwd=terraform_path,
            env=env
        )
        if validate_result.returncode == 0:
            logger.info("Terraform validation passed")
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, "ops", "✅ Terraform validation passed")
            )
        else:
            logger.warning(f"Terraform validation warning: {validate_result.stderr}")
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, "ops", f"⚠️ Terraform validation warning:\n```\n{validate_result.stderr}\n```")
            )
    else:
        logger.info(f"No terraform directory found at {terraform_path}, skipping validate")

    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)

    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        from ipe.ipe_modules.ipe_workflow_ops import classify_issue
        issue_command, error = classify_issue(issue, ipe_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/ipe_feature"
            logger.warning("Defaulting to /ipe_feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("ipe_build_iso")

    # Create commit message
    logger.info("Creating implementation commit")
    commit_msg, error = create_commit(AGENT_BUILDER, issue, issue_command, ipe_id, logger, worktree_path)

    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_BUILDER, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)

    # Commit the implementation (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)

    if not success:
        logger.error(f"Error committing implementation: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_BUILDER, f"❌ Error committing implementation: {error}")
        )
        sys.exit(1)

    logger.info(f"Committed implementation: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(ipe_id, AGENT_BUILDER, "✅ Implementation committed")
    )

    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)

    logger.info("Isolated implementation phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(ipe_id, "ops", "✅ Isolated implementation phase completed")
    )

    # Save final state
    state.save("ipe_build_iso")

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{ipe_id}_ops: 📋 Final build state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )


if __name__ == "__main__":
    main()
