#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ASW IO Plan Iso - Infrastructure Platform Engineer workflow for agentic planning in isolated worktrees

Usage:
  uv run asw_io_plan_iso.py <issue-number> [asw-id] [environment]

Workflow:
1. Fetch GitHub issue details
2. Check/create worktree for isolated execution
3. Setup worktree environment (NO port allocation - IPE difference from ADW)
4. Classify issue type (/ipe_chore, /ipe_bug, /ipe_feature)
5. Create feature branch in worktree
6. Generate infrastructure implementation plan in worktree
7. Commit plan in worktree
8. Push and create/update PR

This workflow creates an isolated git worktree under trees/<asw_id>/ for
parallel execution without interference.

BEHAVIORAL DIFFERENCES FROM ADW:
- No port allocation (IPE vs Application)
- Uses spec_file instead of plan_file
- Sets environment field (dev/staging/prod) for ipe_build_ami_iso.py
- Uses /ipe_chore, /ipe_bug, /ipe_feature slash commands
- Manages infrastructure (Terraform/Packer) not application code

RELATIONSHIP TO ipe_build_ami_iso.py:
This script is a PREREQUISITE - it creates the worktree and state that
ipe_build_ami_iso.py requires. The state contract includes:
- branch_name: Git branch in worktree
- environment: Target environment (dev/staging/prod)
- worktree_path: Path to isolated worktree
- issue_number: GitHub issue number
"""

import sys
import os
import logging
import json
import re
from typing import Optional
from dotenv import load_dotenv

# Add paths for imports
repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'ipe'))

from ipe.ipe_modules.ipe_state import IPEState
from ipe.ipe_modules.ipe_git_ops import commit_changes, finalize_git_operations
from ipe.ipe_modules.ipe_github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from ipe.ipe_modules.ipe_workflow_ops import (
    classify_issue,
    build_plan,
    generate_branch_name,
    create_commit,
    format_issue_message,
    ensure_asw_io_id,
    extract_ipe_info,
    AGENT_PLANNER,
)
from ipe.ipe_modules.ipe_utils import setup_logger, check_env_vars
from ipe.ipe_modules.ipe_data_types import GitHubIssue, IssueClassSlashCommand, AgentTemplateRequest
from ipe.ipe_modules.ipe_agent import execute_template
from ipe.ipe_modules.ipe_worktree_ops import (
    create_worktree,
    validate_worktree,
)


# Minimum expected execution time for planning (10 seconds)
MIN_PLANNING_DURATION_MS = 10_000

# Expected output pattern for plan file paths
PLAN_FILE_PATTERN = re.compile(r'^specs/.*\.md$')


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 2:
        print("Usage: uv run asw_io_plan_iso.py <issue-number> [asw-id] [environment]")
        print("\nArguments:")
        print("  issue-number: GitHub issue number (required)")
        print("  ipe-id: IPE workflow ID (optional, will be generated if not provided)")
        print("  environment: Target environment - dev/staging/prod/sandbox (optional, defaults to 'sandbox')")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2] if len(sys.argv) > 2 else None
    environment = sys.argv[3] if len(sys.argv) > 3 else "sandbox"

    # Validate environment
    valid_environments = ["dev", "staging", "prod", "sandbox"]
    if environment not in valid_environments:
        print(f"Error: Invalid environment '{environment}'")
        print(f"Must be one of: {', '.join(valid_environments)}")
        sys.exit(1)

    # Ensure IPE ID exists with initialized state
    temp_logger = setup_logger(ipe_id, "ipe_plan_iso") if ipe_id else None
    ipe_id = ensure_asw_io_id(issue_number, ipe_id, temp_logger)

    # Load the state that was created/found by ensure_ipe_id
    state = ASWIOState.load(ipe_id, temp_logger)

    # Ensure state has the ipe_id field
    if not state.get("ipe_id"):
        state.update(ipe_id=ipe_id)

    # Set environment field (CRITICAL: required by ipe_build_ami_iso.py)
    state.update(environment=environment)

    # Track that this IPE workflow has run
    state.append_asw_id("ipe_plan_iso")

    # Set up logger with IPE ID
    logger = setup_logger(ipe_id, "ipe_plan_iso")
    logger.info(f"ASW IO Plan Iso starting - ID: {ipe_id}, Issue: {issue_number}, Environment: {environment}")

    # Validate environment
    check_env_vars(logger)

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Check if worktree already exists
    valid, error = validate_worktree(ipe_id, state)
    if valid:
        logger.info(f"Using existing worktree for {ipe_id}")
        worktree_path = state.get("worktree_path")
    else:
        worktree_path = None

    # Fetch issue details
    issue: GitHubIssue = fetch_issue(issue_number, repo_path)

    logger.debug(f"Fetched issue: {issue.model_dump_json(indent=2, by_alias=True)}")

    # Extract model_set from issue body (detects "heavy" keyword)
    extraction_result = extract_ipe_info(issue.body or "", ipe_id)
    detected_model_set = extraction_result.model_set or "base"
    state.update(model_set=detected_model_set)
    logger.info(f"Model set detected from issue: {detected_model_set}")

    make_issue_comment(
        issue_number, format_issue_message(ipe_id, "ops", f"✅ Starting isolated planning phase (model_set: {detected_model_set})")
    )

    make_issue_comment(
        issue_number,
        f"{ipe_id}_ops: 🔍 Using state\n```json\n{json.dumps(state.data, indent=2)}\n```",
    )

    # Classify the issue (check if already classified)
    if state.get("issue_class"):
        logger.info(f"Using existing classification: {state.get('issue_class')}")
        issue_command = state.get("issue_class")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"✅ Issue already classified as: {issue_command}"),
        )
    else:
        issue_command, error = classify_issue(issue, ipe_id, logger)

        if error:
            logger.error(f"Error classifying issue: {error}")
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, "ops", f"❌ Error classifying issue: {error}"),
            )
            sys.exit(1)

        state.update(issue_class=issue_command)
        state.save("ipe_plan_iso")
        logger.info(f"Issue classified as: {issue_command}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"✅ Issue classified as: {issue_command}"),
        )

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, ipe_id, logger)

    if error:
        logger.error(f"Error generating branch name: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                ipe_id, "ops", f"❌ Error generating branch name: {error}"
            ),
        )
        sys.exit(1)

    # Don't create branch here - let worktree create it
    # The worktree command will create the branch when we specify -b
    state.update(branch_name=branch_name, issue_number=issue_number)
    state.save("ipe_plan_iso")
    logger.info(f"Will create branch in worktree: {branch_name}")

    # Create worktree if it doesn't exist
    if not valid:
        logger.info(f"Creating worktree for {ipe_id}")
        worktree_path, error = create_worktree(ipe_id, branch_name, logger)

        if error:
            logger.error(f"Error creating worktree: {error}")
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, "ops", f"❌ Error creating worktree: {error}"),
            )
            sys.exit(1)

        state.update(worktree_path=worktree_path)
        state.save("ipe_plan_iso")
        logger.info(f"Created worktree at {worktree_path}")

        # Run install_worktree command to set up the isolated environment
        # NOTE: NO port arguments for IPE (key difference from ADW)
        logger.info("Setting up isolated environment")
        install_request = AgentTemplateRequest(
            agent_name="ops",
            slash_command="/install_worktree",
            args=[worktree_path],  # NO ports for IPE
            ipe_id=ipe_id,
            working_dir=worktree_path,  # Execute in worktree
        )

        install_response = execute_template(install_request)
        if not install_response.success:
            logger.error(f"Error setting up worktree: {install_response.output}")
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, "ops", f"❌ Error setting up worktree: {install_response.output}"),
            )
            sys.exit(1)

        logger.info("Worktree environment setup complete")

    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", f"✅ Working in isolated worktree: {worktree_path}\n"
                           f"🌍 Environment: {environment}"),
    )

    # Build the implementation plan (now executing in worktree)
    logger.info("Building implementation plan in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_PLANNER, "✅ Building implementation plan in isolated environment"),
    )

    plan_response = build_plan(issue, issue_command, ipe_id, logger, working_dir=worktree_path)

    if not plan_response.success:
        logger.error(f"Error building plan: {plan_response.output}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                ipe_id, AGENT_PLANNER, f"❌ Error building plan: {plan_response.output}"
            ),
        )
        sys.exit(1)

    logger.debug(f"Plan response: {plan_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_PLANNER, "✅ Implementation plan created"),
    )

    # Check for suspiciously fast execution (indicates likely failure)
    if plan_response.duration_ms and plan_response.duration_ms < MIN_PLANNING_DURATION_MS:
        error = (
            f"Planning completed too quickly ({plan_response.duration_ms}ms < {MIN_PLANNING_DURATION_MS}ms). "
            f"This usually indicates the slash command didn't execute properly."
        )
        logger.warning(error)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"⚠️ {error}"),
        )
        # Don't exit - just log warning, continue to validate output

    # Get the plan file path directly from response
    logger.info("Getting plan file path")
    plan_file_path = plan_response.output.strip()

    # Validate the path format matches expected pattern
    if plan_file_path and not PLAN_FILE_PATTERN.match(plan_file_path):
        error = (
            f"Plan file path has unexpected format: '{plan_file_path}'. "
            f"Expected pattern: 'specs/*.md'"
        )
        logger.error(error)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error}"),
        )
        sys.exit(1)

    # Validate the path exists (within worktree)
    if not plan_file_path:
        error = "No plan file path returned from planning agent"
        logger.error(error)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error}"),
        )
        sys.exit(1)

    # Check if file exists in worktree
    worktree_plan_path = os.path.join(worktree_path, plan_file_path)
    if not os.path.exists(worktree_plan_path):
        error = f"Plan file does not exist in worktree: {plan_file_path}"
        logger.error(error)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, "ops", f"❌ {error}"),
        )
        sys.exit(1)

    # IPE uses spec_file (not plan_file like ADW)
    state.update(spec_file=plan_file_path)
    state.save("ipe_plan_iso")
    logger.info(f"Plan file created: {plan_file_path}")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", f"✅ Plan file created: {plan_file_path}"),
    )

    # Create commit message
    logger.info("Creating plan commit")
    commit_msg, error = create_commit(
        AGENT_PLANNER, issue, issue_command, ipe_id, logger, worktree_path
    )

    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                ipe_id, AGENT_PLANNER, f"❌ Error creating commit message: {error}"
            ),
        )
        sys.exit(1)

    # Commit the plan (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)

    if not success:
        logger.error(f"Error committing plan: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                ipe_id, AGENT_PLANNER, f"❌ Error committing plan: {error}"
            ),
        )
        sys.exit(1)

    logger.info(f"Committed plan: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(ipe_id, AGENT_PLANNER, "✅ Plan committed")
    )

    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)

    logger.info("Isolated planning phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(ipe_id, "ops", "✅ Isolated planning phase completed")
    )

    # Save final state
    state.save("ipe_plan_iso")

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{ipe_id}_ops: 📋 Final planning state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )

    logger.info(f"ASW IO Plan Iso completed - ID: {ipe_id}")


if __name__ == "__main__":
    main()
