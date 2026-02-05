#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ASW IO Build - GitHub Actions AMI Build Wrapper

Triggers the infrastructure-deploy.yml workflow in build-ami-only mode
to build a Packer AMI using GitHub Actions runners.

Usage: uv run ipe/ipe_build.py [options]

Options:
  --version=<version>            Custom AMI version (optional)
  --version-strategy=<strategy>  Version strategy: git-describe, semantic, commit-hash, timestamp
  --environment=<env>            Environment: dev, staging, prod (default: dev)
  --branch=<branch>              Git branch to build from (default: main)
  --wait / --no-wait             Wait for build completion (default: --wait)
  --timeout=<minutes>            Build timeout in minutes (default: 45)
  --poll-interval=<seconds>      Status poll interval (default: 15)
  --ipe-id=<id>                  IPE workflow ID for tracking
  --output-format=<format>       Output format: json, text (default: text)

Examples:
  # Build AMI with git-describe versioning
  uv run ipe/ipe_build.py --environment=dev

  # Build with custom version
  uv run ipe/ipe_build.py --version=v2.0.0-rc1 --environment=staging

  # Build without waiting (fire and forget)
  uv run ipe/ipe_build.py --no-wait --environment=prod

  # Build with JSON output for scripting
  uv run ipe/ipe_build.py --wait --output-format=json

Callable from IPE/ADW workflows:
  from ipe.ipe_build import build_ami
  result = build_ami(environment="sandbox", version="v1.0.0")
  if result.success:
      print(f"AMI ID: {result.ami_id}")
"""

import sys
import os
import subprocess
import logging
import time
import json
import tempfile
import re
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Add ipe directory to path for module imports
script_dir = Path(__file__).parent.resolve()
repo_root = script_dir.parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(repo_root))

# Try to import IPE modules (graceful fallback if not available)
try:
    from ipe.ipe_modules.ipe_logging import (
        setup_dual_logger,
        write_failure_log,
        display_failure_message,
        rotate_logs_if_needed
    )
    HAS_IPE_MODULES = True
except ImportError:
    HAS_IPE_MODULES = False
    setup_dual_logger = None
    rotate_logs_if_needed = None


@dataclass
class BuildOptions:
    """Options for AMI build operation."""
    version: Optional[str] = None
    version_strategy: str = "git-describe"
    environment: str = "sandbox"
    branch: str = "main"
    wait: bool = True
    timeout: int = 45  # minutes
    poll_interval: int = 15  # seconds
    ipe_id: Optional[str] = None
    output_format: str = "text"


@dataclass
class BuildResult:
    """Result of AMI build operation."""
    success: bool
    ami_id: Optional[str] = None
    ami_name: Optional[str] = None
    version: Optional[str] = None
    run_id: Optional[str] = None
    run_url: Optional[str] = None
    environment: str = "sandbox"
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None


def parse_arguments() -> BuildOptions:
    """Parse command line arguments."""
    options = BuildOptions()

    for arg in sys.argv[1:]:
        if arg.startswith("--version="):
            options.version = arg.split("=", 1)[1]
        elif arg.startswith("--version-strategy="):
            strategy = arg.split("=", 1)[1]
            valid = ["git-describe", "semantic", "commit-hash", "timestamp"]
            if strategy not in valid:
                print(f"Error: Invalid strategy '{strategy}'. Valid: {valid}")
                sys.exit(1)
            options.version_strategy = strategy
        elif arg.startswith("--environment="):
            env = arg.split("=", 1)[1]
            if env not in ["dev", "staging", "prod"]:
                print(f"Error: Invalid environment '{env}'")
                sys.exit(1)
            options.environment = env
        elif arg.startswith("--branch="):
            options.branch = arg.split("=", 1)[1]
        elif arg.startswith("--timeout="):
            options.timeout = int(arg.split("=", 1)[1])
        elif arg.startswith("--poll-interval="):
            options.poll_interval = int(arg.split("=", 1)[1])
        elif arg.startswith("--ipe-id="):
            options.ipe_id = arg.split("=", 1)[1]
        elif arg.startswith("--output-format="):
            options.output_format = arg.split("=", 1)[1]
        elif arg == "--wait":
            options.wait = True
        elif arg == "--no-wait":
            options.wait = False
        elif arg in ["--help", "-h"]:
            print(__doc__)
            sys.exit(0)

    return options


def check_github_cli(logger: Optional[logging.Logger] = None) -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    log = logger.info if logger else print
    err = logger.error if logger else print

    # Check if gh is installed
    result = subprocess.run(["which", "gh"], capture_output=True, text=True)
    if result.returncode != 0:
        err("ERROR: GitHub CLI (gh) is not installed")
        err("Install with: brew install gh")
        return False

    # Check if authenticated
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        err("ERROR: GitHub CLI is not authenticated")
        err("Authenticate with: gh auth login")
        return False

    return True


def trigger_build_ami_workflow(
    options: BuildOptions,
    logger: logging.Logger
) -> Optional[str]:
    """Trigger infrastructure-deploy.yml workflow in build-ami-only mode."""
    logger.info(f"Triggering build-ami-only workflow on branch '{options.branch}'...")

    # Build workflow command
    cmd = [
        "gh", "workflow", "run", "infrastructure-deploy.yml",
        "--ref", options.branch,
        "-f", "deployment_mode=build-ami-only",
        "-f", f"environment={options.environment}",
        "-f", f"version_strategy={options.version_strategy}",
    ]

    if options.version:
        cmd.extend(["-f", f"ami_version={options.version}"])

    logger.debug(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed to trigger workflow: {result.stderr}")
        return None

    logger.info("Workflow triggered, waiting for registration...")
    time.sleep(5)

    # Get latest run ID
    result = subprocess.run(
        ["gh", "run", "list", "--workflow=infrastructure-deploy.yml",
         "--limit", "1", "--json", "databaseId,status"],
        capture_output=True, text=True
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
    logger: logging.Logger
) -> Tuple[bool, str]:
    """Poll GitHub Actions workflow until completion or timeout."""
    logger.info(f"Polling workflow status (timeout: {timeout_minutes} min)...")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    # Get repo for URL
    repo_result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True
    )
    repo_name = repo_result.stdout.strip() if repo_result.returncode == 0 else "unknown/repo"
    logger.info(f"View: https://github.com/{repo_name}/actions/runs/{run_id}")

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"Timeout exceeded ({timeout_minutes} minutes)")
            return False, "timeout"

        result = subprocess.run(
            ["gh", "run", "view", run_id, "--json", "status,conclusion"],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            time.sleep(poll_interval_seconds)
            continue

        try:
            data = json.loads(result.stdout)
            status = data["status"]
            conclusion = data.get("conclusion")

            elapsed_min = int(elapsed / 60)
            logger.info(f"Status: {status}" + (f" ({conclusion})" if conclusion else f" - {elapsed_min}m"))

            if status == "completed":
                return conclusion == "success", conclusion or "unknown"

            time.sleep(poll_interval_seconds)
        except json.JSONDecodeError:
            time.sleep(poll_interval_seconds)


def get_build_details_from_workflow(
    run_id: str,
    logger: logging.Logger
) -> Dict[str, Any]:
    """Extract AMI build details from completed workflow."""
    details = {"ami_id": None, "ami_name": None, "version": None}

    logger.info("Extracting build details...")

    # Try to download packer-manifest artifact
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["gh", "run", "download", run_id, "--name", "packer-manifest", "--dir", tmpdir],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            manifest_path = Path(tmpdir) / "packer-manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        manifest = json.load(f)

                    build = manifest.get("builds", [{}])[0]
                    artifact_id = build.get("artifact_id", "")

                    if ":" in artifact_id:
                        details["ami_id"] = artifact_id.split(":")[1]
                        logger.info(f"AMI ID: {details['ami_id']}")

                    custom_data = build.get("custom_data", {})
                    details["ami_name"] = custom_data.get("ami_name") or build.get("name")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse manifest: {e}")
        else:
            logger.warning("Could not download packer-manifest artifact")

    # Fallback: parse logs for AMI ID
    if not details["ami_id"]:
        result = subprocess.run(
            ["gh", "run", "view", run_id, "--log"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            match = re.search(r'ami_id[=:]?\s*(ami-[a-f0-9]+)', result.stdout, re.IGNORECASE)
            if match:
                details["ami_id"] = match.group(1)
                logger.info(f"AMI ID (from logs): {details['ami_id']}")

    return details


def output_result(result: BuildResult, output_format: str, logger: logging.Logger) -> None:
    """Output build result in specified format."""
    if output_format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"BUILD RESULT: {'SUCCESS' if result.success else 'FAILED'}")
        logger.info("=" * 60)

        if result.ami_id:
            logger.info(f"AMI ID:       {result.ami_id}")
        if result.ami_name:
            logger.info(f"AMI Name:     {result.ami_name}")
        logger.info(f"Environment:  {result.environment}")
        if result.run_url:
            logger.info(f"Workflow URL: {result.run_url}")
        if result.duration_seconds:
            logger.info(f"Duration:     {result.duration_seconds // 60}m {result.duration_seconds % 60}s")
        if result.error_message:
            logger.info(f"Error: {result.error_message}")

        logger.info("=" * 60)

        if result.success and result.ami_id:
            logger.info("")
            logger.info("Next steps:")
            logger.info(f"  Deploy: uv run ipe/ipe_deploy.py deploy --ami-id={result.ami_id}")


def main() -> int:
    """Main entry point."""
    load_dotenv()
    options = parse_arguments()

    if not options.ipe_id:
        options.ipe_id = f"build-{int(time.time())}"

    # Setup logging
    if HAS_IPE_MODULES and setup_dual_logger:
        logger, _ = setup_dual_logger(options.ipe_id, "build-ami", "ipe_build")
        rotate_logs_if_needed()
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        logger = logging.getLogger("ipe_build")

    logger.info("=" * 60)
    logger.info("ASW IO Build - GitHub Actions AMI Builder")
    logger.info("=" * 60)
    logger.info(f"Environment:      {options.environment}")
    logger.info(f"Branch:           {options.branch}")
    logger.info(f"Version Strategy: {options.version_strategy}")
    if options.version:
        logger.info(f"Custom Version:   {options.version}")
    logger.info(f"Wait for build:   {options.wait}")
    logger.info("=" * 60)

    if not check_github_cli(logger):
        result = BuildResult(success=False, environment=options.environment,
                           error_message="GitHub CLI not available")
        output_result(result, options.output_format, logger)
        return 1

    start_time = time.time()
    run_id = trigger_build_ami_workflow(options, logger)

    if not run_id:
        result = BuildResult(success=False, environment=options.environment,
                           error_message="Failed to trigger workflow")
        output_result(result, options.output_format, logger)
        return 1

    # Get run URL
    repo_result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True
    )
    repo_name = repo_result.stdout.strip() if repo_result.returncode == 0 else "unknown"
    run_url = f"https://github.com/{repo_name}/actions/runs/{run_id}"

    if not options.wait:
        logger.info("--no-wait specified, returning immediately")
        result = BuildResult(success=True, run_id=run_id, run_url=run_url,
                           environment=options.environment)
        output_result(result, options.output_format, logger)
        return 0

    success, conclusion = poll_workflow_status(
        run_id, options.timeout, options.poll_interval, logger
    )

    duration = int(time.time() - start_time)

    if not success:
        result = BuildResult(success=False, run_id=run_id, run_url=run_url,
                           environment=options.environment,
                           error_message=f"Workflow failed: {conclusion}",
                           duration_seconds=duration)
        output_result(result, options.output_format, logger)
        return 1

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

    output_result(result, options.output_format, logger)
    return 0


def build_ami(
    environment: str = "sandbox",
    version: Optional[str] = None,
    version_strategy: str = "git-describe",
    branch: str = "main",
    wait: bool = True,
    timeout: int = 45,
    ipe_id: Optional[str] = None,
) -> BuildResult:
    """Build AMI using GitHub Actions (programmatic interface).

    For use from other scripts like adw_sdlc_zte_iso.py or asw_io_ship_iso.py.

    Example:
        from ipe.ipe_build import build_ami
        result = build_ami(environment="staging", version="v2.0.0")
        if result.success:
            # Deploy the AMI
            subprocess.run(["uv", "run", "ipe/ipe_deploy.py", "deploy",
                          f"--ami-id={result.ami_id}"])
    """
    options = BuildOptions(
        environment=environment,
        version=version,
        version_strategy=version_strategy,
        branch=branch,
        wait=wait,
        timeout=timeout,
        ipe_id=ipe_id or f"build-{int(time.time())}",
    )

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ipe_build")

    if not check_github_cli(logger):
        return BuildResult(success=False, environment=environment,
                         error_message="GitHub CLI not available")

    run_id = trigger_build_ami_workflow(options, logger)
    if not run_id:
        return BuildResult(success=False, environment=environment,
                         error_message="Failed to trigger workflow")

    if not wait:
        return BuildResult(success=True, run_id=run_id, environment=environment)

    success, conclusion = poll_workflow_status(run_id, timeout, 15, logger)
    if not success:
        return BuildResult(success=False, run_id=run_id, environment=environment,
                         error_message=f"Workflow failed: {conclusion}")

    details = get_build_details_from_workflow(run_id, logger)
    return BuildResult(
        success=True,
        ami_id=details.get("ami_id"),
        ami_name=details.get("ami_name"),
        version=details.get("version") or version,
        run_id=run_id,
        environment=environment,
    )


if __name__ == "__main__":
    sys.exit(main())
