#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv", "claude-agent-sdk", "pydantic"]
# ///

"""
Unified Webhook Router - ADW and IPE

Routes GitHub webhook events to the appropriate workflow system:
- ADW (Application Development Workflow) for application code
- IPE (Infrastructure Platform Engineering) for Terraform infrastructure

Usage: uv run trigger_webhook.py

Environment Requirements:
- PORT: Server port (default: 8000)
- GITHUB_PAT: GitHub Personal Access Token
- CLAUDE_CODE_OAUTH_TOKEN: Claude API key
"""

import os
import subprocess
import sys
from typing import Optional, Literal
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn

# Add both adws and ipe to path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "adws"))
sys.path.insert(0, os.path.join(repo_root, "ipe"))

# Import from ADW system
from adw_modules.utils import make_adw_id, setup_logger as adw_setup_logger, get_safe_subprocess_env
from adw_modules.github import make_issue_comment as adw_make_issue_comment, ADW_BOT_IDENTIFIER
from adw_modules.workflow_ops import extract_adw_info, AVAILABLE_ADW_WORKFLOWS
from adw_modules.state import ADWState

# Import from IPE system (legacy)
from ipe_modules.ipe_utils import make_ipe_id, setup_logger as ipe_setup_logger
from ipe_modules.ipe_github import make_issue_comment as ipe_make_issue_comment
from ipe_modules.ipe_state import IPEState

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", "8000"))

# Bot identifiers to prevent loops
BOT_IDENTIFIERS = [
    ADW_BOT_IDENTIFIER,  # "[ADW-AGENTS]"
    "[IPE-AGENTS]",
    "🤖 IPE",
    "🤖 ADW",
]

# Error patterns that indicate failure/error messages (shouldn't trigger workflows)
ERROR_PATTERNS = [
    "failed",
    "error:",
    "traceback",
    "exception:",
    "❌",
    "crashed",
    "isolated plan phase failed",
    "isolated build phase failed",
    "isolated test phase failed",
    "isolated review phase failed",
    "isolated ship phase failed",
]

# Track recent failures to prevent loops
RECENT_FAILURES = {}
FAILURE_COOLDOWN_SECONDS = 300  # 5 minutes

# IMPORTANT: Workflow lists MUST be ordered by specificity (longest/most-specific first).
# This prevents substring matching bugs where shorter workflow names match before longer ones.

# ADW Workflows - ORDERED BY SPECIFICITY (longest/most-specific first)
# All names are lowercase for case-insensitive matching
AVAILABLE_ADW_WORKFLOWS_LOCAL = [
    "adw_sdlc_zte_iso",  # ZTE (Zero Touch Execution) must come before adw_sdlc_iso
    "adw_sdlc_iso",
    "adw_document_iso",
    "adw_review_iso",
    "adw_build_iso",
    "adw_test_iso",
    "adw_plan_iso",
    "adw_ship_iso",
    "adw_patch_iso",
]

# Mapping from detection names (lowercase) to actual script filenames
# Only needed for workflows where script filename differs from detection name
ADW_WORKFLOW_TO_SCRIPT = {}

ADW_DEPENDENT_WORKFLOWS = [
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
]

# IPE Workflows - ORDERED BY SPECIFICITY (longest/most-specific first)
AVAILABLE_IPE_WORKFLOWS = [
    "ipe_sdlc_iso",       # Full SDLC first (in case future variants exist)
    "ipe_document_iso",
    "ipe_build_ami_iso",  # AMI build in worktree (NEW)
    "ipe_review_iso",
    "ipe_build_iso",
    "ipe_test_iso",
    "ipe_plan_iso",
    "ipe_ship_iso",
    "ipe_patch_iso",
    "ipe_destroy",        # DESTRUCTIVE - Note: NOT "_iso" suffix
    "ipe_deploy",         # Infrastructure deployment
]

# Destructive workflows that require explicit confirmation
IPE_DESTRUCTIVE_WORKFLOWS = [
    "ipe_destroy",
]

IPE_DEPENDENT_WORKFLOWS = [
    "ipe_build_ami_iso",  # Requires IPE ID (NEW)
    "ipe_build_iso",
    "ipe_test_iso",
    "ipe_review_iso",
    "ipe_document_iso",
    "ipe_ship_iso",
]

# Type definitions
WorkflowType = Literal["adw", "ipe"]

# Create FastAPI app
app = FastAPI(
    title="Unified Webhook Router",
    description="Routes GitHub webhooks to ADW or IPE workflows",
)

print(f"Starting Unified Webhook Router on port {PORT}")


def detect_workflow_type(content: str) -> tuple[Optional[WorkflowType], Optional[str]]:
    """Detect workflow type and command from content.

    IMPORTANT: Workflow lists must be ordered by specificity (longest/most-specific first)
    to prevent substring matching bugs. For example, 'adw_sdlc_zte_iso' must come
    before 'adw_sdlc_iso' since the latter is a substring prefix.

    Returns:
        tuple[WorkflowType | None, str | None]: (workflow_type, workflow_command)
    """
    content_lower = content.lower()

    # Check for IPE workflows first (more specific system)
    for workflow in AVAILABLE_IPE_WORKFLOWS:
        if workflow.lower() in content_lower:
            return ("ipe", workflow)

    # Check for ADW workflows
    for workflow in AVAILABLE_ADW_WORKFLOWS_LOCAL:
        if workflow.lower() in content_lower:
            return ("adw", workflow)

    return (None, None)


def is_bot_or_error_message(content: str) -> bool:
    """Check if content is from bot or an error message that shouldn't trigger workflows."""
    content_lower = content.lower()

    # Check for bot identifiers
    if any(bot_id in content for bot_id in BOT_IDENTIFIERS):
        return True

    # Check for error patterns (case-insensitive)
    if any(pattern in content_lower for pattern in ERROR_PATTERNS):
        return True

    return False




def check_recent_failure(issue_number: str, workflow_command: str) -> bool:
    """Check if this workflow recently failed for this issue."""
    import time

    key = f"{issue_number}:{workflow_command}"

    if key in RECENT_FAILURES:
        failure_time = RECENT_FAILURES[key]
        elapsed = time.time() - failure_time

        if elapsed < FAILURE_COOLDOWN_SECONDS:
            print(f"Ignoring {workflow_command} for issue #{issue_number} - recently failed {elapsed:.0f}s ago")
            return True

    return False


def record_failure(issue_number: str, workflow_command: str):
    """Record a workflow failure."""
    import time

    key = f"{issue_number}:{workflow_command}"
    RECENT_FAILURES[key] = time.time()


def extract_ipe_info_local(content: str, temp_id: str) -> dict:
    """Extract IPE workflow information from issue/comment content.

    Looks for patterns like:
    - ipe_plan_iso
    - ipe_build_iso ipe-12345678
    - ipe_test_iso ipe-12345678 sonnet
    - ipe_destroy environment=dev DESTROY

    Returns dict with:
    - has_workflow: bool
    - workflow_command: str or None
    - ipe_id: str or None
    - model_set: str or None
    - environment: str or None (for ipe_destroy)
    - delete_ami: bool (for ipe_destroy)
    - destroy_confirmed: bool (for ipe_destroy)
    """
    content_lower = content.lower()

    # Check if content contains any IPE workflow
    workflow_found = None
    for workflow in AVAILABLE_IPE_WORKFLOWS:
        if workflow.lower() in content_lower:
            workflow_found = workflow
            break

    if not workflow_found:
        return {
            "has_workflow": False,
            "workflow_command": None,
            "ipe_id": None,
            "model_set": None,
            "environment": None,
            "delete_ami": False,
            "destroy_confirmed": False,
            "deploy_mode": None,
            "ami_id": None,
        }

    # Try to extract IPE ID and model set from content
    # Pattern: ipe_workflow_name [ipe-id] [model]
    parts = content.split()
    ipe_id = None
    model_set = None

    for i, part in enumerate(parts):
        if part.lower() == workflow_found:
            # Check for ipe-id in next parts
            if i + 1 < len(parts) and parts[i + 1].startswith("ipe-"):
                ipe_id = parts[i + 1]
            # Check for model set
            if i + 2 < len(parts) and parts[i + 2] in ["sonnet", "opus", "haiku"]:
                model_set = parts[i + 2]
            elif i + 1 < len(parts) and parts[i + 1] in ["sonnet", "opus", "haiku"]:
                model_set = parts[i + 1]

    # For ipe_destroy, extract additional parameters
    environment = "dev"  # default
    delete_ami = False
    destroy_confirmed = False

    if workflow_found == "ipe_destroy":
        # Check for environment parameter
        if "environment=staging" in content_lower:
            environment = "staging"
        elif "environment=prod" in content_lower:
            environment = "prod"

        # Check for delete_ami flag
        if "delete_ami=true" in content_lower or "delete-ami" in content_lower:
            delete_ami = True

        # Check for DESTROY confirmation (must be uppercase)
        if "DESTROY" in content:  # Case-sensitive check
            destroy_confirmed = True

    # For ipe_deploy, extract additional parameters
    deploy_mode = None
    ami_id = None

    if workflow_found == "ipe_deploy":
        deploy_mode = "deploy-latest-ami"  # default

        if "mode=deploy-custom-ami" in content_lower:
            deploy_mode = "deploy-custom-ami"
        elif "mode=deploy-latest-ami" in content_lower:
            deploy_mode = "deploy-latest-ami"
        elif "mode=deploy" in content_lower and "mode=deploy-" not in content_lower:
            deploy_mode = "deploy"
        elif "mode=plan-only" in content_lower:
            deploy_mode = "plan-only"

        if "environment=staging" in content_lower:
            environment = "staging"
        elif "environment=prod" in content_lower:
            environment = "prod"
        elif "environment=dev" in content_lower:
            environment = "dev"

        import re
        ami_match = re.search(r'ami_id=(ami-[a-f0-9]+)', content_lower)
        if ami_match:
            ami_id = ami_match.group(1)

    # Extract build_new_ami parameter
    build_new_ami = None
    if "build_new_ami=true" in content_lower or "build-new-ami=true" in content_lower:
        build_new_ami = True
    elif "build_new_ami=false" in content_lower or "build-new-ami=false" in content_lower:
        build_new_ami = False

    return {
        "has_workflow": True,
        "workflow_command": workflow_found,
        "ipe_id": ipe_id,
        "model_set": model_set,
        "environment": environment,
        "delete_ami": delete_ami,
        "destroy_confirmed": destroy_confirmed,
        "deploy_mode": deploy_mode,
        "ami_id": ami_id,
        "build_new_ami": build_new_ami,
    }


def extract_workflow_info(content: str, workflow_type: WorkflowType, temp_id: str) -> dict:
    """Extract workflow information based on type.

    Returns:
        dict with keys:
        - has_workflow: bool
        - workflow_command: str or None
        - workflow_id: str or None (adw_id or ipe_id)
        - model_set: str or None
    """
    if workflow_type == "adw":
        result = extract_adw_info(content, temp_id)
        return {
            "has_workflow": result.has_workflow,
            "workflow_command": result.workflow_command,
            "workflow_id": result.adw_id,
            "model_set": result.model_set,
        }
    elif workflow_type == "ipe":
        # Use local IPE extraction function
        result = extract_ipe_info_local(content, temp_id)
        return {
            "has_workflow": result.get("has_workflow"),
            "workflow_command": result.get("workflow_command"),
            "workflow_id": result.get("ipe_id"),
            "model_set": result.get("model_set"),
            # Pass through destroy-specific params
            "environment": result.get("environment"),
            "delete_ami": result.get("delete_ami", False),
            "destroy_confirmed": result.get("destroy_confirmed", False),
            # Pass through deploy-specific params
            "deploy_mode": result.get("deploy_mode"),
            "ami_id": result.get("ami_id"),
            "build_new_ami": result.get("build_new_ami"),
        }

    return {
        "has_workflow": False,
        "workflow_command": None,
        "workflow_id": None,
        "model_set": None,
    }


async def handle_adw_workflow(
    workflow_command: str,
    issue_number: str,
    adw_id: Optional[str],
    model_set: Optional[str],
    trigger_reason: str,
):
    """Handle ADW workflow routing."""

    # Validate dependent workflows
    if workflow_command in ADW_DEPENDENT_WORKFLOWS and not adw_id:
        adw_make_issue_comment(
            issue_number,
            f"❌ Error: `{workflow_command}` requires an existing ADW ID.\n\n"
            f"Example: `{workflow_command} adw-12345678`",
        )
        return None

    # Generate or use provided ADW ID
    final_adw_id = adw_id or make_adw_id()

    # State management
    if adw_id:
        state = ADWState.load(adw_id)
        if state:
            state.update(issue_number=issue_number, model_set=model_set)
        else:
            state = ADWState(adw_id)
            state.update(
                adw_id=adw_id,
                issue_number=issue_number,
                model_set=model_set,
            )
    else:
        state = ADWState(final_adw_id)
        state.update(
            adw_id=final_adw_id,
            issue_number=issue_number,
            model_set=model_set,
        )
    state.save("webhook_router")

    # Set up logger
    logger = adw_setup_logger(final_adw_id, "webhook_router")
    logger.info(f"Routing ADW workflow: {workflow_command} for issue #{issue_number}")

    # Post notification
    adw_make_issue_comment(
        issue_number,
        f"[ADW-AGENTS] 🤖 ADW Webhook: Starting `{workflow_command}`\n\n"
        f"ID: `{final_adw_id}`\n"
        f"Type: Application Development\n"
        f"Reason: {trigger_reason}",
    )

    # Build and launch command
    # Use mapping to get actual script filename if different from detection name
    script_name = ADW_WORKFLOW_TO_SCRIPT.get(workflow_command, workflow_command)
    script_path = os.path.join(repo_root, "adws", f"{script_name}.py")
    cmd = ["uv", "run", script_path, issue_number, final_adw_id]

    print(f"Launching ADW workflow: {' '.join(cmd)}")
    print(f"Working directory: {repo_root}")

    # Create log directory for subprocess output
    log_dir = os.path.join(repo_root, "agents", final_adw_id, "webhook_subprocess")
    os.makedirs(log_dir, exist_ok=True)
    stdout_log = os.path.join(log_dir, "stdout.log")
    stderr_log = os.path.join(log_dir, "stderr.log")

    try:
        with open(stdout_log, "w") as stdout_f, open(stderr_log, "w") as stderr_f:
            process = subprocess.Popen(
                cmd,
                cwd=repo_root,
                env=get_safe_subprocess_env(),
                start_new_session=True,
                stdout=stdout_f,
                stderr=stderr_f,
            )
            logger.info(f"Successfully launched subprocess PID {process.pid}")
            print(f"Subprocess launched with PID: {process.pid}")
            print(f"Logs: {stdout_log}, {stderr_log}")
    except Exception as e:
        error_msg = f"Failed to launch subprocess: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        adw_make_issue_comment(
            issue_number,
            f"❌ **Webhook Error**: Failed to start workflow\n\n"
            f"Command: `{' '.join(cmd)}`\n"
            f"Error: `{str(e)}`\n\n"
            f"Please try triggering manually with:\n"
            f"```bash\nuv run adws/{workflow_command}.py {issue_number}\n```",
        )
        raise

    return {
        "status": "accepted",
        "type": "adw",
        "workflow": workflow_command,
        "id": final_adw_id,
    }


async def handle_ipe_workflow(
    workflow_command: str,
    issue_number: str,
    ipe_id: Optional[str],
    model_set: Optional[str],
    trigger_reason: str,
    # New parameters for destroy
    environment: Optional[str] = None,
    delete_ami: bool = False,
    destroy_confirmed: bool = False,
    # New parameters for deploy
    deploy_mode: Optional[str] = None,
    ami_id: Optional[str] = None,
    build_new_ami: Optional[bool] = None,
):
    """Handle IPE workflow routing."""

    # Special handling for destructive workflows
    if workflow_command == "ipe_destroy":
        if not destroy_confirmed:
            ipe_make_issue_comment(
                issue_number,
                "## Safety Check Failed\n\n"
                "Infrastructure destruction requires explicit confirmation.\n\n"
                "To destroy infrastructure, your comment must include:\n"
                "1. The word `DESTROY` (uppercase)\n"
                "2. The target environment: `environment=dev`, `environment=staging`, or `environment=prod`\n\n"
                "**Example:**\n"
                "```\n"
                "/ipe_destroy environment=dev DESTROY\n"
                "```\n\n"
                "**With AMI deletion:**\n"
                "```\n"
                "/ipe_destroy environment=dev delete_ami=true DESTROY\n"
                "```\n\n"
                "This action CANNOT be undone!",
            )
            return None

    # Special handling for deploy workflows
    if workflow_command == "ipe_deploy":
        if deploy_mode == "deploy-custom-ami" and not ami_id:
            ipe_make_issue_comment(
                issue_number,
                "## Parameter Validation Failed\n\n"
                "The `deploy-custom-ami` mode requires an AMI ID.\n\n"
                "**Example:**\n"
                "```\n"
                "/ipe_deploy mode=deploy-custom-ami environment=dev ami_id=ami-0123456789abcdef\n"
                "```\n\n"
                "**Available modes:**\n"
                "- `deploy` - Build new AMI and deploy\n"
                "- `deploy-latest-ami` - Use most recent AMI (fastest)\n"
                "- `deploy-custom-ami` - Deploy specific AMI by ID\n"
                "- `plan-only` - Terraform plan without apply",
            )
            return None

    # Validate dependent workflows
    if workflow_command in IPE_DEPENDENT_WORKFLOWS and not ipe_id:
        ipe_make_issue_comment(
            issue_number,
            f"❌ Error: `{workflow_command}` requires an existing IPE ID.\n\n"
            f"Example: `{workflow_command} ipe-12345678`",
        )
        return None

    # Generate or use provided IPE ID
    final_ipe_id = ipe_id or make_ipe_id()

    # State management
    if ipe_id:
        state = IPEState.load(ipe_id)
        if state:
            state.update(issue_number=issue_number, model_set=model_set)
        else:
            state = IPEState(ipe_id)
            state.update(
                ipe_id=ipe_id,
                issue_number=issue_number,
                model_set=model_set,
            )
    else:
        state = IPEState(final_ipe_id)
        state.update(
            ipe_id=final_ipe_id,
            issue_number=issue_number,
            model_set=model_set,
        )
    state.save("webhook_router")

    # Set up logger
    logger = ipe_setup_logger(final_ipe_id, "webhook_router")
    logger.info(f"Routing IPE workflow: {workflow_command} for issue #{issue_number}")

    # Post notification
    ipe_make_issue_comment(
        issue_number,
        f"🤖 IPE Webhook: Starting `{workflow_command}`\n\n"
        f"ID: `{final_ipe_id}`\n"
        f"Type: Infrastructure Engineering\n"
        f"Reason: {trigger_reason}",
    )

    # Build and launch command
    if workflow_command == "ipe_destroy":
        # Special command format for destroy
        script_path = os.path.join(repo_root, "ipe", "ipe_destroy.py")
        cmd = [
            "uv", "run", script_path,
            issue_number,
            final_ipe_id,
            environment or "dev",
            "true" if delete_ami else "false",
        ]
    elif workflow_command == "ipe_deploy":
        # Special command format for deploy
        script_path = os.path.join(repo_root, "ipe", "ipe_deploy.py")
        # Convert build_new_ami to string for CLI
        build_new_ami_str = ""
        if build_new_ami is True:
            build_new_ami_str = "true"
        elif build_new_ami is False:
            build_new_ami_str = "false"
        cmd = [
            "uv", "run", script_path,
            issue_number,
            final_ipe_id,
            deploy_mode or "deploy-latest-ami",
            environment or "dev",
            ami_id or "",
            build_new_ami_str,
        ]
    else:
        # Standard IPE workflow command
        script_path = os.path.join(repo_root, "ipe", f"{workflow_command}.py")
        cmd = ["uv", "run", script_path, issue_number, final_ipe_id]

    print(f"Launching IPE workflow: {' '.join(cmd)}")
    print(f"Working directory: {repo_root}")

    # Create log directory for subprocess output
    log_dir = os.path.join(repo_root, "agents", final_ipe_id, "webhook_subprocess")
    os.makedirs(log_dir, exist_ok=True)
    stdout_log = os.path.join(log_dir, "stdout.log")
    stderr_log = os.path.join(log_dir, "stderr.log")

    try:
        with open(stdout_log, "w") as stdout_f, open(stderr_log, "w") as stderr_f:
            process = subprocess.Popen(
                cmd,
                cwd=repo_root,
                env=get_safe_subprocess_env(),
                start_new_session=True,
                stdout=stdout_f,
                stderr=stderr_f,
            )
            logger.info(f"Successfully launched subprocess PID {process.pid}")
            print(f"Subprocess launched with PID: {process.pid}")
            print(f"Logs: {stdout_log}, {stderr_log}")
    except Exception as e:
        error_msg = f"Failed to launch subprocess: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        ipe_make_issue_comment(
            issue_number,
            f"❌ **Webhook Error**: Failed to start workflow\n\n"
            f"Command: `{' '.join(cmd)}`\n"
            f"Error: `{str(e)}`\n\n"
            f"Please try triggering manually with:\n"
            f"```bash\nuv run ipe/{workflow_command}.py {issue_number}\n```",
        )
        raise

    return {
        "status": "accepted",
        "type": "ipe",
        "workflow": workflow_command,
        "id": final_ipe_id,
    }


async def route_workflow(
    workflow_type: WorkflowType,
    workflow_command: str,
    issue_number: str,
    workflow_id: Optional[str],
    model_set: Optional[str],
    trigger_reason: str,
    # New optional params for destroy
    environment: Optional[str] = None,
    delete_ami: bool = False,
    destroy_confirmed: bool = False,
    # New optional params for deploy
    deploy_mode: Optional[str] = None,
    ami_id: Optional[str] = None,
    build_new_ami: Optional[bool] = None,
):
    """Route workflow to appropriate system."""

    if workflow_type == "adw":
        return await handle_adw_workflow(
            workflow_command, issue_number, workflow_id, model_set, trigger_reason,
        )
    elif workflow_type == "ipe":
        return await handle_ipe_workflow(
            workflow_command, issue_number, workflow_id, model_set, trigger_reason,
            environment=environment,
            delete_ami=delete_ami,
            destroy_confirmed=destroy_confirmed,
            deploy_mode=deploy_mode,
            ami_id=ami_id,
            build_new_ami=build_new_ami,
        )


@app.post("/gh-webhook")
async def github_webhook(request: Request):
    """Unified webhook handler for ADW and IPE."""
    try:
        event_type = request.headers.get("X-GitHub-Event", "")
        payload = await request.json()
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")

        print(
            f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}"
        )

        content_to_check = ""

        # Extract content from issue or comment
        if event_type == "issues" and action == "opened":
            content_to_check = issue.get("body", "")
        elif event_type == "issue_comment" and action == "created":
            content_to_check = payload.get("comment", {}).get("body", "")

        # Check for bot messages or error messages to prevent loops
        if is_bot_or_error_message(content_to_check):
            print("Ignoring bot/error message to prevent loop")
            return {"status": "ignored", "reason": "Bot or error message - preventing loop"}

        # Detect workflow type
        workflow_type, workflow_command = detect_workflow_type(content_to_check)

        if not workflow_type:
            print("No ADW or IPE workflow detected")
            return {
                "status": "ignored",
                "reason": "No ADW or IPE workflow detected",
            }

        print(f"Detected {workflow_type.upper()} workflow: {workflow_command}")

        # Check if this workflow recently failed for this issue
        if check_recent_failure(str(issue_number), workflow_command):
            return {
                "status": "ignored",
                "reason": f"Recently failed - cooldown period active"
            }

        # Extract workflow details
        temp_id = make_adw_id() if workflow_type == "adw" else make_ipe_id()
        workflow_info = extract_workflow_info(
            content_to_check, workflow_type, temp_id
        )

        if not workflow_info["has_workflow"]:
            print("Workflow extraction failed")
            return {"status": "ignored", "reason": "Workflow extraction failed"}

        # Route to appropriate handler
        trigger_reason = (
            f"{'Issue' if event_type == 'issues' else 'Comment'} with {workflow_command}"
        )

        result = await route_workflow(
            workflow_type,
            workflow_info["workflow_command"],
            str(issue_number),
            workflow_info["workflow_id"],
            workflow_info["model_set"],
            trigger_reason,
            # Pass destroy-specific params
            environment=workflow_info.get("environment"),
            delete_ami=workflow_info.get("delete_ami", False),
            destroy_confirmed=workflow_info.get("destroy_confirmed", False),
            # Pass deploy-specific params
            deploy_mode=workflow_info.get("deploy_mode"),
            ami_id=workflow_info.get("ami_id"),
            build_new_ami=workflow_info.get("build_new_ami"),
        )

        return result or {"status": "error", "reason": "Routing failed"}

    except Exception as e:
        print(f"Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


async def check_adw_health():
    """Check ADW subsystem health."""
    try:
        # Check if ADW modules are importable
        from adw_modules.utils import make_adw_id
        from adw_modules.github import make_issue_comment

        return {
            "status": "healthy",
            "workflows": AVAILABLE_ADW_WORKFLOWS_LOCAL,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_ipe_health():
    """Check IPE subsystem health."""
    try:
        # Check if IPE modules are importable
        from ipe_modules.ipe_utils import make_ipe_id
        from ipe_modules.ipe_github import make_issue_comment

        return {
            "status": "healthy",
            "workflows": AVAILABLE_IPE_WORKFLOWS,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@app.get("/health")
async def health():
    """Unified health check for router and both subsystems."""
    try:
        # Check ADW health
        adw_health = await check_adw_health()

        # Check IPE health
        ipe_health = await check_ipe_health()

        # Router is healthy if both subsystems are operational
        overall_healthy = (
            adw_health.get("status") == "healthy"
            and ipe_health.get("status") == "healthy"
        )

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "service": "unified-webhook-router",
            "port": PORT,
            "subsystems": {
                "adw": adw_health,
                "ipe": ipe_health,
            },
            "workflows_available": {
                "adw": AVAILABLE_ADW_WORKFLOWS_LOCAL,
                "ipe": AVAILABLE_IPE_WORKFLOWS,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "unified-webhook-router",
            "error": str(e),
        }


if __name__ == "__main__":
    print(f"Starting server on http://0.0.0.0:{PORT}")
    print(f"Webhook endpoint: POST /gh-webhook")
    print(f"Health check: GET /health")
    print(f"")
    print(f"Supported workflows:")
    print(f"  ADW: {', '.join(AVAILABLE_ADW_WORKFLOWS_LOCAL)}")
    print(f"  IPE: {', '.join(AVAILABLE_IPE_WORKFLOWS)}")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
