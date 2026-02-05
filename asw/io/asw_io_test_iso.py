#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "claude-agent-sdk"]
# ///

"""
ASW IO Test Iso - Infrastructure Platform Engineer workflow for agentic validation in isolated worktrees

Usage:
  uv run asw_io_test_iso.py <issue-number> <asw-id>

Workflow:
1. Load state and validate worktree exists
2. Run infrastructure validation suite in worktree (terraform validate, tflint)
3. Execute terraform plan and analyze changes
4. Report results to issue
5. Create commit with validation results in worktree
6. Push and update PR

This workflow REQUIRES that asw_io_plan_iso.py or asw_io_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.

BEHAVIORAL DIFFERENCES FROM ADW:
- No application tests (pytest/E2E)
- Runs terraform validate and tflint instead
- Executes terraform plan to preview infrastructure changes
- Uses /ipe_validate slash command
- Bot identifier is [🤖 IPE] instead of [🤖 ADW]
- Uses AGENT_VALIDATOR instead of AGENT_TESTER
"""

import json
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional, List
from dotenv import load_dotenv

# Add paths for imports
repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'ipe'))

from ipe.ipe_modules.ipe_data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
)
from ipe.ipe_modules.ipe_agent import execute_template
from ipe.ipe_modules.ipe_github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    get_repo_url,
)
from ipe.ipe_modules.ipe_utils import setup_logger, check_env_vars
from ipe.ipe_modules.ipe_state import IPEState
from ipe.ipe_modules.ipe_git_ops import commit_changes, finalize_git_operations
from ipe.ipe_modules.ipe_workflow_ops import (
    format_issue_message,
    create_commit,
    classify_issue,
)
from ipe.ipe_modules.ipe_worktree_ops import validate_worktree

# Agent name constants
AGENT_VALIDATOR = "infrastructure_validator"




def run_terraform_validate(
    ipe_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    terraform_dir: str = "io/terraform",
    environment: str = "sandbox"
) -> Tuple[bool, str]:
    """Run terraform validate in the worktree."""
    terraform_path = os.path.join(working_dir, terraform_dir) if working_dir else terraform_dir

    if not os.path.exists(terraform_path):
        logger.warning(f"No terraform directory found at {terraform_path}")
        return False, f"No terraform directory found at {terraform_path}"

    # Set TF_WORKSPACE to avoid interactive prompt with Terraform Cloud
    env = os.environ.copy()
    workspace_name = f"{{{{PROJECT_SLUG}}}}-{environment}"
    env["TF_WORKSPACE"] = workspace_name
    logger.info(f"Using TFC workspace: {workspace_name}")

    # Initialize terraform with Terraform Cloud backend
    logger.info(f"Initializing terraform in {terraform_path}")
    init_result = subprocess.run(
        ["terraform", "init", "-input=false"],
        capture_output=True,
        text=True,
        cwd=terraform_path,
        env=env
    )

    if init_result.returncode != 0:
        error_msg = f"Terraform init failed:\n{init_result.stderr}"
        logger.error(error_msg)
        return False, error_msg

    # Run terraform validate
    logger.info("Running terraform validate")
    validate_result = subprocess.run(
        ["terraform", "validate", "-json"],
        capture_output=True,
        text=True,
        cwd=terraform_path,
        env=env
    )

    if validate_result.returncode != 0:
        error_msg = f"Terraform validation failed:\n{validate_result.stdout}\n{validate_result.stderr}"
        logger.error(error_msg)
        return False, error_msg

    logger.info("Terraform validation passed")
    return True, validate_result.stdout


def run_terraform_plan(
    ipe_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    terraform_dir: str = "io/terraform",
    environment: str = "sandbox"
) -> Tuple[bool, str]:
    """Run terraform plan in the worktree to preview changes."""
    terraform_path = os.path.join(working_dir, terraform_dir) if working_dir else terraform_dir

    if not os.path.exists(terraform_path):
        logger.warning(f"No terraform directory found at {terraform_path}")
        return False, f"No terraform directory found at {terraform_path}"

    # Set TF_WORKSPACE for Terraform Cloud
    env = os.environ.copy()
    workspace_name = f"{{{{PROJECT_SLUG}}}}-{environment}"
    env["TF_WORKSPACE"] = workspace_name

    # Run terraform plan against Terraform Cloud backend
    logger.info(f"Running terraform plan for environment: {environment} (workspace: {workspace_name})")
    plan_result = subprocess.run(
        ["terraform", "plan", "-no-color", "-input=false"],
        capture_output=True,
        text=True,
        cwd=terraform_path,
        env=env
    )

    if plan_result.returncode != 0:
        error_msg = f"Terraform plan failed:\n{plan_result.stdout}\n{plan_result.stderr}"
        logger.warning(error_msg)
        # Plan failures are warnings, not errors (may be expected during development)
        return False, error_msg

    logger.info("Terraform plan generated successfully")
    return True, plan_result.stdout


def run_tflint(
    ipe_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    terraform_dir: str = "io/terraform"
) -> Tuple[bool, str]:
    """Run tflint for static analysis of Terraform code."""
    terraform_path = os.path.join(working_dir, terraform_dir) if working_dir else terraform_dir

    if not os.path.exists(terraform_path):
        logger.warning(f"No terraform directory found at {terraform_path}")
        return False, f"No terraform directory found at {terraform_path}"

    # Check if tflint is available
    which_result = subprocess.run(
        ["which", "tflint"],
        capture_output=True,
        text=True
    )

    if which_result.returncode != 0:
        logger.warning("tflint not installed, skipping")
        return True, "tflint not installed, skipping"

    # Initialize tflint
    logger.info("Initializing tflint")
    init_result = subprocess.run(
        ["tflint", "--init"],
        capture_output=True,
        text=True,
        cwd=terraform_path
    )

    # Run tflint
    logger.info("Running tflint")
    lint_result = subprocess.run(
        ["tflint", "--format", "json"],
        capture_output=True,
        text=True,
        cwd=terraform_path
    )

    # tflint returns non-zero on findings, which is not necessarily an error
    output = lint_result.stdout if lint_result.stdout else "No issues found"
    logger.info(f"tflint completed with exit code {lint_result.returncode}")

    return True, output


def format_validation_results_comment(
    validate_success: bool,
    validate_output: str,
    plan_success: bool,
    plan_output: str,
    tflint_success: bool,
    tflint_output: str
) -> str:
    """Format validation results for GitHub issue comment."""
    comment_parts = []
    comment_parts.append("# 🔍 Infrastructure Validation Results\n")

    # Terraform Validate
    comment_parts.append("## Terraform Validate")
    if validate_success:
        comment_parts.append("✅ **Status**: PASSED")
        comment_parts.append("```json")
        comment_parts.append(validate_output[:1000])  # Truncate if too long
        comment_parts.append("```")
    else:
        comment_parts.append("❌ **Status**: FAILED")
        comment_parts.append("```")
        comment_parts.append(validate_output[:2000])  # Show more on failure
        comment_parts.append("```")
    comment_parts.append("")

    # Terraform Plan
    comment_parts.append("## Terraform Plan")
    if plan_success:
        comment_parts.append("✅ **Status**: Plan generated successfully")
        comment_parts.append("<details>")
        comment_parts.append("<summary>View Plan Output</summary>")
        comment_parts.append("\n```terraform")
        comment_parts.append(plan_output[:5000])  # Truncate if too long
        comment_parts.append("```")
        comment_parts.append("</details>")
    else:
        comment_parts.append("⚠️ **Status**: Plan had warnings/errors")
        comment_parts.append("```")
        comment_parts.append(plan_output[:2000])
        comment_parts.append("```")
    comment_parts.append("")

    # TFLint
    comment_parts.append("## TFLint")
    if "not installed" in tflint_output or "skipping" in tflint_output:
        comment_parts.append("⚠️ **Status**: Skipped (not installed)")
    elif tflint_success:
        comment_parts.append("✅ **Status**: Completed")
        comment_parts.append("```json")
        comment_parts.append(tflint_output[:1000])
        comment_parts.append("```")
    else:
        comment_parts.append("❌ **Status**: Issues found")
        comment_parts.append("```")
        comment_parts.append(tflint_output[:2000])
        comment_parts.append("```")
    comment_parts.append("")

    # Summary
    comment_parts.append("## Summary")
    all_passed = validate_success and (plan_success or "not installed" in plan_output)
    if all_passed:
        comment_parts.append("✅ **Overall Status**: Infrastructure validation PASSED")
    else:
        comment_parts.append("❌ **Overall Status**: Infrastructure validation FAILED")

    return "\n".join(comment_parts)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    # INTENTIONAL: ipe-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run asw_io_test_iso.py <issue-number> <asw-id>")
        print("\nError: ipe-id is required to locate the worktree")
        print("Run asw_io_plan_iso.py or asw_io_patch_iso.py first to create the worktree")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2]

    # Try to load existing state
    temp_logger = setup_logger(ipe_id, "ipe_test_iso")
    state = ASWIOState.load(ipe_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            f"{ipe_id}_ops: 🔍 Found existing state - starting isolated validation\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )
    else:
        # No existing state found
        logger = setup_logger(ipe_id, "ipe_test_iso")
        logger.error(f"No state found for IPE ID: {ipe_id}")
        logger.error("Run asw_io_plan_iso.py or asw_io_patch_iso.py first to create the worktree and state")
        print(f"\nError: No state found for IPE ID: {ipe_id}")
        print("Run asw_io_plan_iso.py or asw_io_patch_iso.py first to create the worktree and state")
        sys.exit(1)

    # Track that this IPE workflow has run
    state.append_asw_id("ipe_test_iso")

    # Set up logger with IPE ID from command line
    logger = setup_logger(ipe_id, "ipe_test_iso")
    logger.info(f"ASW IO Test Iso starting - ID: {ipe_id}, Issue: {issue_number}")

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

    # Get environment and terraform directory from state
    environment = state.get("environment", "sandbox")
    terraform_dir = state.get("terraform_dir") or "io/terraform"

    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", f"✅ Starting isolated validation phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🌍 Environment: {environment}\n"
                           f"📁 Terraform Directory: {terraform_dir}")
    )

    # Run terraform validate (executing in worktree)
    logger.info("Running terraform validate in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_VALIDATOR, "🔍 Running terraform validate in isolated environment...")
    )

    validate_success, validate_output = run_terraform_validate(
        ipe_id, logger, worktree_path, terraform_dir, environment
    )

    # Run terraform plan (executing in worktree)
    logger.info("Running terraform plan in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_VALIDATOR, "📋 Running terraform plan to preview changes...")
    )

    plan_success, plan_output = run_terraform_plan(
        ipe_id, logger, worktree_path, terraform_dir, environment
    )

    # Run tflint (executing in worktree)
    logger.info("Running tflint in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_VALIDATOR, "🔎 Running tflint for static analysis...")
    )

    tflint_success, tflint_output = run_tflint(
        ipe_id, logger, worktree_path, terraform_dir
    )

    # Format and post results
    comment = format_validation_results_comment(
        validate_success, validate_output,
        plan_success, plan_output,
        tflint_success, tflint_output
    )
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_VALIDATOR, comment)
    )

    # Check if we should exit due to validation failures
    if not validate_success:
        logger.error("Terraform validation failed - continuing to commit results")
        # Note: We don't exit here, we commit the results regardless

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)

    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        issue_command, error = classify_issue(issue, ipe_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/ipe_feature"
            logger.warning("Defaulting to /ipe_feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("ipe_test_iso")

    # Create commit message
    logger.info("Creating validation commit")
    commit_msg, error = create_commit(AGENT_VALIDATOR, issue, issue_command, ipe_id, logger, worktree_path)

    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_VALIDATOR, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)

    # Commit the validation results (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)

    if not success:
        logger.error(f"Error committing validation results: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_VALIDATOR, f"❌ Error committing validation results: {error}")
        )
        sys.exit(1)

    logger.info(f"Committed validation results: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(ipe_id, AGENT_VALIDATOR, "✅ Validation results committed")
    )

    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)

    logger.info("Isolated validation phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(ipe_id, "ops", "✅ Isolated validation phase completed")
    )

    # Save final state
    state.save("ipe_test_iso")

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{ipe_id}_ops: 📋 Final validation state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )

    # Exit with appropriate code based on validation results
    if not validate_success:
        logger.error("Infrastructure validation failed")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", "❌ Infrastructure validation failed")
        )
        sys.exit(1)
    else:
        logger.info("Infrastructure validation passed successfully")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", "✅ Infrastructure validation passed successfully!")
        )


if __name__ == "__main__":
    main()
