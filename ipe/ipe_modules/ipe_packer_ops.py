"""Packer operations for AMI builds."""

import subprocess
import logging
from pathlib import Path
from typing import Optional


def init_packer(packer_dir: Path, logger: logging.Logger) -> bool:
    """Initialize Packer.

    Args:
        packer_dir: Packer directory
        logger: Logger instance

    Returns:
        True if successful
    """
    logger.info("Initializing Packer...")

    result = subprocess.run(
        ["packer", "init", "app.pkr.hcl"],
        cwd=packer_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Packer init failed: {result.stderr}")
        return False

    logger.info(result.stdout)
    return True


def validate_packer(packer_dir: Path, logger: logging.Logger) -> bool:
    """Validate Packer template.

    Args:
        packer_dir: Packer directory
        logger: Logger instance

    Returns:
        True if valid
    """
    logger.info("Validating Packer template...")

    result = subprocess.run(
        ["packer", "validate", "app.pkr.hcl"],
        cwd=packer_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Packer validation failed: {result.stderr}")
        return False

    logger.info(result.stdout)
    return True


def build_packer_ami(
    packer_dir: Path,
    logger: logging.Logger,
    ami_name: Optional[str] = None,
    version: Optional[str] = None,
    environment: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """Build Packer AMI.

    Args:
        packer_dir: Packer directory
        logger: Logger instance
        ami_name: AMI name (optional, will use default if not provided)
        version: Version string (optional)
        environment: Environment (optional)

    Returns:
        Tuple of (success, output) where output contains Packer stdout
    """
    logger.info("Building AMI (this will take 5-10 minutes)...")

    # Build command
    cmd = ["packer", "build"]

    # Add variables if provided
    if ami_name:
        cmd.extend(["-var", f"ami_name={ami_name}"])
    if version:
        cmd.extend(["-var", f"version={version}"])
    if environment:
        cmd.extend(["-var", f"environment={environment}"])

    cmd.append("app.pkr.hcl")

    # Enable Packer debug logging
    import os
    env = os.environ.copy()
    env["PACKER_LOG"] = "1"

    result = subprocess.run(
        cmd,
        cwd=packer_dir,
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode != 0:
        logger.error(f"Packer build failed: {result.stderr}")
        return False, None

    logger.info(result.stdout)
    return True, result.stdout
