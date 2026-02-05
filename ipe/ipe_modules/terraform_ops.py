"""Terraform-specific operations for IPE workflows.

This module provides all Terraform operations needed for infrastructure workflows:
- Initialization and validation
- Planning and applying
- Security scanning
- Cost estimation
- Linting and formatting
"""

import subprocess
import json
import os
import shutil
from typing import Tuple, Optional, Dict, Any
import logging
from datetime import datetime
from pathlib import Path


def check_terraform_installed() -> bool:
    """Check if Terraform is installed."""
    return shutil.which("terraform") is not None


def create_tfvars_override(
    terraform_dir: Path,
    ami_id: str,
    logger: logging.Logger
) -> Optional[Path]:
    """Create a temporary tfvars file with custom AMI ID.

    Args:
        terraform_dir: Path to terraform directory
        ami_id: AMI ID to deploy
        logger: Logger instance

    Returns:
        Path to temporary tfvars file, or None on failure
    """
    try:
        # Create override tfvars file
        override_file = terraform_dir / "override.auto.tfvars"

        with open(override_file, 'w') as f:
            f.write(f'# Auto-generated override for custom AMI deployment\n')
            f.write(f'# Generated: {datetime.now().isoformat()}\n')
            f.write(f'ami_id = "{ami_id}"\n')

        logger.info(f"Created tfvars override: {override_file}")
        return override_file

    except Exception as e:
        logger.error(f"Failed to create tfvars override: {e}")
        return None


def run_terraform_init(
    cwd: str,
    logger: logging.Logger,
    workspace: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Initialize Terraform in the working directory.

    Args:
        cwd: Working directory path
        logger: Logger instance
        workspace: TFC workspace name (e.g., "{{PROJECT_SLUG}}-dev")

    Returns:
        Tuple of (success, error_message)
    """
    try:
        env = os.environ.copy()
        if workspace:
            env["TF_WORKSPACE"] = workspace
            logger.info(f"Using TFC workspace: {workspace}")

        logger.info("Running terraform init...")
        result = subprocess.run(
            ["terraform", "init", "-input=false"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )
        if result.returncode == 0:
            logger.info("✅ Terraform init successful")
            return True, None
        logger.error(f"Terraform init failed: {result.stderr}")
        return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Terraform init timed out after 5 minutes"
    except Exception as e:
        return False, str(e)


def run_terraform_validate(
    cwd: str,
    logger: logging.Logger,
    workspace: Optional[str] = None
) -> Dict[str, Any]:
    """Validate Terraform configuration.

    Args:
        cwd: Working directory path
        logger: Logger instance
        workspace: TFC workspace name (e.g., "{{PROJECT_SLUG}}-dev")

    Returns:
        Test result dictionary
    """
    try:
        env = os.environ.copy()
        if workspace:
            env["TF_WORKSPACE"] = workspace

        logger.info("Running terraform validate...")
        result = subprocess.run(
            ["terraform", "validate", "-json"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )

        # Parse JSON output
        output = json.loads(result.stdout) if result.stdout else {}

        passed = result.returncode == 0 and output.get("valid", False)
        error_msg = None

        if not passed:
            if "diagnostics" in output:
                errors = [d.get("summary", "") for d in output["diagnostics"] if d.get("severity") == "error"]
                error_msg = "\n".join(errors) if errors else result.stderr
            else:
                error_msg = result.stderr

        return {
            "test_name": "terraform_validate",
            "passed": passed,
            "execution_command": "terraform validate",
            "test_purpose": "Validate Terraform configuration syntax",
            "error": error_msg
        }
    except Exception as e:
        return {
            "test_name": "terraform_validate",
            "passed": False,
            "execution_command": "terraform validate",
            "test_purpose": "Validate Terraform configuration syntax",
            "error": str(e)
        }


def run_terraform_fmt(cwd: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """Format Terraform files (auto-fix formatting issues).

    Args:
        cwd: Working directory path
        logger: Logger instance

    Returns:
        Tuple of (success, output_message)
    """
    try:
        logger.info("Running terraform fmt...")
        result = subprocess.run(
            ["terraform", "fmt", "-recursive"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # terraform fmt returns 0 on success, even if it formatted files
        if result.returncode == 0:
            formatted_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            if formatted_files and formatted_files[0]:
                logger.info(f"✅ Formatted {len(formatted_files)} file(s)")
                return True, f"Formatted: {', '.join(formatted_files)}"
            else:
                logger.info("✅ All files already formatted correctly")
                return True, "All files already formatted"

        logger.warning(f"Terraform fmt reported issues: {result.stderr}")
        return False, result.stderr

    except Exception as e:
        logger.error(f"Error running terraform fmt: {e}")
        return False, str(e)


def run_terraform_fmt_check(cwd: str, logger: logging.Logger) -> Dict[str, Any]:
    """Check Terraform formatting.

    Args:
        cwd: Working directory path
        logger: Logger instance

    Returns:
        Test result dictionary
    """
    try:
        logger.info("Running terraform fmt check...")
        result = subprocess.run(
            ["terraform", "fmt", "-check", "-recursive"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )

        passed = result.returncode == 0
        error_msg = None

        if not passed:
            # List files that need formatting
            files = result.stdout.strip().split('\n') if result.stdout else []
            error_msg = f"Files need formatting: {', '.join(files)}" if files else "Formatting issues found"

        return {
            "test_name": "terraform_fmt",
            "passed": passed,
            "execution_command": "terraform fmt -check -recursive",
            "test_purpose": "Check Terraform code formatting",
            "error": error_msg
        }
    except Exception as e:
        return {
            "test_name": "terraform_fmt",
            "passed": False,
            "execution_command": "terraform fmt -check -recursive",
            "test_purpose": "Check Terraform code formatting",
            "error": str(e)
        }


def run_terraform_plan(
    cwd: str,
    logger: logging.Logger,
    out_file: str = "tfplan",
    workspace: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Generate Terraform plan.

    Args:
        cwd: Working directory path
        logger: Logger instance
        out_file: Output file for plan
        workspace: TFC workspace name (e.g., "{{PROJECT_SLUG}}-dev")

    Returns:
        Tuple of (success, plan_output, error_message)
    """
    try:
        env = os.environ.copy()
        if workspace:
            env["TF_WORKSPACE"] = workspace

        logger.info("Generating Terraform plan...")
        result = subprocess.run(
            ["terraform", "plan", f"-out={out_file}", "-input=false"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )

        if result.returncode == 0:
            logger.info("✅ Terraform plan generated successfully")
            return True, result.stdout, None

        logger.error(f"Terraform plan failed: {result.stderr}")
        return False, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, None, "Terraform plan timed out after 5 minutes"
    except Exception as e:
        return False, None, str(e)


def run_terraform_plan_json(
    cwd: str,
    logger: logging.Logger,
    plan_file: str = "tfplan"
) -> Optional[Dict[str, Any]]:
    """Get Terraform plan in JSON format.

    Args:
        cwd: Working directory path
        logger: Logger instance
        plan_file: Plan file to read

    Returns:
        Plan JSON or None if failed
    """
    try:
        logger.info("Getting Terraform plan in JSON format...")
        result = subprocess.run(
            ["terraform", "show", "-json", plan_file],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return json.loads(result.stdout)

        logger.error(f"Failed to get plan JSON: {result.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error getting plan JSON: {e}")
        return None


def run_tflint(cwd: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Run tflint validation.

    Args:
        cwd: Working directory path
        logger: Logger instance

    Returns:
        Test result dictionary or None if tflint not available
    """
    if not shutil.which("tflint"):
        logger.info("tflint not installed, skipping")
        return None

    try:
        logger.info("Running tflint...")

        # Initialize tflint
        init_result = subprocess.run(
            ["tflint", "--init"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Run tflint
        result = subprocess.run(
            ["tflint", "--format=json"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Parse output
        issues = json.loads(result.stdout) if result.stdout else {}

        # tflint returns 0 for no issues, 2 for issues found
        passed = result.returncode == 0
        error_msg = None

        if not passed and issues:
            # Extract issues
            all_issues = []
            for issue in issues.get("issues", []):
                all_issues.append(f"{issue.get('rule', {}).get('name', 'unknown')}: {issue.get('message', '')}")
            error_msg = "\n".join(all_issues) if all_issues else "Linting issues found"

        return {
            "test_name": "tflint",
            "passed": passed,
            "execution_command": "tflint --format=json",
            "test_purpose": "Lint Terraform code for best practices",
            "error": error_msg
        }
    except Exception as e:
        return {
            "test_name": "tflint",
            "passed": False,
            "execution_command": "tflint --format=json",
            "test_purpose": "Lint Terraform code for best practices",
            "error": str(e)
        }


def run_checkov(cwd: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Run Checkov security scan.

    Args:
        cwd: Working directory path
        logger: Logger instance

    Returns:
        Test result dictionary or None if checkov not available
    """
    if not shutil.which("checkov"):
        logger.info("checkov not installed, skipping")
        return None

    try:
        logger.info("Running Checkov security scan...")
        result = subprocess.run(
            ["checkov", "-d", ".", "--output", "json", "--quiet"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=180
        )

        # Parse output
        output = json.loads(result.stdout) if result.stdout else {}

        # Check results
        summary = output.get("summary", {})
        failed = summary.get("failed", 0)
        passed = failed == 0

        error_msg = None
        if not passed:
            error_msg = f"Found {failed} security issues"

        return {
            "test_name": "checkov",
            "passed": passed,
            "execution_command": "checkov -d . --output json",
            "test_purpose": "Security and compliance scanning",
            "error": error_msg
        }
    except Exception as e:
        return {
            "test_name": "checkov",
            "passed": False,
            "execution_command": "checkov -d . --output json",
            "test_purpose": "Security and compliance scanning",
            "error": str(e)
        }


def run_tfsec(cwd: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Run tfsec security scan.

    Args:
        cwd: Working directory path
        logger: Logger instance

    Returns:
        Test result dictionary or None if tfsec not available
    """
    if not shutil.which("tfsec"):
        logger.info("tfsec not installed, skipping")
        return None

    try:
        logger.info("Running tfsec security scan...")
        result = subprocess.run(
            ["tfsec", ".", "--format", "json"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Parse output
        output = json.loads(result.stdout) if result.stdout else {}

        # Check results
        results = output.get("results", [])
        passed = len(results) == 0

        error_msg = None
        if not passed:
            error_msg = f"Found {len(results)} security issues"

        return {
            "test_name": "tfsec",
            "passed": passed,
            "execution_command": "tfsec . --format json",
            "test_purpose": "Security scanning for Terraform",
            "error": error_msg
        }
    except Exception as e:
        return {
            "test_name": "tfsec",
            "passed": False,
            "execution_command": "tfsec . --format json",
            "test_purpose": "Security scanning for Terraform",
            "error": str(e)
        }


def setup_terraform_workspace(
    cwd: str,
    workspace_name: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Create or select Terraform workspace (LOCAL workspaces only).

    NOTE: This function is for local Terraform workspaces, not Terraform Cloud.
    For TFC workspace selection, use TF_WORKSPACE environment variable instead.
    This function should only be used for local development or non-TFC backends.

    Args:
        cwd: Working directory path
        workspace_name: Workspace name
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Check if workspace exists
        result = subprocess.run(
            ["terraform", "workspace", "list"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if workspace_name in result.stdout:
            # Select existing workspace
            logger.info(f"Selecting existing workspace: {workspace_name}")
            result = subprocess.run(
                ["terraform", "workspace", "select", workspace_name],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
        else:
            # Create new workspace
            logger.info(f"Creating new workspace: {workspace_name}")
            result = subprocess.run(
                ["terraform", "workspace", "new", workspace_name],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )

        if result.returncode == 0:
            logger.info(f"✅ Workspace {workspace_name} ready")
            return True, None

        return False, result.stderr
    except Exception as e:
        return False, str(e)


def estimate_cost(cwd: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Run Infracost cost estimation if available.

    Args:
        cwd: Working directory path
        logger: Logger instance

    Returns:
        Cost estimate dictionary or None if not available
    """
    if not shutil.which("infracost"):
        logger.info("infracost not installed, skipping cost estimation")
        return None

    try:
        logger.info("Running Infracost cost estimation...")
        result = subprocess.run(
            ["infracost", "breakdown", "--path", ".", "--format", "json"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode == 0:
            cost_data = json.loads(result.stdout)
            logger.info("✅ Cost estimation complete")
            return cost_data

        logger.warning(f"Infracost failed: {result.stderr}")
        return None
    except Exception as e:
        logger.warning(f"Infracost error: {e}")
        return None


def apply_terraform_changes(
    cwd: str,
    logger: logging.Logger,
    auto_approve: bool = False
) -> Tuple[bool, Optional[str]]:
    """Apply Terraform changes - USE WITH EXTREME CAUTION.

    Args:
        cwd: Working directory path
        logger: Logger instance
        auto_approve: Whether to auto-approve (DANGEROUS!)

    Returns:
        Tuple of (success, error_message)
    """
    logger.warning("⚠️ APPLYING TERRAFORM CHANGES - THIS WILL MODIFY INFRASTRUCTURE!")

    try:
        # Build command
        cmd = ["terraform", "apply"]
        if auto_approve:
            cmd.append("-auto-approve")
        cmd.extend(["-input=false"])

        # Apply
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Terraform apply completed successfully")
            return True, None

        logger.error(f"Terraform apply failed: {result.stderr}")
        return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Terraform apply timed out after 30 minutes"
    except Exception as e:
        return False, str(e)


# Helper functions for ipe_deploy.py compatibility
from pathlib import Path


def init_terraform(
    terraform_dir: Path,
    logger: logging.Logger,
    workspace: Optional[str] = None
) -> bool:
    """Initialize Terraform (wrapper for ipe_deploy compatibility).

    Args:
        terraform_dir: Terraform directory path
        logger: Logger instance
        workspace: TFC workspace name (e.g., "{{PROJECT_SLUG}}-dev")

    Returns:
        True if successful
    """
    success, error = run_terraform_init(str(terraform_dir), logger, workspace)
    return success


def validate_terraform(
    terraform_dir: Path,
    logger: logging.Logger,
    workspace: Optional[str] = None
) -> bool:
    """Validate Terraform configuration (wrapper for ipe_deploy compatibility).

    Args:
        terraform_dir: Terraform directory path
        logger: Logger instance
        workspace: TFC workspace name (e.g., "{{PROJECT_SLUG}}-dev")

    Returns:
        True if valid
    """
    result = run_terraform_validate(str(terraform_dir), logger, workspace)
    return result.get("passed", False)


def plan_terraform(
    terraform_dir: Path,
    plan_file: str,
    logger: logging.Logger,
    workspace: Optional[str] = None
) -> bool:
    """Generate Terraform plan (wrapper for ipe_deploy compatibility).

    Args:
        terraform_dir: Terraform directory path
        plan_file: Output plan file path
        logger: Logger instance
        workspace: TFC workspace name (e.g., "{{PROJECT_SLUG}}-dev")

    Returns:
        True if successful
    """
    success, output, error = run_terraform_plan(
        str(terraform_dir), logger, os.path.basename(plan_file), workspace
    )
    return success


def apply_terraform(terraform_dir: Path, plan_file: str, logger: logging.Logger) -> bool:
    """Apply Terraform plan (wrapper for ipe_deploy compatibility).

    Args:
        terraform_dir: Terraform directory path
        plan_file: Plan file to apply
        logger: Logger instance

    Returns:
        True if successful
    """
    try:
        logger.info("Applying Terraform plan...")
        result = subprocess.run(
            ["terraform", "apply", "-input=false", os.path.basename(plan_file)],
            cwd=str(terraform_dir),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Terraform apply completed successfully")
            return True

        logger.error(f"Terraform apply failed: {result.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Terraform apply timed out after 30 minutes")
        return False
    except Exception as e:
        logger.error(f"Terraform apply error: {e}")
        return False


def destroy_terraform(terraform_dir: Path, logger: logging.Logger, auto_approve: bool = False) -> bool:
    """Destroy Terraform infrastructure (wrapper for ipe_deploy compatibility).

    Args:
        terraform_dir: Terraform directory path
        logger: Logger instance
        auto_approve: Whether to auto-approve

    Returns:
        True if successful
    """
    try:
        logger.warning("⚠️ DESTROYING TERRAFORM INFRASTRUCTURE!")

        # Build command
        cmd = ["terraform", "destroy"]
        if auto_approve:
            cmd.append("-auto-approve")
        cmd.extend(["-input=false"])

        # Destroy
        result = subprocess.run(
            cmd,
            cwd=str(terraform_dir),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Terraform destroy completed successfully")
            return True

        logger.error(f"Terraform destroy failed: {result.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Terraform destroy timed out after 30 minutes")
        return False
    except Exception as e:
        logger.error(f"Terraform destroy error: {e}")
        return False


def get_terraform_outputs(terraform_dir: Path, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Get Terraform outputs (wrapper for ipe_deploy compatibility).

    Args:
        terraform_dir: Terraform directory path
        logger: Logger instance

    Returns:
        Dictionary of outputs or None
    """
    try:
        logger.info("Getting Terraform outputs...")
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=str(terraform_dir),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            outputs_raw = json.loads(result.stdout)
            # Extract values from output format
            outputs = {}
            for key, value in outputs_raw.items():
                outputs[key] = value.get("value")
            return outputs

        logger.warning(f"Failed to get outputs: {result.stderr}")
        return None
    except Exception as e:
        logger.warning(f"Error getting outputs: {e}")
        return None
