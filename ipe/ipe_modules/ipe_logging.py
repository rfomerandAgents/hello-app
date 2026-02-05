"""Enhanced logging module for IPE deployment operations.

This module provides centralized logging capabilities for ipe_deploy.py,
capturing full command output and automatically saving detailed failure logs.
"""

import logging
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import re


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to project root
    """
    # __file__ is in ipe/ipe_modules/, so go up 2 levels
    return Path(__file__).parent.parent.parent


def ensure_ipe_logs_directory() -> Path:
    """Ensure ipe_logs directory structure exists.

    Returns:
        Path to ipe_logs directory
    """
    project_root = get_project_root()
    ipe_logs = project_root / "ipe_logs"

    # Create subdirectories
    subdirs = ["deploy", "build-ami", "destroy", "full-deploy", "failures",
               "status", "list-versions"]

    for subdir in subdirs:
        (ipe_logs / subdir).mkdir(parents=True, exist_ok=True)

    return ipe_logs


def get_log_file_path(
    command: str,
    ipe_id: str,
    failed: bool = False
) -> Tuple[Path, Path]:
    """Generate log file paths for a deployment operation.

    Args:
        command: Command being executed (deploy, build-ami, etc.)
        ipe_id: IPE workflow ID
        failed: Whether this is a failure log

    Returns:
        Tuple of (command_log_path, failure_log_path)
        If failed=False, failure_log_path is None
    """
    ipe_logs = ensure_ipe_logs_directory()

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Normalize command name for directory
    command_dir = command.replace("_", "-")

    # Build filename
    suffix = "_FAILED" if failed else ""
    filename = f"{timestamp}_{ipe_id}{suffix}.log"

    command_log = ipe_logs / command_dir / filename

    if failed:
        failure_log = ipe_logs / "failures" / f"{timestamp}_{command_dir}{suffix}.log"
        return command_log, failure_log

    return command_log, None


def sanitize_command_for_logging(command: str) -> str:
    """Sanitize command strings to redact sensitive information.

    Args:
        command: Command string to sanitize

    Returns:
        Sanitized command with secrets redacted
    """
    # Patterns to redact
    patterns = [
        (r'(AWS_SECRET_ACCESS_KEY=)[^\s]+', r'\1***REDACTED***'),
        (r'(AWS_ACCESS_KEY_ID=)[^\s]+', r'\1***REDACTED***'),
        (r'(ANTHROPIC_API_KEY=)[^\s]+', r'\1***REDACTED***'),
        (r'(GITHUB_PAT=)[^\s]+', r'\1***REDACTED***'),
        (r'(GH_TOKEN=)[^\s]+', r'\1***REDACTED***'),
        (r'(sk-ant-[^\s]+)', r'***REDACTED***'),
        (r'(ghp_[^\s]+)', r'***REDACTED***'),
        (r'(-var\s+["\']?ssh_public_key=[^\s"\']+)', r'-var ssh_public_key=***REDACTED***'),
    ]

    sanitized = command
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def setup_dual_logger(
    ipe_id: str,
    command: str,
    trigger_type: str = "ipe_deploy"
) -> Tuple[logging.Logger, Path]:
    """Set up dual logging to both agents/ and ipe_logs/ directories.

    Args:
        ipe_id: IPE workflow ID
        command: Command being executed
        trigger_type: Type of trigger

    Returns:
        Tuple of (logger, ipe_logs_file_path)
    """
    project_root = get_project_root()

    # Create agents log directory (existing behavior)
    agents_log_dir = project_root / "agents" / ipe_id / trigger_type
    agents_log_dir.mkdir(parents=True, exist_ok=True)
    agents_log_file = agents_log_dir / "execution.log"

    # Create ipe_logs file path
    ipe_logs_file, _ = get_log_file_path(command, ipe_id, failed=False)

    # Create logger with unique name
    logger = logging.getLogger(f"ipe_{ipe_id}")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler for agents/ directory
    agents_handler = logging.FileHandler(agents_log_file, mode='a')
    agents_handler.setLevel(logging.DEBUG)

    # File handler for ipe_logs/ directory
    ipe_logs_handler = logging.FileHandler(ipe_logs_file, mode='a')
    ipe_logs_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter('%(message)s')

    agents_handler.setFormatter(file_formatter)
    ipe_logs_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(agents_handler)
    logger.addHandler(ipe_logs_handler)
    logger.addHandler(console_handler)

    # Log initialization
    logger.info(f"IPE Logger initialized - ID: {ipe_id}")
    logger.debug(f"Agents log: {agents_log_file}")
    logger.debug(f"IPE log: {ipe_logs_file}")

    return logger, ipe_logs_file


def write_failure_log(
    command: str,
    ipe_id: str,
    error_message: str,
    full_output: str,
    context: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[Path, Path]:
    """Write detailed failure log when a deployment step fails.

    Args:
        command: Command that failed
        ipe_id: IPE workflow ID
        error_message: Brief error message
        full_output: Full command output (stdout + stderr)
        context: Additional context (environment, args, etc.)
        logger: Logger instance for logging

    Returns:
        Tuple of (command_log_path, failure_log_path)
    """
    # Get log paths
    command_log, failure_log = get_log_file_path(command, ipe_id, failed=True)

    # Build failure report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "=" * 80,
        f"IPE DEPLOYMENT FAILURE REPORT",
        "=" * 80,
        f"Timestamp: {timestamp}",
        f"Command: {command}",
        f"IPE ID: {ipe_id}",
        "",
        "-" * 80,
        "ERROR MESSAGE",
        "-" * 80,
        error_message,
        "",
        "-" * 80,
        "FULL OUTPUT",
        "-" * 80,
        full_output,
        "",
    ]

    # Add context if provided
    if context:
        report_lines.extend([
            "-" * 80,
            "EXECUTION CONTEXT",
            "-" * 80,
        ])
        for key, value in context.items():
            # Sanitize sensitive values
            if key in ["ssh_public_key", "AWS_SECRET_ACCESS_KEY", "ANTHROPIC_API_KEY"]:
                value = "***REDACTED***"
            report_lines.append(f"{key}: {value}")
        report_lines.append("")

    report_lines.extend([
        "=" * 80,
        "END OF FAILURE REPORT",
        "=" * 80,
    ])

    report = "\n".join(report_lines)

    # Write to command-specific log
    command_log.write_text(report)

    # Copy to failures directory
    failure_log.write_text(report)

    if logger:
        logger.debug(f"Failure log written to: {command_log}")
        logger.debug(f"Failure log copied to: {failure_log}")

    return command_log, failure_log


def rotate_logs_if_needed(max_size_mb: int = 100, max_age_days: int = 30) -> None:
    """Rotate logs if they exceed size or age limits.

    Args:
        max_size_mb: Maximum total size in MB
        max_age_days: Maximum age in days
    """
    ipe_logs = get_project_root() / "ipe_logs"

    if not ipe_logs.exists():
        return

    # Calculate total size
    total_size = 0
    for log_file in ipe_logs.rglob("*.log"):
        total_size += log_file.stat().st_size

    total_size_mb = total_size / (1024 * 1024)

    # Check if rotation needed
    if total_size_mb > max_size_mb:
        # Archive oldest logs
        archive_name = f"ipe_logs_archive_{datetime.now().strftime('%Y-%m')}.tar.gz"
        archive_path = get_project_root() / archive_name

        # Create archive (simple implementation - compress entire directory)
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'gztar',
            str(ipe_logs.parent),
            'ipe_logs'
        )

        # Clean old logs (keep last 100 files)
        all_logs = sorted(ipe_logs.rglob("*.log"), key=lambda p: p.stat().st_mtime)
        if len(all_logs) > 100:
            for old_log in all_logs[:-100]:
                old_log.unlink()


def display_failure_message(
    step_name: str,
    error_message: str,
    command_log: Path,
    failure_log: Path,
    logger: logging.Logger
) -> None:
    """Display user-friendly error message with log locations.

    Args:
        step_name: Name of the step that failed
        error_message: Brief error message
        command_log: Path to command-specific log
        failure_log: Path to failure log in failures directory
        logger: Logger instance
    """
    logger.error("")
    logger.error("=" * 60)
    logger.error(f"❌ {step_name} failed")
    logger.error("=" * 60)
    logger.error("")
    logger.error(f"Error: {error_message}")
    logger.error("")
    logger.error("Full error details saved to:")
    logger.error(f"  • {command_log}")
    logger.error(f"  • {failure_log}")
    logger.error("")
    logger.error("To view the full error log:")
    logger.error(f"  cat {failure_log}")
    logger.error("")
    logger.error("=" * 60)
