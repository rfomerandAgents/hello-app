#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# requires-python = ">=3.10"
# ///

"""
ASW IO Destroy - GitHub Actions Infrastructure Destruction Wrapper

Triggers the destroy-infrastructure.yml workflow to tear down
infrastructure with safety confirmations and audit logging.

WARNING: This is a DESTRUCTIVE operation that cannot be undone!

Usage: uv run ipe/ipe_destroy.py [options]

Options:
  --environment=<env>     Environment: dev, staging, prod (required)
  --delete-ami            Also delete AMI and EBS snapshots (default: false)
  --confirm               REQUIRED: Confirm destruction (safety check)
  --dry-run               Show what would be destroyed without executing
  --wait / --no-wait      Wait for completion (default: --wait)
  --timeout=<minutes>     Destruction timeout (default: 20)
  --poll-interval=<sec>   Status poll interval (default: 10)
  --ipe-id=<id>           IPE workflow ID for tracking
  --output-format=<fmt>   Output format: json, text (default: text)
  --force                 Skip extra production confirmation

Examples:
  # Dry run - see what would be destroyed
  uv run ipe/ipe_destroy.py --environment=dev --dry-run

  # Destroy dev infrastructure (keep AMI)
  uv run ipe/ipe_destroy.py --environment=dev --confirm

  # Destroy everything including AMI
  uv run ipe/ipe_destroy.py --environment=dev --delete-ami --confirm

  # Destroy staging (requires extra typing confirmation)
  uv run ipe/ipe_destroy.py --environment=staging --confirm

  # Destroy production (VERY DANGEROUS - extra confirmation required)
  uv run ipe/ipe_destroy.py --environment=prod --confirm

Exit Codes:
  0 - Success
  1 - Destruction failed
  2 - Timeout waiting for workflow
  3 - Invalid arguments
  4 - Prerequisites not met (gh CLI)
  5 - User cancelled/aborted
"""

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv

# Add ipe directory to path for module imports
script_dir = Path(__file__).parent.resolve()
repo_root = script_dir.parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(repo_root))

# Try to import IPE modules (graceful fallback)
try:
    from ipe.ipe_modules.ipe_logging import (
        rotate_logs_if_needed,
        setup_dual_logger,
    )

    HAS_IPE_MODULES = True
except ImportError:
    HAS_IPE_MODULES = False
    setup_dual_logger = None
    rotate_logs_if_needed = None

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_TIMEOUT = 2
EXIT_INVALID_ARGS = 3
EXIT_PREREQUISITES = 4
EXIT_CANCELLED = 5


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class DestroyOptions:
    """Options for infrastructure destruction."""

    environment: str = "sandbox"
    delete_ami: bool = False
    confirm: bool = False
    dry_run: bool = False
    force: bool = False  # Skip extra production confirmation
    wait: bool = True
    timeout: int = 20  # minutes (destroy is faster than build)
    poll_interval: int = 10  # seconds
    ipe_id: Optional[str] = None
    output_format: str = "text"


@dataclass
class DestroyResult:
    """Result of infrastructure destruction."""

    success: bool
    environment: str = "sandbox"
    ami_deleted: bool = False
    ami_id: Optional[str] = None
    run_id: Optional[str] = None
    run_url: Optional[str] = None
    resources_destroyed: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None
    dry_run: bool = False
    cancelled: bool = False


@dataclass
class InfrastructureState:
    """Current infrastructure state for dry-run display."""

    environment: str
    has_infrastructure: bool = False
    ami_id: Optional[str] = None
    instance_id: Optional[str] = None
    elastic_ip: Optional[str] = None
    resources: List[str] = field(default_factory=list)


# =============================================================================
# Argument Parsing
# =============================================================================


def parse_arguments() -> DestroyOptions:
    """Parse command line arguments."""
    options = DestroyOptions()
    environment_set = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg.startswith("--environment="):
            env = arg.split("=", 1)[1]
            if env not in ["dev", "staging", "prod"]:
                print(
                    f"Error: Invalid environment '{env}'. Must be: dev, staging, prod"
                )
                sys.exit(EXIT_INVALID_ARGS)
            options.environment = env
            environment_set = True
        elif arg == "--delete-ami":
            options.delete_ami = True
        elif arg == "--confirm":
            options.confirm = True
        elif arg == "--dry-run":
            options.dry_run = True
        elif arg == "--force":
            options.force = True
        elif arg == "--wait":
            options.wait = True
        elif arg == "--no-wait":
            options.wait = False
        elif arg.startswith("--timeout="):
            options.timeout = int(arg.split("=", 1)[1])
        elif arg.startswith("--poll-interval="):
            options.poll_interval = int(arg.split("=", 1)[1])
        elif arg.startswith("--ipe-id="):
            options.ipe_id = arg.split("=", 1)[1]
        elif arg.startswith("--output-format="):
            fmt = arg.split("=", 1)[1]
            if fmt not in ["text", "json"]:
                print(f"Error: Invalid output format '{fmt}'")
                sys.exit(EXIT_INVALID_ARGS)
            options.output_format = fmt
        elif arg in ["--help", "-h"]:
            print(__doc__)
            sys.exit(EXIT_SUCCESS)
        else:
            print(f"Error: Unknown argument: {arg}")
            sys.exit(EXIT_INVALID_ARGS)

        i += 1

    # Environment is required
    if not environment_set:
        print("Error: --environment is required")
        print("Usage: uv run ipe/ipe_destroy.py --environment=dev --confirm")
        sys.exit(EXIT_INVALID_ARGS)

    return options


# =============================================================================
# Safety Confirmations
# =============================================================================


def require_confirmation(options: DestroyOptions, logger: logging.Logger) -> bool:
    """
    Require explicit confirmation for destruction.
    Returns True if confirmed, False if cancelled.
    """
    if options.dry_run:
        return True  # Dry run doesn't need confirmation

    if not options.confirm:
        logger.error("")
        logger.error("=" * 60)
        logger.error("SAFETY CHECK FAILED")
        logger.error("=" * 60)
        logger.error("")
        logger.error("You must use --confirm to acknowledge this destructive operation.")
        logger.error("")
        logger.error("Example:")
        logger.error(
            f"  uv run ipe/ipe_destroy.py --environment={options.environment} --confirm"
        )
        logger.error("")
        if options.delete_ami:
            logger.error(
                "WARNING: --delete-ami will permanently delete the AMI and snapshots!"
            )
        logger.error("=" * 60)
        return False

    # Extra confirmation for staging/production
    if options.environment in ["staging", "prod"] and not options.force:
        logger.warning("")
        logger.warning("=" * 60)
        logger.warning(
            f"DESTRUCTIVE OPERATION: {options.environment.upper()} ENVIRONMENT"
        )
        logger.warning("=" * 60)
        logger.warning("")
        logger.warning(
            f"You are about to destroy the {options.environment} environment."
        )
        logger.warning("")

        if options.delete_ami:
            logger.warning("This will ALSO DELETE the AMI and all snapshots!")

        logger.warning("")
        logger.warning(f"Type '{options.environment.upper()}' to confirm:")

        try:
            user_input = input("> ").strip()
            if user_input != options.environment.upper():
                logger.error("")
                logger.error("Confirmation failed. Destruction cancelled.")
                return False
            logger.info("")
            logger.info("Confirmation received. Proceeding with destruction...")
        except (EOFError, KeyboardInterrupt):
            logger.error("")
            logger.error("Destruction cancelled by user.")
            return False

    return True


# =============================================================================
# GitHub CLI Operations
# =============================================================================


def check_github_cli(logger: logging.Logger) -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    # Check if gh is installed
    result = subprocess.run(["which", "gh"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("ERROR: GitHub CLI (gh) is not installed")
        logger.error("Install with: brew install gh")
        return False

    # Check if authenticated
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("ERROR: GitHub CLI is not authenticated")
        logger.error("Authenticate with: gh auth login")
        return False

    logger.debug("GitHub CLI is available and authenticated")
    return True


def get_infrastructure_state(
    environment: str, logger: logging.Logger
) -> InfrastructureState:
    """
    Query current infrastructure state for dry-run display.
    Uses terraform state list via local terraform.
    """
    state = InfrastructureState(environment=environment)

    # Check for terraform directory
    terraform_dir = repo_root / "io" / "terraform"
    if terraform_dir.exists():
        result = subprocess.run(
            ["terraform", "state", "list"],
            capture_output=True,
            text=True,
            cwd=str(terraform_dir),
        )

        if result.returncode == 0 and result.stdout.strip():
            state.has_infrastructure = True
            state.resources = result.stdout.strip().split("\n")
            logger.debug(f"Found {len(state.resources)} resources in terraform state")

            # Try to get specific outputs
            outputs = subprocess.run(
                ["terraform", "output", "-json"],
                capture_output=True,
                text=True,
                cwd=str(terraform_dir),
            )
            if outputs.returncode == 0:
                try:
                    output_data = json.loads(outputs.stdout)
                    state.ami_id = output_data.get("ami_id", {}).get("value")
                    state.instance_id = output_data.get("instance_id", {}).get("value")
                    state.elastic_ip = output_data.get("elastic_ip", {}).get("value")
                except json.JSONDecodeError:
                    pass

    return state


def trigger_destroy_workflow(
    options: DestroyOptions, logger: logging.Logger
) -> Optional[str]:
    """
    Trigger destroy-infrastructure.yml workflow.
    Returns run_id on success, None on failure.
    """
    logger.info(f"Triggering destroy workflow for {options.environment}...")

    # Build workflow command
    cmd = [
        "gh",
        "workflow",
        "run",
        "destroy-infrastructure.yml",
        "-f",
        "confirmation=DESTROY",
        "-f",
        f"environment={options.environment}",
        "-f",
        f"delete_ami={'true' if options.delete_ami else 'false'}",
    ]

    logger.debug(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed to trigger workflow: {result.stderr}")
        return None

    logger.info("Workflow triggered, waiting for registration...")
    time.sleep(5)  # Wait for GitHub to register the run

    # Get latest run ID
    result = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--workflow=destroy-infrastructure.yml",
            "--limit",
            "1",
            "--json",
            "databaseId,status",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"Failed to get run ID: {result.stderr}")
        return None

    try:
        runs = json.loads(result.stdout)
        if not runs:
            logger.error("No workflow runs found")
            return None

        run_id = str(runs[0]["databaseId"])
        logger.info(f"Workflow run ID: {run_id}")
        return run_id
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse run list: {e}")
        return None


def poll_workflow_status(
    run_id: str,
    timeout_minutes: int,
    poll_interval_seconds: int,
    logger: logging.Logger,
) -> Tuple[bool, str]:
    """
    Poll GitHub Actions workflow until completion or timeout.
    Returns (success, conclusion) tuple.
    """
    logger.info(f"Polling workflow status (timeout: {timeout_minutes} min)...")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    # Get repo for URL
    repo_result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True,
        text=True,
    )
    repo_name = (
        repo_result.stdout.strip() if repo_result.returncode == 0 else "unknown/repo"
    )
    logger.info(f"View: https://github.com/{repo_name}/actions/runs/{run_id}")

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"Timeout exceeded ({timeout_minutes} minutes)")
            return False, "timeout"

        result = subprocess.run(
            ["gh", "run", "view", run_id, "--json", "status,conclusion"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            time.sleep(poll_interval_seconds)
            continue

        try:
            data = json.loads(result.stdout)
            status = data["status"]
            conclusion = data.get("conclusion")

            elapsed_min = int(elapsed / 60)
            elapsed_sec = int(elapsed % 60)
            status_msg = f"Status: {status}"
            if conclusion:
                status_msg += f" ({conclusion})"
            else:
                status_msg += f" - {elapsed_min}m {elapsed_sec}s"
            logger.info(status_msg)

            if status == "completed":
                return conclusion == "success", conclusion or "unknown"

            time.sleep(poll_interval_seconds)
        except json.JSONDecodeError:
            time.sleep(poll_interval_seconds)


# =============================================================================
# Output Functions
# =============================================================================


def display_dry_run(
    options: DestroyOptions, state: InfrastructureState, logger: logging.Logger
) -> None:
    """Display what would be destroyed in dry-run mode."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("DRY RUN - No changes will be made")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"Environment: {options.environment}")
    logger.info("")

    if not state.has_infrastructure:
        logger.info("No infrastructure found in terraform state.")
        logger.info("Nothing to destroy.")
    else:
        logger.info("Resources that WOULD be destroyed:")
        logger.info("-" * 40)

        # Standard resources
        logger.info("  - EC2 Instance")
        logger.info("  - Elastic IP")
        logger.info("  - Security Group")
        logger.info("  - SSH Key Pair")

        if state.instance_id:
            logger.info(f"    Instance ID: {state.instance_id}")
        if state.elastic_ip:
            logger.info(f"    Elastic IP:  {state.elastic_ip}")

        if options.delete_ami:
            logger.info("")
            logger.info("  ALSO DELETING (--delete-ami):")
            logger.info("  - AMI (Amazon Machine Image)")
            logger.info("  - EBS Snapshots")
            if state.ami_id:
                logger.info(f"    AMI ID: {state.ami_id}")

        logger.info("")
        logger.info(f"Total resources: {len(state.resources)}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("To execute destruction, run:")
    cmd = f"uv run ipe/ipe_destroy.py --environment={options.environment} --confirm"
    if options.delete_ami:
        cmd += " --delete-ami"
    logger.info(f"  {cmd}")
    logger.info("=" * 60)


def output_result(
    result: DestroyResult, output_format: str, logger: logging.Logger
) -> None:
    """Output destruction result in specified format."""
    if output_format == "json":
        output = asdict(result)
        print(json.dumps(output, indent=2))
        return

    # Text format
    logger.info("")
    logger.info("=" * 60)

    if result.dry_run:
        logger.info("DRY RUN COMPLETE - No changes made")
    elif result.cancelled:
        logger.info("DESTRUCTION CANCELLED")
    elif result.success:
        logger.info("DESTRUCTION COMPLETE")
    else:
        logger.info("DESTRUCTION FAILED")

    logger.info("=" * 60)
    logger.info(f"Environment:  {result.environment}")

    if result.ami_deleted and result.ami_id:
        logger.info(f"AMI Deleted:  {result.ami_id}")
    elif result.success and not result.ami_deleted:
        logger.info("AMI Status:   Retained (use --delete-ami to remove)")

    if result.run_url:
        logger.info(f"Workflow URL: {result.run_url}")

    if result.duration_seconds:
        mins = result.duration_seconds // 60
        secs = result.duration_seconds % 60
        logger.info(f"Duration:     {mins}m {secs}s")

    if result.error_message:
        logger.error(f"Error:        {result.error_message}")

    logger.info("=" * 60)

    if result.success and not result.dry_run:
        logger.info("")
        logger.info("Infrastructure has been destroyed.")
        logger.info("")
        logger.info("To redeploy:")
        logger.info("  uv run ipe/ipe_build.py --environment=dev")
        logger.info("  # or")
        logger.info("  uv run ipe/ipe_deploy.py deploy --environment=dev")


def write_audit_log(
    options: DestroyOptions, result: DestroyResult, logger: logging.Logger
) -> None:
    """Write destruction audit log for compliance/tracking."""
    if options.dry_run:
        return  # Don't log dry runs

    audit_dir = repo_root / "ipe_logs" / "destroy" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    audit_file = audit_dir / f"{timestamp}_{options.environment}_destroy.json"

    audit_record = {
        "timestamp": datetime.now().isoformat(),
        "environment": options.environment,
        "delete_ami": options.delete_ami,
        "success": result.success,
        "cancelled": result.cancelled,
        "run_id": result.run_id,
        "run_url": result.run_url,
        "ami_deleted": result.ami_deleted,
        "ami_id": result.ami_id,
        "duration_seconds": result.duration_seconds,
        "error_message": result.error_message,
        "user": os.getenv("USER", "unknown"),
        "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
    }

    try:
        with open(audit_file, "w") as f:
            json.dump(audit_record, f, indent=2)
        logger.debug(f"Audit log written: {audit_file}")
    except Exception as e:
        logger.warning(f"Failed to write audit log: {e}")


# =============================================================================
# Main Function
# =============================================================================


def main() -> int:
    """Main entry point."""
    load_dotenv()
    options = parse_arguments()

    if not options.ipe_id:
        options.ipe_id = f"destroy-{int(time.time())}"

    # Setup logging
    if HAS_IPE_MODULES and setup_dual_logger:
        logger, _ = setup_dual_logger(options.ipe_id, "destroy", "ipe_destroy")
        if rotate_logs_if_needed:
            rotate_logs_if_needed()
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logger = logging.getLogger("ipe_destroy")

    # Display header
    logger.info("")
    logger.info("=" * 60)
    logger.info("ASW IO Destroy - Infrastructure Destruction")
    logger.info("=" * 60)
    logger.info(f"Environment:  {options.environment}")
    logger.info(f"Delete AMI:   {options.delete_ami}")
    logger.info(f"Dry Run:      {options.dry_run}")
    logger.info("=" * 60)

    # Check prerequisites
    if not check_github_cli(logger):
        result = DestroyResult(
            success=False,
            environment=options.environment,
            error_message="GitHub CLI not available",
        )
        output_result(result, options.output_format, logger)
        return EXIT_PREREQUISITES

    # Get current infrastructure state (for dry-run)
    state = get_infrastructure_state(options.environment, logger)

    # Dry run mode
    if options.dry_run:
        display_dry_run(options, state, logger)
        result = DestroyResult(
            success=True, environment=options.environment, dry_run=True
        )
        output_result(result, options.output_format, logger)
        return EXIT_SUCCESS

    # Safety confirmation
    if not require_confirmation(options, logger):
        result = DestroyResult(
            success=False,
            environment=options.environment,
            cancelled=True,
            error_message="Destruction not confirmed",
        )
        output_result(result, options.output_format, logger)
        write_audit_log(options, result, logger)
        return EXIT_CANCELLED

    # Trigger workflow
    start_time = time.time()
    run_id = trigger_destroy_workflow(options, logger)

    if not run_id:
        result = DestroyResult(
            success=False,
            environment=options.environment,
            error_message="Failed to trigger workflow",
        )
        output_result(result, options.output_format, logger)
        write_audit_log(options, result, logger)
        return EXIT_FAILURE

    # Get run URL
    repo_result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True,
        text=True,
    )
    repo_name = repo_result.stdout.strip() if repo_result.returncode == 0 else "unknown"
    run_url = f"https://github.com/{repo_name}/actions/runs/{run_id}"

    # No-wait mode
    if not options.wait:
        logger.info("--no-wait specified, returning immediately")
        result = DestroyResult(
            success=True,
            environment=options.environment,
            run_id=run_id,
            run_url=run_url,
            ami_deleted=options.delete_ami,
        )
        output_result(result, options.output_format, logger)
        return EXIT_SUCCESS

    # Poll for completion
    success, conclusion = poll_workflow_status(
        run_id, options.timeout, options.poll_interval, logger
    )

    duration = int(time.time() - start_time)

    if not success:
        exit_code = EXIT_TIMEOUT if conclusion == "timeout" else EXIT_FAILURE
        result = DestroyResult(
            success=False,
            environment=options.environment,
            run_id=run_id,
            run_url=run_url,
            error_message=f"Workflow {conclusion}",
            duration_seconds=duration,
        )
        output_result(result, options.output_format, logger)
        write_audit_log(options, result, logger)
        return exit_code

    # Success
    result = DestroyResult(
        success=True,
        environment=options.environment,
        ami_deleted=options.delete_ami,
        ami_id=state.ami_id if options.delete_ami else None,
        run_id=run_id,
        run_url=run_url,
        duration_seconds=duration,
    )

    output_result(result, options.output_format, logger)
    write_audit_log(options, result, logger)
    return EXIT_SUCCESS


# =============================================================================
# Programmatic Interface
# =============================================================================


def destroy_infrastructure(
    environment: str = "sandbox",
    delete_ami: bool = False,
    wait: bool = True,
    timeout: int = 20,
    ipe_id: Optional[str] = None,
    skip_confirmation: bool = False,
) -> DestroyResult:
    """
    Destroy infrastructure using GitHub Actions (programmatic interface).

    WARNING: This is a destructive operation!

    Args:
        environment: Target environment (dev, staging, prod)
        delete_ami: Also delete AMI and snapshots
        wait: Wait for completion
        timeout: Timeout in minutes
        ipe_id: Optional tracking ID
        skip_confirmation: Skip interactive confirmation (DANGEROUS)

    Returns:
        DestroyResult with operation status

    Example:
        from ipe.ipe_destroy import destroy_infrastructure
        result = destroy_infrastructure(
            environment="sandbox",
            delete_ami=False,
            skip_confirmation=True
        )
        if result.success:
            print("Infrastructure destroyed")
    """
    if not skip_confirmation:
        raise ValueError(
            "Programmatic destruction requires skip_confirmation=True. "
            "This is a safety measure. Set skip_confirmation=True to proceed."
        )

    options = DestroyOptions(
        environment=environment,
        delete_ami=delete_ami,
        confirm=True,  # Skip CLI confirmation
        force=True,  # Skip interactive prompt
        wait=wait,
        timeout=timeout,
        ipe_id=ipe_id or f"destroy-{int(time.time())}",
    )

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ipe_destroy")

    if not check_github_cli(logger):
        return DestroyResult(
            success=False,
            environment=environment,
            error_message="GitHub CLI not available",
        )

    run_id = trigger_destroy_workflow(options, logger)
    if not run_id:
        return DestroyResult(
            success=False,
            environment=environment,
            error_message="Failed to trigger workflow",
        )

    if not wait:
        return DestroyResult(
            success=True, environment=environment, run_id=run_id, ami_deleted=delete_ami
        )

    success, conclusion = poll_workflow_status(run_id, timeout, 10, logger)

    return DestroyResult(
        success=success,
        environment=environment,
        run_id=run_id,
        ami_deleted=delete_ami if success else False,
        error_message=None if success else f"Workflow {conclusion}",
    )


def destroy_from_issue(
    issue_number: str,
    ipe_id: str,
    environment: str = "sandbox",
    delete_ami: bool = False,
) -> int:
    """
    Entry point for GitHub issue-triggered destruction.

    This is called by the webhook router when /ipe_destroy is detected.
    Confirmation is already validated by the webhook.

    Args:
        issue_number: GitHub issue number
        ipe_id: IPE tracking ID
        environment: Target environment (dev, staging, prod)
        delete_ami: Whether to also delete AMI and snapshots

    Returns:
        Exit code (0=success, non-zero=failure)
    """
    load_dotenv()

    # Try to import IPE modules for GitHub comments and state
    try:
        from ipe.ipe_modules.ipe_github import make_issue_comment
        from ipe.ipe_modules.ipe_state import IPEState
    except ImportError:
        # Fallback - just run without GitHub comments
        make_issue_comment = None
        IPEState = None

    # Setup logging
    if HAS_IPE_MODULES and setup_dual_logger:
        logger, _ = setup_dual_logger(ipe_id, "destroy", "ipe_destroy")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logger = logging.getLogger("ipe_destroy")

    # Load/create state if available
    if IPEState:
        state = ASWIOState.load(ipe_id)
        if not state:
            state = ASWIOState(ipe_id)
        state.update(
            ipe_id=ipe_id,
            issue_number=issue_number,
            workflow="ipe_destroy",
            environment=environment,
            delete_ami=delete_ami,
        )
        state.save("ipe_destroy")

    # Post start notification
    if make_issue_comment:
        make_issue_comment(
            issue_number,
            f"## ASW IO Destroy Started\n\n"
            f"| Parameter | Value |\n"
            f"|-----------|-------|\n"
            f"| IPE ID | `{ipe_id}` |\n"
            f"| Environment | `{environment}` |\n"
            f"| Delete AMI | `{delete_ami}` |\n\n"
            f"Triggering destroy-infrastructure workflow...\n\n"
            f"**This operation CANNOT be undone!**",
        )

    logger.info(f"Starting issue-triggered destruction for issue #{issue_number}")
    logger.info(f"Environment: {environment}, Delete AMI: {delete_ami}")

    try:
        # Call the programmatic interface
        result = destroy_infrastructure(
            environment=environment,
            delete_ami=delete_ami,
            wait=True,
            timeout=20,
            ipe_id=ipe_id,
            skip_confirmation=True,  # Already confirmed via issue comment
        )

        if result.success:
            if make_issue_comment:
                make_issue_comment(
                    issue_number,
                    f"## Infrastructure Destroyed Successfully\n\n"
                    f"| Result | Value |\n"
                    f"|--------|-------|\n"
                    f"| Environment | `{result.environment}` |\n"
                    f"| AMI Deleted | `{result.ami_deleted}` |\n"
                    f"| Run ID | `{result.run_id}` |\n"
                    f"| Duration | `{result.duration_seconds}s` |\n\n"
                    f"[View Workflow Run]({result.run_url})\n\n"
                    f"To redeploy: `/ipe_deploy mode=deploy-latest-ami environment={environment}`",
                )
            if IPEState and state:
                state.update(status="completed", run_id=result.run_id)
                state.save("ipe_destroy")
            logger.info("Destruction completed successfully")
            return EXIT_SUCCESS
        else:
            if make_issue_comment:
                make_issue_comment(
                    issue_number,
                    f"## Destruction Failed\n\n"
                    f"Error: {result.error_message}\n\n"
                    f"[View Workflow Run]({result.run_url})\n\n"
                    f"Please check the workflow logs for details.",
                )
            if IPEState and state:
                state.update(status="failed", error=result.error_message)
                state.save("ipe_destroy")
            logger.error(f"Destruction failed: {result.error_message}")
            return EXIT_FAILURE

    except Exception as e:
        error_msg = str(e)
        if make_issue_comment:
            make_issue_comment(
                issue_number,
                f"## Destruction Error\n\n"
                f"An unexpected error occurred:\n"
                f"```\n{error_msg}\n```\n\n"
                f"Please check the logs at: `agents/{ipe_id}/ipe_destroy/`",
            )
        if IPEState and state:
            state.update(status="error", error=error_msg)
            state.save("ipe_destroy")
        logger.exception("Unexpected error during destruction")
        return EXIT_FAILURE


if __name__ == "__main__":
    # Check if called with issue arguments (webhook mode)
    if len(sys.argv) >= 3 and sys.argv[1].isdigit():
        # Called by webhook: ipe_destroy.py <issue_number> <ipe_id> [environment] [delete_ami]
        issue_number = sys.argv[1]
        ipe_id = sys.argv[2]
        environment = sys.argv[3] if len(sys.argv) > 3 else "sandbox"
        delete_ami = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False

        sys.exit(destroy_from_issue(issue_number, ipe_id, environment, delete_ami))
    else:
        # CLI mode
        sys.exit(main())
