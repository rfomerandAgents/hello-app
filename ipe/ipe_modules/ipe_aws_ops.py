"""AWS CLI operations for infrastructure management."""

import subprocess
import logging
import os
import re
from typing import Optional, Dict, Any

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def verify_ami_exists(ami_id: str, region: str, logger: logging.Logger) -> bool:
    """Verify that an AMI exists in AWS.

    Args:
        ami_id: AMI ID to verify (e.g., ami-0a2feb13eee5e403c)
        region: AWS region
        logger: Logger instance

    Returns:
        True if AMI exists, False otherwise
    """
    # Check if boto3 is available
    if not BOTO3_AVAILABLE:
        logger.error("boto3 is not installed. Install with: pip install boto3")
        return False

    # Validate AMI ID format
    ami_pattern = r'^ami-[0-9a-f]{17}$'
    if not re.match(ami_pattern, ami_id):
        logger.error(f"Invalid AMI ID format: {ami_id}")
        logger.error("Expected format: ami-xxxxxxxxxxxxxxxxx (17 hex characters)")
        return False

    try:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_images(ImageIds=[ami_id])

        if not response['Images']:
            logger.error(f"AMI not found: {ami_id}")
            return False

        ami = response['Images'][0]
        logger.info(f"✓ AMI verified: {ami_id}")
        logger.info(f"  Name: {ami.get('Name', 'N/A')}")
        logger.info(f"  State: {ami.get('State', 'N/A')}")
        logger.info(f"  Created: {ami.get('CreationDate', 'N/A')}")

        return True

    except ClientError as e:
        logger.error(f"Failed to verify AMI: {e}")
        return False


def verify_aws_credentials(logger: logging.Logger) -> bool:
    """Verify AWS credentials are configured.

    Args:
        logger: Logger instance

    Returns:
        True if credentials are configured
    """
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        logger.error("AWS_ACCESS_KEY_ID not set")
        return False

    if not os.getenv("AWS_SECRET_ACCESS_KEY"):
        logger.error("AWS_SECRET_ACCESS_KEY not set")
        return False

    logger.info("AWS credentials verified")
    return True


def get_ec2_instance_status(
    instance_id: str,
    region: str,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """Get EC2 instance status.

    Args:
        instance_id: EC2 instance ID
        region: AWS region
        logger: Logger instance

    Returns:
        Instance status dictionary or None
    """
    result = subprocess.run(
        [
            "aws", "ec2", "describe-instances",
            "--region", region,
            "--instance-ids", instance_id,
            "--query", "Reservations[0].Instances[0].[State.Name,InstanceType,PublicIpAddress]",
            "--output", "json"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Failed to query instance: {result.stderr}")
        return None

    import json
    data = json.loads(result.stdout)

    return {
        "state": data[0],
        "instance_type": data[1],
        "public_ip": data[2]
    }


def test_website_accessibility(url: str, logger: logging.Logger) -> bool:
    """Test if website is accessible.

    Args:
        url: Website URL
        logger: Logger instance

    Returns:
        True if accessible (HTTP 200)
    """
    result = subprocess.run(
        ["curl", "-I", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
        capture_output=True,
        text=True
    )

    status_code = result.stdout.strip()
    return status_code == "200"


def check_ami_in_use(ami_id: str, region: str, logger: logging.Logger) -> tuple[bool, list[str]]:
    """Check if AMI is currently in use by any EC2 instances.

    Args:
        ami_id: AMI ID to check
        region: AWS region
        logger: Logger instance

    Returns:
        Tuple of (is_in_use, list_of_instance_ids)
    """
    if not BOTO3_AVAILABLE:
        logger.error("boto3 is not installed. Install with: pip install boto3")
        return False, []

    try:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'image-id', 'Values': [ami_id]},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending', 'stopping']}
            ]
        )

        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
                state = instance['State']['Name']
                logger.debug(f"  - {instance['InstanceId']} ({state})")

        if instance_ids:
            return True, instance_ids
        return False, []

    except ClientError as e:
        logger.error(f"Failed to check AMI usage: {e}")
        return False, []


def delete_ami_and_snapshots(ami_id: str, region: str, logger: logging.Logger, dry_run: bool = False) -> bool:
    """Delete AMI and its associated EBS snapshots.

    Args:
        ami_id: AMI ID to delete
        region: AWS region
        logger: Logger instance
        dry_run: If True, only show what would be deleted

    Returns:
        True if successful, False otherwise
    """
    if not BOTO3_AVAILABLE:
        logger.error("boto3 is not installed. Install with: pip install boto3")
        return False

    try:
        ec2 = boto3.client('ec2', region_name=region)

        # Get AMI details to find associated snapshots
        response = ec2.describe_images(ImageIds=[ami_id])
        if not response['Images']:
            logger.error(f"AMI not found: {ami_id}")
            return False

        ami = response['Images'][0]
        snapshot_ids = []

        # Extract snapshot IDs from block device mappings
        for mapping in ami.get('BlockDeviceMappings', []):
            if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                snapshot_ids.append(mapping['Ebs']['SnapshotId'])

        if dry_run:
            logger.info(f"[DRY RUN] Would deregister AMI: {ami_id}")
            logger.info(f"[DRY RUN] Would delete {len(snapshot_ids)} snapshot(s): {', '.join(snapshot_ids)}")
            return True

        # Deregister the AMI
        logger.info(f"Deregistering AMI {ami_id}...")
        ec2.deregister_image(ImageId=ami_id)
        logger.info("✅ AMI deregistered successfully")

        # Delete associated snapshots
        if snapshot_ids:
            logger.info(f"Deleting {len(snapshot_ids)} associated snapshot(s)...")
            for snapshot_id in snapshot_ids:
                try:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    logger.info(f"✅ Snapshot {snapshot_id} deleted")
                except ClientError as e:
                    logger.warning(f"Failed to delete snapshot {snapshot_id}: {e}")
        else:
            logger.info("No snapshots to delete")

        return True

    except ClientError as e:
        logger.error(f"Failed to delete AMI: {e}")
        return False


def list_amis_by_environment(environment: str, region: str, logger: logging.Logger) -> list[Dict[str, Any]]:
    """List all AMIs for a specific environment.

    Args:
        environment: Environment name (dev/staging/prod)
        region: AWS region
        logger: Logger instance

    Returns:
        List of AMI dictionaries sorted by creation date (newest first)
    """
    if not BOTO3_AVAILABLE:
        logger.error("boto3 is not installed. Install with: pip install boto3")
        return []

    try:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': 'name', 'Values': [f'{{{{PROJECT_SLUG}}}}-{environment}-*']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )

        # Sort by creation date (newest first)
        amis = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)

        return amis

    except ClientError as e:
        logger.error(f"Failed to list AMIs: {e}")
        return []
