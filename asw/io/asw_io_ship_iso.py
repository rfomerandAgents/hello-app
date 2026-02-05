#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ASW IO Ship Iso - Infrastructure Platform Engineer for shipping (merging) to main

Usage:
  uv run asw_io_ship_iso.py <issue-number> <adw-id> [--skip-ci-check] [--create-ami]

Requirements:
  1. Clean working directory on main branch (or auto-stash enabled)
  2. No merge conflicts between feature branch and main
  3. All CI checks passing (unless --skip-ci-check)
  4. Complete IPE state with all required fields populated

Workflow:
1. Load state and validate worktree exists
2. Validate ALL state fields are populated (not None)
3. Run pre-merge validation:
   - Check main branch working directory (auto-stash if needed)
   - Detect merge conflicts
   - Verify CI status (optional)
4. Perform manual git merge in main repository:
   - Fetch latest from origin
   - Checkout main
   - Merge feature branch (--no-ff to preserve commits)
   - Push to origin/main
5. Update state with ship metadata
6. (Optional) Build AMI if --create-ami flag is provided:
   - Generate IPE ID from IPE ID
   - Determine environment from branch name
   - Create IPE state for AMI build
   - Invoke ipe_build_ami_iso.py to build Packer AMI
   - Retrieve and report AMI build results
7. Post success message to issue

This workflow REQUIRES that all previous workflows have been run and that
every field in IPEState has a value. This is our final approval step.

Note: Merge operations happen in the main repository root, not in the worktree,
to preserve the worktree's state. Uncommitted changes are automatically stashed
and restored.

AMI Build: The --create-ami flag triggers an optional AMI build after merge.
AMI build failures do NOT fail the ship workflow - shipping to main takes priority.

See: SHIP_WORKFLOW_REQUIREMENTS.md for detailed requirements and troubleshooting.
"""

import sys
import os
import logging
import json
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

from asw.modules.state import ASWIOState
from asw.modules.github import (
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from asw.modules.workflow_ops import format_issue_message
from asw.modules.utils import setup_logger, check_env_vars
from asw.modules.worktree_ops import validate_worktree
from asw.modules.data_types import IPEStateData

# Agent name constant
AGENT_SHIPPER = "shipper"


def get_main_repo_root() -> str:
    """Get the main repository root directory (parent of adws)."""
    # This script is in ipe/, so go up one level to get repo root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_ipe_id_from_adw(ipe_id: str) -> str:
    """Generate IPE ID from IPE ID for AMI builds.

    Uses 'ami-' prefix + first 5 chars of ipe_id.
    Example: abc123de -> ami-abc12

    Args:
        ipe_id: The IPE ID (e.g., "IPE-abc123de" or "abc123de")

    Returns:
        IPE ID for AMI build (e.g., "ami-abc12")
    """
    base_id = ipe_id.replace("IPE-", "").replace("adw-", "")
    ipe_id = f"ami-{base_id[:5]}"
    return ipe_id


def determine_environment_from_branch(branch_name: str) -> str:
    """Determine deployment environment from branch name.

    Args:
        branch_name: Git branch name

    Returns:
        Environment string: "prod", "staging", or "dev"
    """
    branch_lower = branch_name.lower()

    if branch_lower in ["main", "master", "production", "prod"]:
        return "prod"
    if "staging" in branch_lower or "release" in branch_lower:
        return "staging"
    return "dev"


def create_ipe_state_for_ami_build(
    ipe_state: IPEState,
    ipe_id: str,
    environment: str,
    logger: logging.Logger
) -> bool:
    """Create IPE state from IPE state for AMI building.

    Args:
        ipe_state: IPE state object
        ipe_id: IPE ID to create
        environment: Deployment environment (dev/staging/prod)
        logger: Logger instance

    Returns:
        True if state created successfully, False otherwise
    """
    import sys
    import os

    repo_root = get_main_repo_root()
    ipe_path = os.path.join(repo_root, 'ipe')
    sys.path.insert(0, ipe_path)

    try:
        from ipe.ipe_modules.ipe_state import IPEState

        ipe_state = ASWIOState(ipe_id)
        ipe_state.update(
            issue_number=ipe_state.get("issue_number"),
            branch_name=ipe_state.get("branch_name"),
            worktree_path=ipe_state.get("worktree_path"),
            environment=environment,
            issue_class="/ipe_feature",
            spec_file=ipe_state.get("spec_file"),
            model_set=ipe_state.get("model_set", "base"),
        )

        ipe_state.save("ipe_ship_iso_ami_integration")
        logger.info(f"Created IPE state for AMI build: {ipe_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to create IPE state: {e}")
        return False


def invoke_ami_build(
    issue_number: str,
    ipe_id: str,
    logger: logging.Logger
) -> tuple[bool, Optional[str]]:
    """Invoke ipe_build_ami_iso.py to build AMI.

    Args:
        issue_number: GitHub issue number
        ipe_id: IPE ID for AMI build
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    import subprocess
    import os

    repo_root = get_main_repo_root()
    ipe_script = os.path.join(repo_root, "ipe", "ipe_build_ami_iso.py")

    cmd = ["uv", "run", ipe_script, issue_number, ipe_id]
    logger.info(f"Invoking AMI build: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=repo_root
        )

        if result.returncode != 0:
            error_msg = f"AMI build failed with exit code {result.returncode}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

        logger.info("AMI build completed successfully")
        return True, None

    except Exception as e:
        error_msg = f"Failed to invoke AMI build: {e}"
        logger.error(error_msg)
        return False, error_msg


def get_ami_build_result(ipe_id: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Retrieve AMI build results from IPE artifact file.

    Args:
        ipe_id: IPE ID for AMI build
        logger: Logger instance

    Returns:
        Dictionary with AMI build results or None if not found
    """
    import json
    import os

    repo_root = get_main_repo_root()
    result_path = os.path.join(repo_root, "agents", ipe_id, "ami_build_result.json")

    if not os.path.exists(result_path):
        logger.warning(f"AMI result file not found: {result_path}")
        return None

    try:
        with open(result_path, 'r') as f:
            result = json.load(f)
        logger.info(f"Retrieved AMI build result: {result.get('ami_id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to read AMI result: {e}")
        return None


def manual_merge_to_main(branch_name: str, logger: logging.Logger) -> Tuple[bool, Optional[str], Optional[str]]:
    """Manually merge a branch to main using git commands.

    This runs in the main repository root, not in a worktree.
    Automatically stashes uncommitted changes if present.

    Args:
        branch_name: The feature branch to merge
        logger: Logger instance

    Returns:
        Tuple of (success, error_message, merge_commit_sha)
    """
    from asw.modules.git_ops import check_working_directory_clean, stash_changes, unstash_changes

    repo_root = get_main_repo_root()
    logger.info(f"Performing manual merge in main repository: {repo_root}")

    stash_id = None
    original_branch = None

    try:
        # Check for uncommitted changes and stash if needed
        is_clean, _, changed_files = check_working_directory_clean(cwd=repo_root)
        if not is_clean:
            logger.warning(f"Working directory has uncommitted changes: {changed_files}")
            logger.info("Stashing changes before merge...")

            success, error, stash_id = stash_changes(
                message=f"ASW IO Ship: Auto-stash before merging {branch_name}",
                cwd=repo_root,
                logger=logger
            )

            if not success:
                return False, f"Failed to stash uncommitted changes: {error}", None

            logger.info(f"Changes stashed as {stash_id}")

        # Save current branch to restore later
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=repo_root
        )
        original_branch = result.stdout.strip()
        logger.debug(f"Original branch: {original_branch}")

        # Step 1: Fetch latest from origin
        logger.info("Fetching latest from origin...")
        result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            _cleanup_on_failure(repo_root, original_branch, stash_id, logger)
            return False, f"Failed to fetch from origin: {result.stderr}", None

        # Step 2: Checkout main
        logger.info("Checking out main branch...")
        result = subprocess.run(
            ["git", "checkout", "main"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            _cleanup_on_failure(repo_root, original_branch, stash_id, logger)
            return False, f"Failed to checkout main: {result.stderr}", None

        # Step 3: Pull latest main
        logger.info("Pulling latest main...")
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            _cleanup_on_failure(repo_root, original_branch, stash_id, logger)
            return False, f"Failed to pull latest main: {result.stderr}", None

        # Step 4: Merge the feature branch (no-ff to preserve all commits)
        logger.info(f"Merging branch {branch_name} (no-ff to preserve all commits)...")
        result = subprocess.run(
            ["git", "merge", branch_name, "--no-ff", "-m", f"Merge branch '{branch_name}' via ASW IO Ship workflow"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            # Check if merge is in progress and abort it
            merge_head_path = os.path.join(repo_root, ".git", "MERGE_HEAD")
            if os.path.exists(merge_head_path):
                logger.info("Aborting incomplete merge...")
                abort_result = subprocess.run(
                    ["git", "merge", "--abort"],
                    capture_output=True, text=True, cwd=repo_root
                )
                if abort_result.returncode == 0:
                    logger.info("Merge aborted successfully")
                else:
                    logger.error(f"Failed to abort merge: {abort_result.stderr}")

            _cleanup_on_failure(repo_root, original_branch, stash_id, logger)
            return False, f"Failed to merge {branch_name}: {result.stderr}", None

        # Get the merge commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=repo_root
        )
        merge_commit_sha = result.stdout.strip() if result.returncode == 0 else None

        # Step 5: Push to origin/main
        logger.info("Pushing to origin/main...")
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            _cleanup_on_failure(repo_root, original_branch, stash_id, logger)
            return False, f"Failed to push to origin/main: {result.stderr}", None

        # Step 6: Restore original branch
        logger.info(f"Restoring original branch: {original_branch}")
        subprocess.run(["git", "checkout", original_branch], cwd=repo_root)

        # Unstash if we stashed earlier
        if stash_id:
            logger.info("Restoring stashed changes...")
            success, error = unstash_changes(stash_id=stash_id, cwd=repo_root, logger=logger)
            if not success:
                logger.warning(f"Failed to restore stashed changes: {error}")
                logger.warning(f"Changes are saved in {stash_id}")

        logger.info("Successfully merged and pushed to main!")
        return True, None, merge_commit_sha

    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        _cleanup_on_failure(repo_root, original_branch, stash_id, logger)
        return False, str(e), None


def _cleanup_on_failure(repo_root: str, original_branch: Optional[str], stash_id: Optional[str], logger: logging.Logger) -> None:
    """Clean up after a failed merge operation.

    Args:
        repo_root: Path to repository root
        original_branch: Branch to restore
        stash_id: Stash ID to restore, if any
        logger: Logger instance
    """
    from asw.modules.git_ops import unstash_changes

    try:
        # Check if merge is in progress and abort
        merge_head_path = os.path.join(repo_root, ".git", "MERGE_HEAD")
        if os.path.exists(merge_head_path):
            logger.info("Aborting incomplete merge during cleanup...")
            subprocess.run(["git", "merge", "--abort"], cwd=repo_root)

        # Restore original branch
        if original_branch:
            subprocess.run(["git", "checkout", original_branch], cwd=repo_root)

        # Restore stash
        if stash_id:
            logger.info("Restoring stashed changes after failure...")
            unstash_changes(stash_id=stash_id, cwd=repo_root, logger=logger)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def validate_state_completeness(state: IPEState, logger: logging.Logger) -> tuple[bool, list[str]]:
    """Validate that all fields in IPEState have values (not None).
    
    Returns:
        tuple of (is_valid, missing_fields)
    """
    # Get the expected fields from IPEStateData model
    expected_fields = {
        "ipe_id",
        "issue_number",
        "branch_name",
        "spec_file",
        "issue_class",
        "worktree_path",
    }
    
    missing_fields = []
    
    for field in expected_fields:
        value = state.get(field)
        if value is None:
            missing_fields.append(field)
            logger.warning(f"Missing required field: {field}")
        else:
            logger.debug(f"✓ {field}: {value}")
    
    return len(missing_fields) == 0, missing_fields


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree and state
    if len(sys.argv) < 3:
        print("Usage: uv run asw_io_ship_iso.py <issue-number> <adw-id> [--skip-ci-check] [--create-ami]")
        print("\nError: Both issue-number and adw-id are required")
        print("\nOptions:")
        print("  --skip-ci-check  Skip CI/CD status validation")
        print("  --create-ami     Build AMI using latest codebase after merge")
        print("\nRun the complete SDLC workflow before shipping")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2]

    # Check for optional flags
    skip_ci_check = "--skip-ci-check" in sys.argv
    create_ami = "--create-ami" in sys.argv

    # Try to load existing state
    temp_logger = setup_logger(ipe_id, "ipe_ship_iso")
    state = ASWIOState.load(ipe_id, temp_logger)
    if not state:
        # No existing state found
        logger = setup_logger(ipe_id, "ipe_ship_iso")
        logger.error(f"No state found for IPE ID: {ipe_id}")
        logger.error("Run the complete SDLC workflow before shipping")
        print(f"\nError: No state found for IPE ID: {ipe_id}")
        print("Run the complete SDLC workflow before shipping")
        sys.exit(1)

    # Update issue number from state if available
    issue_number = state.get("issue_number", issue_number)

    # Set up logger with IPE ID
    logger = setup_logger(ipe_id, "ipe_ship_iso")
    logger.info(f"ASW IO Ship Iso starting - ID: {ipe_id}, Issue: {issue_number}")
    if skip_ci_check:
        logger.info("CI check skipped via --skip-ci-check flag")

    # Validate environment
    check_env_vars(logger)
    
    # Post initial status
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, "ops", f"🚢 Starting ship workflow\n"
                           f"📋 Validating state completeness...")
    )
    
    # Step 1: Validate state completeness
    logger.info("Validating state completeness...")
    is_valid, missing_fields = validate_state_completeness(state, logger)
    
    if not is_valid:
        error_msg = f"State validation failed. Missing fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_SHIPPER, f"❌ {error_msg}\n\n"
                               "Please ensure all workflows have been run:\n"
                               "- asw_io_plan_iso.py (creates spec_file, branch_name, issue_class)\n"
                               "- asw_io_build_iso.py (implements the plan)\n" 
                               "- asw_io_test_iso.py (runs tests)\n"
                               "- asw_io_review_iso.py (reviews implementation)\n"
                               "- asw_io_document_iso.py (generates docs)")
        )
        sys.exit(1)
    
    logger.info("✅ State validation passed - all fields have values")
    
    # Step 2: Validate worktree exists
    valid, error = validate_worktree(ipe_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_SHIPPER, f"❌ Worktree validation failed: {error}")
        )
        sys.exit(1)
    
    worktree_path = state.get("worktree_path")
    logger.info(f"✅ Worktree validated at: {worktree_path}")
    
    # Step 3: Get branch name
    branch_name = state.get("branch_name")
    logger.info(f"Preparing to merge branch: {branch_name}")

    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_SHIPPER, f"📋 State validation complete\n"
                           f"🔍 Preparing to merge branch: {branch_name}")
    )

    # Step 3.5: Pre-merge validation
    from asw.modules.git_ops import validate_pre_merge

    logger.info("Running pre-merge validation...")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_SHIPPER,
            "Running pre-merge validation:\n"
            "- Checking working directory status\n"
            "- Detecting merge conflicts\n"
            f"- Validating CI checks: {'skipped' if skip_ci_check else 'enabled'}")
    )

    is_valid, errors, details = validate_pre_merge(
        branch_name=branch_name,
        target_branch="main",
        check_ci=not skip_ci_check,
        cwd=get_main_repo_root(),
        logger=logger
    )

    if not is_valid:
        error_msg = "Pre-merge validation failed:\n" + "\n".join(f"- {err}" for err in errors)
        logger.error(error_msg)

        # Enhanced error message with troubleshooting
        troubleshooting = (
            "\n\n**Troubleshooting:**\n"
            "- Working directory not clean: Commit or stash changes manually, or let auto-stash handle it\n"
            "- Merge conflicts: Merge main into feature branch and resolve conflicts\n"
            "- CI checks failing: Fix failing tests and push updates\n"
            "\nSee: SHIP_WORKFLOW_REQUIREMENTS.md for details"
        )

        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_SHIPPER,
                f"{error_msg}{troubleshooting}\n\n"
                f"**Validation Details:**\n"
                f"```json\n{json.dumps(details, indent=2)}\n```")
        )
        sys.exit(1)

    logger.info("Pre-merge validation passed")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_SHIPPER,
            "Pre-merge validation passed\n"
            "- Working directory is clean (or will be stashed)\n"
            "- No merge conflicts detected\n"
            f"- CI checks: {'skipped' if skip_ci_check else 'all passing'}")
    )

    # Step 4: Perform manual merge
    logger.info(f"Starting manual merge of {branch_name} to main...")
    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_SHIPPER, f"Merging {branch_name} to main...\n"
                           "Using manual git operations in main repository")
    )

    success, error, merge_commit = manual_merge_to_main(branch_name, logger)

    if not success:
        logger.error(f"Failed to merge: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_SHIPPER, f"Failed to merge: {error}\n\n"
                               "**Note:** If uncommitted changes were stashed, they have been restored.\n"
                               "Check `git stash list` if changes are missing.")
        )
        sys.exit(1)

    logger.info(f"Successfully merged {branch_name} to main")

    # Step 5: Update state with ship metadata
    from asw.modules.git_ops import get_pr_number
    pr_number = get_pr_number(branch_name)

    state.update(
        deployed_at=datetime.now().isoformat(),
        merge_commit=merge_commit,
        pr_number=pr_number
    )

    # Track that ship workflow completed successfully
    state.append_asw_id("ipe_ship_iso")

    # Save final state
    state.save("ipe_ship_iso")

    # Step 5.5: Optional AMI Build
    ami_id = None
    ami_name = None

    if create_ami:
        logger.info("--create-ami flag detected, building AMI...")

        environment = determine_environment_from_branch(branch_name)
        logger.info(f"Determined environment: {environment}")

        make_issue_comment(
            issue_number,
            format_issue_message(ipe_id, AGENT_SHIPPER,
                f"Building AMI for latest codebase\n"
                f"- Branch: {branch_name}\n"
                f"- Environment: {environment}")
        )

        ipe_id = generate_ipe_id_from_adw(ipe_id)
        logger.info(f"Generated IPE ID: {ipe_id}")

        if not create_ipe_state_for_ami_build(state, ipe_id, environment, logger):
            error_msg = "Failed to create IPE state for AMI build"
            logger.error(error_msg)
            make_issue_comment(
                issue_number,
                format_issue_message(ipe_id, AGENT_SHIPPER,
                    f"AMI build preparation failed: {error_msg}\n"
                    f"Ship workflow succeeded, but AMI build skipped.")
            )
        else:
            success, error = invoke_ami_build(issue_number, ipe_id, logger)

            if not success:
                logger.error(f"AMI build failed: {error}")
                make_issue_comment(
                    issue_number,
                    format_issue_message(ipe_id, AGENT_SHIPPER,
                        f"AMI build failed: {error}\n"
                        f"Ship workflow succeeded, but AMI build failed.")
                )
            else:
                ami_result = get_ami_build_result(ipe_id, logger)
                if ami_result:
                    ami_id = ami_result.get("ami_id")
                    ami_name = ami_result.get("ami_name")

                    logger.info(f"AMI build successful: {ami_id}")
                    make_issue_comment(
                        issue_number,
                        format_issue_message(ipe_id, AGENT_SHIPPER,
                            f"AMI build completed successfully!\n"
                            f"- AMI ID: {ami_id}\n"
                            f"- AMI Name: {ami_name}\n"
                            f"- Environment: {environment}")
                    )

    # Step 6: Post success message
    success_message = (
        f"**Successfully shipped!**\n\n"
        f"Validated all state fields\n"
        f"Merged branch `{branch_name}` to main\n"
        f"Pushed to origin/main\n"
        f"Merge commit: `{merge_commit[:8] if merge_commit else 'N/A'}`"
    )

    if create_ami and ami_id:
        success_message += (
            f"\n\n**AMI Build:**\n"
            f"AMI ID: {ami_id}\n"
            f"AMI Name: {ami_name}\n"
            f"Ready for deployment!"
        )
    elif create_ami:
        success_message += (
            f"\n\n**AMI Build:**\n"
            f"AMI build was attempted but details are unavailable.\n"
            f"Check logs for more information."
        )

    success_message += f"\n\nCode has been deployed to production!"

    make_issue_comment(
        issue_number,
        format_issue_message(ipe_id, AGENT_SHIPPER, success_message)
    )

    # Post final state summary
    make_issue_comment(
        issue_number,
        f"{ipe_id}_ops: Final ship state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )

    logger.info("Ship workflow completed successfully")


if __name__ == "__main__":
    main()