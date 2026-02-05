"""AMI versioning utilities for IPE deployments."""

import subprocess
import logging
import json
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VersionStrategy(str, Enum):
    """AMI versioning strategies."""
    SEMANTIC = "semantic"
    GIT_DESCRIBE = "git-describe"
    COMMIT_HASH = "commit-hash"
    TIMESTAMP = "timestamp"
    CUSTOM = "custom"


def get_semantic_version(logger: logging.Logger) -> str:
    """Get semantic version from git tags.

    Logic:
    1. Get latest git tag matching v*.*.* pattern
    2. If no tags exist, use v0.1.0
    3. If there are commits since tag, append -dev-{short-hash}

    Examples:
    - v1.2.3 (if on tagged commit)
    - v1.2.3-dev-abc123 (if 5 commits after v1.2.3)
    - v0.1.0 (if no tags exist)

    Returns:
        Semantic version string
    """
    try:
        # Get latest tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            latest_tag = result.stdout.strip()

            # Check if we're on the tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # On exact tag
                return latest_tag
            else:
                # Commits since tag, add dev suffix
                short_hash = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True,
                    text=True
                ).stdout.strip()
                return f"{latest_tag}-dev-{short_hash}"
        else:
            # No tags, use default
            logger.warning("No git tags found, using v0.1.0")
            return "v0.1.0"

    except Exception as e:
        logger.error(f"Error getting semantic version: {e}")
        return "v0.1.0"


def get_git_describe_version(logger: logging.Logger) -> str:
    """Get version using git describe.

    Examples:
    - v1.2.3 (on tag)
    - v1.2.3-4-g1a2b3c4 (4 commits after v1.2.3)

    Returns:
        Git describe version string
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

        # Fallback to commit hash
        return get_commit_hash_version(logger)

    except Exception as e:
        logger.error(f"Error getting git describe: {e}")
        return "unknown"


def get_commit_hash_version(logger: logging.Logger) -> str:
    """Get short commit hash as version.

    Examples:
    - 1a2b3c4
    - abc123d

    Returns:
        Short commit hash
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return "unknown"

    except Exception as e:
        logger.error(f"Error getting commit hash: {e}")
        return "unknown"


def get_timestamp_version(logger: logging.Logger) -> str:
    """Get timestamp-based version.

    Examples:
    - 20250109-183045
    - 20250109-183045-abc123 (with git hash)

    Returns:
        Timestamp version string
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Optionally append git hash
    try:
        short_hash = get_commit_hash_version(logger)
        if short_hash and short_hash != "unknown":
            return f"{timestamp}-{short_hash}"
    except:
        pass

    return timestamp


def generate_version(strategy: str, logger: logging.Logger, custom_version: Optional[str] = None) -> str:
    """Generate version based on strategy.

    Args:
        strategy: Version strategy to use
        logger: Logger instance
        custom_version: Custom version string (required if strategy is CUSTOM)

    Returns:
        Version string
    """
    if strategy == VersionStrategy.CUSTOM:
        if custom_version:
            return custom_version
        else:
            logger.warning("Custom version not provided, falling back to semantic")
            return get_semantic_version(logger)
    elif strategy == VersionStrategy.SEMANTIC:
        return get_semantic_version(logger)
    elif strategy == VersionStrategy.GIT_DESCRIBE:
        return get_git_describe_version(logger)
    elif strategy == VersionStrategy.COMMIT_HASH:
        return get_commit_hash_version(logger)
    elif strategy == VersionStrategy.TIMESTAMP:
        return get_timestamp_version(logger)
    else:
        logger.warning(f"Unknown strategy: {strategy}, using semantic")
        return get_semantic_version(logger)


def generate_ami_name(
    base_name: str,
    version: str,
    environment: str,
    logger: logging.Logger
) -> str:
    """Generate AMI name with version and environment.

    Format: {base_name}-{environment}-{version}

    Examples:
    - {{PROJECT_SLUG}}-dev-v1.2.3
    - {{PROJECT_SLUG}}-staging-v1.2.3-rc1
    - {{PROJECT_SLUG}}-prod-v1.2.3

    Args:
        base_name: Base AMI name (e.g., "{{PROJECT_SLUG}}")
        version: Version string
        environment: Environment (dev/staging/prod)
        logger: Logger instance

    Returns:
        Full AMI name
    """
    # Sanitize version (remove invalid characters for AMI names)
    safe_version = re.sub(r'[^a-zA-Z0-9\-\.]', '-', version)

    ami_name = f"{base_name}-{environment}-{safe_version}"

    logger.info(f"Generated AMI name: {ami_name}")
    return ami_name


def get_git_branch(logger: logging.Logger) -> str:
    """Get current git branch name.

    Returns:
        Git branch name or 'unknown'
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return "unknown"

    except Exception as e:
        logger.error(f"Error getting git branch: {e}")
        return "unknown"


def tag_ami(
    ami_id: str,
    ami_name: str,
    version: str,
    environment: str,
    git_commit: str,
    git_branch: str,
    build_timestamp: str,
    builder: str,
    ipe_id: Optional[str],
    region: str,
    logger: logging.Logger
) -> bool:
    """Tag AMI with version and metadata.

    Tags:
    - Name: {ami_name}
    - Version: {version}
    - Environment: {environment}
    - GitCommit: {git_commit}
    - GitBranch: {git_branch}
    - BuildTimestamp: {build_timestamp}
    - Builder: {builder}
    - IPE_ID: {ipe_id}
    - ManagedBy: ipe_deploy

    Args:
        ami_id: AMI ID to tag
        ami_name: AMI name
        version: Version string
        environment: Environment name
        git_commit: Git commit hash
        git_branch: Git branch name
        build_timestamp: Build timestamp
        builder: Who built the AMI
        ipe_id: IPE workflow ID
        region: AWS region
        logger: Logger instance

    Returns:
        True if successful
    """
    try:
        tags = [
            f"Key=Name,Value={ami_name}",
            f"Key=Version,Value={version}",
            f"Key=Environment,Value={environment}",
            f"Key=GitCommit,Value={git_commit}",
            f"Key=GitBranch,Value={git_branch}",
            f"Key=BuildTimestamp,Value={build_timestamp}",
            f"Key=Builder,Value={builder}",
            f"Key=ManagedBy,Value=ipe_deploy",
        ]

        if ipe_id:
            tags.append(f"Key=IPE_ID,Value={ipe_id}")

        # Tag AMI
        cmd = [
            "aws", "ec2", "create-tags",
            "--region", region,
            "--resources", ami_id,
            "--tags"
        ] + tags

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"✅ AMI {ami_id} tagged successfully")
            return True

        logger.error(f"Failed to tag AMI: {result.stderr}")
        return False

    except Exception as e:
        logger.error(f"Error tagging AMI: {e}")
        return False


def track_ami_version(
    state: Any,  # IPEState type
    version: str,
    ami_id: str,
    ami_name: str,
    environment: str,
    git_commit: str,
    git_branch: str,
    build_timestamp: str,
    region: str,
    logger: logging.Logger
):
    """Track AMI version in IPE state.

    Stores version history in state for auditing and rollback.

    Args:
        state: IPE state instance
        version: Version string
        ami_id: AMI ID
        ami_name: AMI name
        environment: Environment
        git_commit: Git commit hash
        git_branch: Git branch
        build_timestamp: Build timestamp
        region: AWS region
        logger: Logger instance
    """
    # Get existing version history
    version_history = state.get("ami_version_history", [])

    # Add new version entry
    version_entry = {
        "version": version,
        "ami_id": ami_id,
        "ami_name": ami_name,
        "environment": environment,
        "git_commit": git_commit,
        "git_branch": git_branch,
        "build_timestamp": build_timestamp,
        "region": region,
        "created_at": datetime.now().isoformat()
    }

    version_history.append(version_entry)

    # Update state
    state.set("ami_version_history", version_history)
    state.set("latest_ami_version", version)
    state.set("latest_ami_id", ami_id)
    state.set("latest_ami_name", ami_name)

    logger.info(f"✅ Tracked AMI version: {version}")


def list_ami_versions(
    environment: Optional[str],
    region: str,
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """List available AMI versions.

    Args:
        environment: Filter by environment (optional)
        region: AWS region
        logger: Logger instance

    Returns:
        List of AMI version dictionaries
    """
    try:
        # Build filter command
        filters = [
            "Name=tag:ManagedBy,Values=ipe_deploy",
            "Name=state,Values=available"
        ]

        if environment:
            filters.append(f"Name=tag:Environment,Values={environment}")

        # Query AMIs
        cmd = [
            "aws", "ec2", "describe-images",
            "--region", region,
            "--owners", "self"
        ]

        for f in filters:
            cmd.extend(["--filters", f])

        cmd.extend([
            "--query", "Images[*].[ImageId,Name,Tags[?Key=='Version'].Value|[0],CreationDate,Tags[?Key=='GitCommit'].Value|[0]]",
            "--output", "json"
        ])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            images = json.loads(result.stdout)

            versions = []
            for img in images:
                versions.append({
                    "ami_id": img[0],
                    "ami_name": img[1],
                    "version": img[2] if img[2] else "unknown",
                    "created_at": img[3],
                    "git_commit": img[4] if len(img) > 4 and img[4] else "unknown"
                })

            # Sort by creation date (newest first)
            versions.sort(key=lambda x: x["created_at"], reverse=True)

            return versions

        logger.error(f"Failed to list AMIs: {result.stderr}")
        return []

    except Exception as e:
        logger.error(f"Error listing AMI versions: {e}")
        return []


def get_latest_ami_version(
    environment: str,
    region: str,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """Get latest AMI version for environment.

    Args:
        environment: Environment name
        region: AWS region
        logger: Logger instance

    Returns:
        Latest AMI version dictionary or None
    """
    versions = list_ami_versions(environment, region, logger)

    if versions:
        return versions[0]  # Already sorted by newest

    return None


def extract_ami_id_from_packer_output(output: str, logger: logging.Logger) -> Optional[str]:
    """Extract AMI ID from Packer build output.

    Args:
        output: Packer build stdout
        logger: Logger instance

    Returns:
        AMI ID if found, None otherwise
    """
    try:
        # Look for pattern: AMI: ami-xxxxxxxxxxxxxxxxx
        pattern = r'AMI:\s+(ami-[a-f0-9]+)'
        match = re.search(pattern, output)

        if match:
            ami_id = match.group(1)
            logger.info(f"Extracted AMI ID: {ami_id}")
            return ami_id

        # Alternative pattern in manifest
        pattern = r'"artifact_id":\s*"[^:]+:(ami-[a-f0-9]+)"'
        match = re.search(pattern, output)

        if match:
            ami_id = match.group(1)
            logger.info(f"Extracted AMI ID from manifest: {ami_id}")
            return ami_id

        logger.warning("Could not extract AMI ID from Packer output")
        return None

    except Exception as e:
        logger.error(f"Error extracting AMI ID: {e}")
        return None
