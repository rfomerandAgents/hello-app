#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# requires-python = ">=3.10"
# ///

"""
ASW IO Deploy - GitHub Actions Infrastructure Deployment Wrapper

Triggers the infrastructure-deploy.yml workflow to deploy infrastructure
with multiple deployment mode options.

Usage: uv run ipe/ipe_deploy.py [options]

Options:
  --mode=<mode>           Deployment mode (required):
                            full-deploy     - Build new AMI and deploy
                            deploy-latest-ami - Use most recent AMI (fastest)
                            deploy-custom-ami - Deploy specific AMI by ID
                            plan-only       - Terraform plan without apply
  --build-new-ami=<bool>  Override AMI build behavior:
                            true  - Force new AMI build (sets mode=full-deploy)
                            false - Skip AMI build (sets mode=deploy-latest-ami)
  --environment=<env>     Environment: dev, staging, prod (default: dev)
  --ami-id=<id>           AMI ID (required for deploy-custom-ami mode)
  --branch=<branch>       Git branch to deploy from (default: main)
  --dry-run               Show what would be done without executing
  --wait / --no-wait      Wait for completion (default: --wait)
  --timeout=<minutes>     Deployment timeout in minutes (default: 30)
  --poll-interval=<sec>   Status poll interval (default: 15)
  --ipe-id=<id>           IPE workflow ID for tracking
  --output-format=<fmt>   Output format: json, text (default: text)

Exit Codes:
  0 - Success
  1 - Deployment failed
  2 - Timeout waiting for workflow
  3 - Invalid arguments
  4 - Prerequisites not met (gh CLI)

Examples:
  # Deploy with new AMI build (full deployment)
  uv run ipe/ipe_deploy.py --mode=full-deploy --environment=dev

  # Deploy using latest existing AMI (fastest)
  uv run ipe/ipe_deploy.py --mode=deploy-latest-ami --environment=dev

  # Deploy specific AMI
  uv run ipe/ipe_deploy.py --mode=deploy-custom-ami --ami-id=ami-0123456789abcdef0 --environment=staging

  # Plan only (no changes applied)
  uv run ipe/ipe_deploy.py --mode=plan-only --environment=prod

  # Dry run - see what command would be executed
  uv run ipe/ipe_deploy.py --mode=deploy-latest-ami --environment=dev --dry-run

  # Deploy with explicit AMI build control
  uv run ipe/ipe_deploy.py --build-new-ami=true --environment=dev
  uv run ipe/ipe_deploy.py --build-new-ami=false --environment=staging

  # JSON output for scripting
  uv run ipe/ipe_deploy.py --mode=deploy-latest-ami --output-format=json

Callable from IPE/ADW workflows:
  from ipe.ipe_deploy import deploy_infrastructure
  result = deploy_infrastructure(mode="deploy-latest-ami", environment="sandbox")
  if result.success:
      print(f"Deployed to: {result.public_ip}")
"""

import json
import logging
import os
import re
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

# Valid deployment modes (matches workflow inputs)
VALID_MODES = ["full-deploy", "deploy-latest-ami", "deploy-custom-ami", "plan-only"]
VALID_ENVIRONMENTS = ["dev", "staging", "prod", "sandbox"]

# Map environments to Terraform Cloud workspace names
ENVIRONMENT_TO_WORKSPACE = {
    "dev": "{{PROJECT_SLUG}}-dev",
    "staging": "{{PROJECT_SLUG}}-staging",
    "prod": "{{PROJECT_SLUG}}-prod",
    "sandbox": "{{PROJECT_SLUG}}-sandbox",
}


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class DeployOptions:
    """Options for infrastructure deployment."""

    mode: str = "deploy-latest-ami"
    environment: str = "sandbox"
    ami_id: Optional[str] = None  # Required for deploy-custom-ami
    branch: str = "main"
    dry_run: bool = False
    wait: bool = True
    timeout: int = 30  # minutes
    poll_interval: int = 15  # seconds
    ipe_id: Optional[str] = None
    output_format: str = "text"
    build_new_ami: Optional[bool] = None  # None means not specified


@dataclass
class DeployResult:
    """Result of infrastructure deployment."""

    success: bool
    mode: str = "deploy-latest-ami"
    environment: str = "sandbox"
    public_ip: Optional[str] = None
    ami_id: Optional[str] = None
    run_id: Optional[str] = None
    run_url: Optional[str] = None
    site_urls: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None
    dry_run: bool = False
    plan_only: bool = False


# =============================================================================
# Argument Parsing
# =============================================================================


def parse_arguments() -> DeployOptions:
    """Parse command line arguments."""
    options = DeployOptions()
    mode_set = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
            if mode not in VALID_MODES:
                print(f"Error: Invalid mode '{mode}'. Valid modes: {VALID_MODES}")
                sys.exit(EXIT_INVALID_ARGS)
            options.mode = mode
            mode_set = True
        elif arg.startswith("--environment="):
            env = arg.split("=", 1)[1]
            if env not in VALID_ENVIRONMENTS:
                print(f"Error: Invalid environment '{env}'. Valid: {VALID_ENVIRONMENTS}")
                sys.exit(EXIT_INVALID_ARGS)
            options.environment = env
        elif arg.startswith("--ami-id="):
            options.ami_id = arg.split("=", 1)[1]
            # Validate AMI ID format
            if not options.ami_id.startswith("ami-"):
                print("Error: Invalid AMI ID format. Must start with 'ami-'")
                sys.exit(EXIT_INVALID_ARGS)
        elif arg.startswith("--build-new-ami="):
            value = arg.split("=", 1)[1].lower()
            if value == "true":
                options.build_new_ami = True
            elif value == "false":
                options.build_new_ami = False
            else:
                print(f"Error: Invalid --build-new-ami value '{value}'. Must be 'true' or 'false'")
                sys.exit(EXIT_INVALID_ARGS)
        elif arg.startswith("--branch="):
            options.branch = arg.split("=", 1)[1]
        elif arg == "--dry-run":
            options.dry_run = True
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
                print(f"Error: Invalid output format '{fmt}'. Valid: text, json")
                sys.exit(EXIT_INVALID_ARGS)
            options.output_format = fmt
        elif arg in ["--help", "-h"]:
            print(__doc__)
            sys.exit(EXIT_SUCCESS)
        else:
            print(f"Error: Unknown argument: {arg}")
            sys.exit(EXIT_INVALID_ARGS)

        i += 1

    # Mode is required (unless --build-new-ami is specified)
    if not mode_set and options.build_new_ami is None:
        print("Error: --mode is required (or use --build-new-ami=true/false)")
        print("Usage: uv run ipe/ipe_deploy.py --mode=deploy-latest-ami --environment=dev")
        print(f"Valid modes: {VALID_MODES}")
        sys.exit(EXIT_INVALID_ARGS)

    # Validate mode-specific requirements
    if options.mode == "deploy-custom-ami" and not options.ami_id:
        print("Error: --ami-id is required when using --mode=deploy-custom-ami")
        sys.exit(EXIT_INVALID_ARGS)

    # Warn if ami_id provided but not using deploy-custom-ami
    if options.ami_id and options.mode != "deploy-custom-ami":
        print(f"Warning: --ami-id is only used with --mode=deploy-custom-ami")
        print(f"Current mode '{options.mode}' will ignore the provided AMI ID")

    # Apply --build-new-ami override to mode
    if options.build_new_ami is not None:
        if options.build_new_ami:
            # --build-new-ami=true forces mode=full-deploy
            if options.mode in ["deploy-custom-ami", "plan-only", "deploy-latest-ami"]:
                print(f"Warning: --build-new-ami=true overrides --mode={options.mode} to mode=full-deploy")
            options.mode = "full-deploy"
        else:
            # --build-new-ami=false forces mode=deploy-latest-ami
            if options.mode in ["full-deploy", "deploy-custom-ami", "plan-only"]:
                print(f"Warning: --build-new-ami=false overrides --mode={options.mode} to mode=deploy-latest-ami")
            options.mode = "deploy-latest-ami"

    return options


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


def build_workflow_command(options: DeployOptions) -> List[str]:
    """Build the gh workflow run command based on deployment mode.

    The GitHub Actions workflow will automatically set TF_WORKSPACE based on
    the environment parameter using the pattern: {{PROJECT_SLUG}}-{environment}
    """
    cmd = [
        "gh",
        "workflow",
        "run",
        "infrastructure-deploy.yml",
        "--ref",
        options.branch,
        "-f",
        f"deployment_mode={options.mode}",
        "-f",
        f"environment={options.environment}",
    ]

    # Add custom AMI ID for deploy-custom-ami mode
    if options.mode == "deploy-custom-ami" and options.ami_id:
        cmd.extend(["-f", f"custom_ami_id={options.ami_id}"])

    return cmd


def trigger_deploy_workflow(
    options: DeployOptions, logger: logging.Logger
) -> Optional[str]:
    """
    Trigger infrastructure-deploy.yml workflow.
    Returns run_id on success, None on failure.
    """
    logger.info("Triggering deployment workflow...")
    logger.info(f"  Mode:        {options.mode}")
    logger.info(f"  Environment: {options.environment}")
    logger.info(f"  Branch:      {options.branch}")
    if options.ami_id:
        logger.info(f"  AMI ID:      {options.ami_id}")

    cmd = build_workflow_command(options)
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
            "--workflow=infrastructure-deploy.yml",
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


def get_deployment_details(run_id: str, logger: logging.Logger) -> dict:
    """Extract deployment details from completed workflow."""
    details = {
        "public_ip": None,
        "ami_id": None,
        "site_urls": [],
    }

    logger.info("Extracting deployment details from workflow...")

    # Get workflow run logs/summary
    result = subprocess.run(
        ["gh", "run", "view", run_id, "--log"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        # Extract public IP from logs
        ip_match = re.search(
            r"public_ip[=:]\s*(\d+\.\d+\.\d+\.\d+)", result.stdout, re.IGNORECASE
        )
        if ip_match:
            details["public_ip"] = ip_match.group(1)
            logger.info(f"Public IP: {details['public_ip']}")

        # Extract AMI ID from logs
        ami_match = re.search(
            r"ami_id[=:]\s*(ami-[a-f0-9]+)", result.stdout, re.IGNORECASE
        )
        if ami_match:
            details["ami_id"] = ami_match.group(1)
            logger.info(f"AMI ID: {details['ami_id']}")

    # Standard site URLs for this project
    details["site_urls"] = [
        "https://{{PROJECT_DOMAIN}}",
        "https://www.{{PROJECT_DOMAIN}}",
    ]

    return details


# =============================================================================
# Output Functions
# =============================================================================


def display_dry_run(options: DeployOptions, logger: logging.Logger) -> None:
    """Display what would be executed in dry-run mode."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("DRY RUN - No changes will be made")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"Deployment Mode: {options.mode}")
    logger.info(f"Environment:     {options.environment}")
    logger.info(f"Branch:          {options.branch}")
    if options.ami_id:
        logger.info(f"AMI ID:          {options.ami_id}")
    logger.info("")
    logger.info("Command that would be executed:")
    logger.info("-" * 40)

    cmd = build_workflow_command(options)
    logger.info(f"  {' '.join(cmd)}")

    logger.info("")
    logger.info("Mode explanation:")
    mode_descriptions = {
        "full-deploy": "Build a new AMI from current code, then deploy infrastructure",
        "deploy-latest-ami": "Find the most recent AMI and deploy with it (fastest)",
        "deploy-custom-ami": f"Deploy using specific AMI: {options.ami_id}",
        "plan-only": "Run Terraform plan without applying changes",
    }
    logger.info(f"  {mode_descriptions.get(options.mode, 'Unknown mode')}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("To execute deployment, remove --dry-run:")
    cmd_str = (
        f"uv run ipe/ipe_deploy.py --mode={options.mode} "
        f"--environment={options.environment}"
    )
    if options.ami_id:
        cmd_str += f" --ami-id={options.ami_id}"
    logger.info(f"  {cmd_str}")
    logger.info("=" * 60)


def output_result(
    result: DeployResult, output_format: str, logger: logging.Logger
) -> None:
    """Output deployment result in specified format."""
    if output_format == "json":
        output = asdict(result)
        print(json.dumps(output, indent=2))
        return

    # Text format
    logger.info("")
    logger.info("=" * 60)

    if result.dry_run:
        logger.info("DRY RUN COMPLETE - No changes made")
    elif result.plan_only:
        logger.info("PLAN COMPLETE - No changes applied")
    elif result.success:
        logger.info("DEPLOYMENT SUCCESSFUL")
    else:
        logger.info("DEPLOYMENT FAILED")

    logger.info("=" * 60)
    logger.info(f"Mode:         {result.mode}")
    logger.info(f"Environment:  {result.environment}")

    if result.ami_id:
        logger.info(f"AMI ID:       {result.ami_id}")

    if result.public_ip:
        logger.info(f"Public IP:    {result.public_ip}")

    if result.run_url:
        logger.info(f"Workflow URL: {result.run_url}")

    if result.duration_seconds:
        mins = result.duration_seconds // 60
        secs = result.duration_seconds % 60
        logger.info(f"Duration:     {mins}m {secs}s")

    if result.error_message:
        logger.error(f"Error:        {result.error_message}")

    logger.info("=" * 60)

    if result.success and result.site_urls and not result.plan_only:
        logger.info("")
        logger.info("Site URLs:")
        for url in result.site_urls:
            logger.info(f"  {url}")
        logger.info("")
        logger.info("Note: DNS propagation may take up to 5 minutes")

    if result.success and not result.dry_run:
        logger.info("")
        logger.info("Next steps:")
        if result.mode == "plan-only":
            logger.info("  To apply changes:")
            logger.info(
                f"  uv run ipe/ipe_deploy.py --mode=deploy-latest-ami "
                f"--environment={result.environment}"
            )
        else:
            logger.info("  To destroy infrastructure:")
            logger.info(
                f"  uv run ipe/ipe_destroy.py --environment={result.environment} "
                "--confirm"
            )


# =============================================================================
# Main Function
# =============================================================================


def main() -> int:
    """Main entry point."""
    load_dotenv()
    options = parse_arguments()

    if not options.ipe_id:
        options.ipe_id = f"deploy-{int(time.time())}"

    # Setup logging
    if HAS_IPE_MODULES and setup_dual_logger:
        logger, _ = setup_dual_logger(options.ipe_id, "deploy", "ipe_deploy")
        if rotate_logs_if_needed:
            rotate_logs_if_needed()
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logger = logging.getLogger("ipe_deploy")

    # Display header
    logger.info("")
    logger.info("=" * 60)
    logger.info("ASW IO Deploy - Infrastructure Deployment")
    logger.info("=" * 60)
    logger.info(f"Mode:         {options.mode}")
    logger.info(f"Environment:  {options.environment}")
    logger.info(f"Branch:       {options.branch}")
    if options.ami_id:
        logger.info(f"AMI ID:       {options.ami_id}")
    logger.info(f"Dry Run:      {options.dry_run}")
    logger.info("=" * 60)

    # Check prerequisites
    if not check_github_cli(logger):
        result = DeployResult(
            success=False,
            mode=options.mode,
            environment=options.environment,
            error_message="GitHub CLI not available",
        )
        output_result(result, options.output_format, logger)
        return EXIT_PREREQUISITES

    # Dry run mode
    if options.dry_run:
        display_dry_run(options, logger)
        result = DeployResult(
            success=True,
            mode=options.mode,
            environment=options.environment,
            ami_id=options.ami_id,
            dry_run=True,
        )
        output_result(result, options.output_format, logger)
        return EXIT_SUCCESS

    # Trigger workflow
    start_time = time.time()
    run_id = trigger_deploy_workflow(options, logger)

    if not run_id:
        result = DeployResult(
            success=False,
            mode=options.mode,
            environment=options.environment,
            error_message="Failed to trigger workflow",
        )
        output_result(result, options.output_format, logger)
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
        result = DeployResult(
            success=True,
            mode=options.mode,
            environment=options.environment,
            ami_id=options.ami_id,
            run_id=run_id,
            run_url=run_url,
            plan_only=(options.mode == "plan-only"),
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
        result = DeployResult(
            success=False,
            mode=options.mode,
            environment=options.environment,
            run_id=run_id,
            run_url=run_url,
            error_message=f"Workflow {conclusion}",
            duration_seconds=duration,
        )
        output_result(result, options.output_format, logger)
        return exit_code

    # Get deployment details
    details = get_deployment_details(run_id, logger)

    # Success
    result = DeployResult(
        success=True,
        mode=options.mode,
        environment=options.environment,
        public_ip=details.get("public_ip"),
        ami_id=details.get("ami_id") or options.ami_id,
        run_id=run_id,
        run_url=run_url,
        site_urls=details.get("site_urls", []),
        duration_seconds=duration,
        plan_only=(options.mode == "plan-only"),
    )

    output_result(result, options.output_format, logger)
    return EXIT_SUCCESS


# =============================================================================
# Programmatic Interface
# =============================================================================


def deploy_infrastructure(
    mode: str = "deploy-latest-ami",
    environment: str = "sandbox",
    ami_id: Optional[str] = None,
    branch: str = "main",
    wait: bool = True,
    timeout: int = 30,
    ipe_id: Optional[str] = None,
    build_new_ami: Optional[bool] = None,
) -> DeployResult:
    """
    Deploy infrastructure using GitHub Actions (programmatic interface).

    Args:
        mode: Deployment mode (deploy, deploy-latest-ami, deploy-custom-ami, plan-only)
        environment: Target environment (dev, staging, prod)
        ami_id: AMI ID (required for deploy-custom-ami mode)
        branch: Git branch to deploy from
        wait: Wait for completion
        timeout: Timeout in minutes
        ipe_id: Optional tracking ID
        build_new_ami: Override AMI build behavior (True=build, False=skip, None=use mode)

    Returns:
        DeployResult with operation status

    Example:
        from ipe.ipe_deploy import deploy_infrastructure

        # Quick deploy using latest AMI
        result = deploy_infrastructure(mode="deploy-latest-ami", environment="sandbox")
        if result.success:
            print(f"Deployed to: {result.public_ip}")
            print(f"Site: {result.site_urls[0]}")

        # Deploy specific AMI
        result = deploy_infrastructure(
            mode="deploy-custom-ami",
            ami_id="ami-0123456789abcdef0",
            environment="staging"
        )

        # Deploy with explicit AMI build control
        result = deploy_infrastructure(build_new_ami=True, environment="sandbox")
    """
    # Apply build_new_ami override
    if build_new_ami is not None:
        mode = "full-deploy" if build_new_ami else "deploy-latest-ami"

    # Validate inputs
    if mode not in VALID_MODES:
        return DeployResult(
            success=False,
            mode=mode,
            environment=environment,
            error_message=f"Invalid mode: {mode}. Valid: {VALID_MODES}",
        )

    if mode == "deploy-custom-ami" and not ami_id:
        return DeployResult(
            success=False,
            mode=mode,
            environment=environment,
            error_message="ami_id is required for deploy-custom-ami mode",
        )

    options = DeployOptions(
        mode=mode,
        environment=environment,
        ami_id=ami_id,
        branch=branch,
        wait=wait,
        timeout=timeout,
        ipe_id=ipe_id or f"deploy-{int(time.time())}",
        build_new_ami=build_new_ami,
    )

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ipe_deploy")

    if not check_github_cli(logger):
        return DeployResult(
            success=False,
            mode=mode,
            environment=environment,
            error_message="GitHub CLI not available",
        )

    run_id = trigger_deploy_workflow(options, logger)
    if not run_id:
        return DeployResult(
            success=False,
            mode=mode,
            environment=environment,
            error_message="Failed to trigger workflow",
        )

    if not wait:
        return DeployResult(
            success=True,
            mode=mode,
            environment=environment,
            ami_id=ami_id,
            run_id=run_id,
            plan_only=(mode == "plan-only"),
        )

    success, conclusion = poll_workflow_status(run_id, timeout, 15, logger)

    if not success:
        return DeployResult(
            success=False,
            mode=mode,
            environment=environment,
            run_id=run_id,
            error_message=f"Workflow {conclusion}",
        )

    details = get_deployment_details(run_id, logger)

    return DeployResult(
        success=True,
        mode=mode,
        environment=environment,
        public_ip=details.get("public_ip"),
        ami_id=details.get("ami_id") or ami_id,
        run_id=run_id,
        site_urls=details.get("site_urls", []),
        plan_only=(mode == "plan-only"),
    )


def deploy_from_issue(
    issue_number: str,
    ipe_id: str,
    mode: str = "deploy-latest-ami",
    environment: str = "sandbox",
    ami_id: Optional[str] = None,
    build_new_ami: Optional[bool] = None,
) -> int:
    """
    Entry point for GitHub issue-triggered deployment.

    This is called by the webhook router when /ipe_deploy is detected.

    Args:
        issue_number: GitHub issue number
        ipe_id: IPE tracking ID
        mode: Deployment mode (deploy, deploy-latest-ami, deploy-custom-ami, plan-only)
        environment: Target environment (dev, staging, prod)
        ami_id: AMI ID (required for deploy-custom-ami mode)
        build_new_ami: Override AMI build behavior (True=build, False=skip, None=use mode)

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
        logger, _ = setup_dual_logger(ipe_id, "deploy", "ipe_deploy")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logger = logging.getLogger("ipe_deploy")

    # Load/create state if available
    if IPEState:
        state = ASWIOState.load(ipe_id)
        if not state:
            state = ASWIOState(ipe_id)
        state.update(
            ipe_id=ipe_id,
            issue_number=issue_number,
            workflow="ipe_deploy",
            mode=mode,
            environment=environment,
            ami_id=ami_id,
        )
        state.save("ipe_deploy")

    # Post start notification
    if make_issue_comment:
        ami_info = f"| AMI ID | `{ami_id}` |\n" if ami_id else ""
        make_issue_comment(
            issue_number,
            f"## ASW IO Deploy Started\n\n"
            f"| Parameter | Value |\n"
            f"|-----------|-------|\n"
            f"| IPE ID | `{ipe_id}` |\n"
            f"| Mode | `{mode}` |\n"
            f"| Environment | `{environment}` |\n"
            f"{ami_info}\n"
            f"Triggering infrastructure-deploy workflow...",
        )

    # Apply build_new_ami override to mode
    effective_mode = mode
    if build_new_ami is not None:
        effective_mode = "full-deploy" if build_new_ami else "deploy-latest-ami"
        logger.info(f"build_new_ami={build_new_ami} overrides mode to {effective_mode}")

    logger.info(f"Starting issue-triggered deployment for issue #{issue_number}")
    logger.info(f"Mode: {effective_mode}, Environment: {environment}")
    if ami_id:
        logger.info(f"AMI ID: {ami_id}")

    try:
        # Call the programmatic interface
        result = deploy_infrastructure(
            mode=effective_mode,
            environment=environment,
            ami_id=ami_id,
            branch="main",
            wait=True,
            timeout=30,
            ipe_id=ipe_id,
            build_new_ami=build_new_ami,
        )

        if result.success:
            if make_issue_comment:
                # Build site URLs display
                site_urls_display = "\n".join([f"- {url}" for url in result.site_urls]) if result.site_urls else "N/A"
                make_issue_comment(
                    issue_number,
                    f"## Deployment Completed Successfully\n\n"
                    f"| Result | Value |\n"
                    f"|--------|-------|\n"
                    f"| Mode | `{result.mode}` |\n"
                    f"| Environment | `{result.environment}` |\n"
                    f"| Public IP | `{result.public_ip or 'N/A'}` |\n"
                    f"| AMI ID | `{result.ami_id or 'N/A'}` |\n"
                    f"| Run ID | `{result.run_id}` |\n"
                    f"| Duration | `{result.duration_seconds}s` |\n\n"
                    f"**Site URLs:**\n{site_urls_display}\n\n"
                    f"[View Workflow Run]({result.run_url})\n\n"
                    f"To destroy: `/ipe_destroy environment={environment} DESTROY`",
                )
            if IPEState and state:
                state.update(status="completed", run_id=result.run_id, public_ip=result.public_ip)
                state.save("ipe_deploy")
            logger.info("Deployment completed successfully")
            return EXIT_SUCCESS
        else:
            if make_issue_comment:
                make_issue_comment(
                    issue_number,
                    f"## Deployment Failed\n\n"
                    f"Error: {result.error_message}\n\n"
                    f"[View Workflow Run]({result.run_url})\n\n"
                    f"Please check the workflow logs for details.",
                )
            if IPEState and state:
                state.update(status="failed", error=result.error_message)
                state.save("ipe_deploy")
            logger.error(f"Deployment failed: {result.error_message}")
            return EXIT_FAILURE

    except Exception as e:
        error_msg = str(e)
        if make_issue_comment:
            make_issue_comment(
                issue_number,
                f"## Deployment Error\n\n"
                f"An unexpected error occurred:\n"
                f"```\n{error_msg}\n```\n\n"
                f"Please check the logs at: `agents/{ipe_id}/ipe_deploy/`",
            )
        if IPEState and state:
            state.update(status="error", error=error_msg)
            state.save("ipe_deploy")
        logger.exception("Unexpected error during deployment")
        return EXIT_FAILURE


if __name__ == "__main__":
    # Check if called with issue arguments (webhook mode)
    if len(sys.argv) >= 3 and sys.argv[1].isdigit():
        # Called by webhook: ipe_deploy.py <issue> <ipe_id> [mode] [env] [ami_id] [build_new_ami]
        issue_number = sys.argv[1]
        ipe_id = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else "deploy-latest-ami"
        environment = sys.argv[4] if len(sys.argv) > 4 else "sandbox"
        ami_id = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None

        # Parse build_new_ami from string
        build_new_ami = None
        if len(sys.argv) > 6 and sys.argv[6]:
            build_new_ami = sys.argv[6].lower() == "true"

        sys.exit(deploy_from_issue(issue_number, ipe_id, mode, environment, ami_id, build_new_ami))
    else:
        # CLI mode
        sys.exit(main())
