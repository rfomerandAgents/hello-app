"""Shared Infrastructure Platform Engineer (IPE) workflow operations."""

import glob
import json
import logging
import os
import subprocess
import re
from typing import Tuple, Optional
from .ipe_data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
    IPEExtractionResult,
    RetryCode,
)
from .ipe_agent import execute_template
from .ipe_github import get_repo_url, extract_repo_path, IPE_BOT_IDENTIFIER
from .ipe_state import IPEState
from .ipe_utils import parse_json


def validate_slash_command_exists(
    command: str,
    working_dir: Optional[str] = None,
) -> Tuple[bool, str]:
    """Validate that a slash command file exists.

    Args:
        command: Slash command (e.g., "/ipe_feature")
        working_dir: Optional working directory to check from

    Returns:
        Tuple of (exists, full_path)
    """
    command_name = command.lstrip("/")
    relative_path = f".claude/commands/{command_name}.md"

    if working_dir:
        full_path = os.path.join(working_dir, relative_path)
    else:
        # Default to project root
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        full_path = os.path.join(project_root, relative_path)

    return os.path.exists(full_path), full_path


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_BUILDER = "sdlc_builder"  # IPE terminology for infrastructure implementation
AGENT_VALIDATOR = "sdlc_validator"  # IPE terminology for infrastructure validation
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"

# Available ADW workflows for runtime validation
AVAILABLE_ADW_WORKFLOWS = [
    # Isolated workflows (all workflows are now iso-based)
    "adw_plan_iso",
    "adw_patch_iso",
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
    "adw_sdlc_ZTE_iso",  # Zero Touch Execution workflow
    "adw_plan_build_iso",
    "adw_plan_build_test_iso",
    "adw_plan_build_test_review_iso",
    "adw_plan_build_document_iso",
    "adw_plan_build_review_iso",
    "adw_sdlc_iso",
]

# Available IPE workflows for runtime validation
AVAILABLE_IPE_WORKFLOWS = [
    # Isolated workflows (all workflows are now iso-based)
    "ipe_plan_iso",
    "ipe_patch_iso",
    "ipe_build_iso",
    "ipe_build_ami_iso",
    "ipe_test_iso",
    "ipe_review_iso",
    "ipe_document_iso",
    "ipe_ship_iso",
    "ipe_sdlc_zte_iso",  # Zero Touch Execution workflow
    "ipe_plan_build_iso",
    "ipe_plan_build_test_iso",
    "ipe_plan_build_test_review_iso",
    "ipe_plan_build_document_iso",
    "ipe_plan_build_review_iso",
    "ipe_sdlc_iso",
]


def format_issue_message(
    ipe_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier."""
    # Always include IPE_BOT_IDENTIFIER to prevent webhook loops
    if session_id:
        return f"{IPE_BOT_IDENTIFIER} {ipe_id}_{agent_name}_{session_id}: {message}"
    return f"{IPE_BOT_IDENTIFIER} {ipe_id}_{agent_name}: {message}"


def extract_adw_info(text: str, temp_ipe_id: str) -> IPEExtractionResult:
    """Extract ADW workflow, ID, and model_set from text using classify_adw agent.
    Returns IPEExtractionResult with workflow_command, ipe_id, and model_set."""

    # Use classify_adw to extract structured info
    request = AgentTemplateRequest(
        agent_name="adw_classifier",
        slash_command="/classify_adw",
        args=[text],
        ipe_id=temp_ipe_id,
    )

    try:
        response = execute_template(request)  # No logger available in this function

        if not response.success:
            print(f"Failed to classify ADW: {response.output}")
            return IPEExtractionResult()  # Empty result

        # Parse JSON response using utility that handles markdown
        try:
            data = parse_json(response.output, dict)
            adw_command = data.get("adw_slash_command", "").replace(
                "/", ""
            )  # Remove slash
            ipe_id = data.get("ipe_id")
            model_set = data.get("model_set", "base")  # Default to "base"

            # Validate command
            if adw_command and adw_command in AVAILABLE_ADW_WORKFLOWS:
                return IPEExtractionResult(
                    workflow_command=adw_command,
                    ipe_id=ipe_id,
                    model_set=model_set
                )

            return IPEExtractionResult()  # Empty result

        except ValueError as e:
            print(f"Failed to parse classify_adw response: {e}")
            return IPEExtractionResult()  # Empty result

    except Exception as e:
        print(f"Error calling classify_adw: {e}")
        return IPEExtractionResult()  # Empty result


def extract_ipe_info(text: str, temp_ipe_id: str) -> IPEExtractionResult:
    """Extract IPE workflow, ID, and model_set from text using classify_ipe agent.
    Returns IPEExtractionResult with workflow_command, ipe_id, and model_set."""

    # Use classify_ipe to extract structured info
    request = AgentTemplateRequest(
        agent_name="ipe_classifier",
        slash_command="/classify_ipe",
        args=[text],
        ipe_id=temp_ipe_id,
    )

    try:
        response = execute_template(request)  # No logger available in this function

        if not response.success:
            print(f"Failed to classify IPE: {response.output}")
            return IPEExtractionResult()  # Empty result

        # Parse JSON response using utility that handles markdown
        try:
            data = parse_json(response.output, dict)
            ipe_command = data.get("ipe_slash_command", "").replace(
                "/", ""
            )  # Remove slash
            ipe_id = data.get("ipe_id")
            model_set = data.get("model_set", "base")  # Default to "base"

            # Validate command
            if ipe_command and ipe_command in AVAILABLE_IPE_WORKFLOWS:
                return IPEExtractionResult(
                    workflow_command=ipe_command,
                    ipe_id=ipe_id,
                    model_set=model_set
                )

            return IPEExtractionResult()  # Empty result

        except ValueError as e:
            print(f"Failed to parse classify_ipe response: {e}")
            return IPEExtractionResult()  # Empty result

    except Exception as e:
        print(f"Error calling classify_ipe: {e}")
        return IPEExtractionResult()  # Empty result


def classify_issue(
    issue: GitHubIssue, ipe_id: str, logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.
    Returns (command, error_message) tuple."""

    # Use the classify_issue slash command template with minimal payload
    # Only include the essential fields: number, title, body
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[minimal_issue_json],
        ipe_id=ipe_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")

    response = execute_template(request)

    logger.debug(
        f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        return None, response.output

    # Extract the classification from the response
    output = response.output.strip()

    # Look for the classification pattern in the output
    # Claude might add explanation, so we need to extract just the command
    classification_match = re.search(r"(/ipe_chore|/ipe_bug|/ipe_feature|0)", output)

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in ["/ipe_chore", "/ipe_bug", "/ipe_feature"]:
        return None, f"Invalid command selected: {response.output}"

    return issue_command, None  # type: ignore


def build_plan(
    issue: GitHubIssue,
    command: str,
    ipe_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command."""

    # Validate slash command file exists before executing
    exists, cmd_path = validate_slash_command_exists(command, working_dir)
    if not exists:
        error_msg = f"Slash command file not found: {cmd_path} (command: {command})"
        logger.error(error_msg)
        return AgentPromptResponse(
            output=error_msg,
            success=False,
            session_id=None,
            retry_code=RetryCode.NONE,
            duration_ms=None,
        )

    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    issue_plan_template_request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=command,
        args=[str(issue.number), ipe_id, minimal_issue_json],
        ipe_id=ipe_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"issue_plan_template_request: {issue_plan_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    issue_plan_response = execute_template(issue_plan_template_request)

    logger.debug(
        f"issue_plan_response: {issue_plan_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return issue_plan_response


def implement_plan(
    spec_file: str,
    ipe_id: str,
    logger: logging.Logger,
    agent_name: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Implement the plan using the /ipe_build command."""
    # Use provided agent_name or default to AGENT_IMPLEMENTOR
    implementor_name = agent_name or AGENT_IMPLEMENTOR

    implement_template_request = AgentTemplateRequest(
        agent_name=implementor_name,
        slash_command="/ipe_build",
        args=[spec_file],
        ipe_id=ipe_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"implement_template_request: {implement_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    implement_response = execute_template(implement_template_request)

    logger.debug(
        f"implement_response: {implement_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return implement_response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    ipe_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate a git branch name for the issue.
    Returns (branch_name, error_message) tuple."""
    # Remove the leading slash from issue_class for the branch name
    issue_type = issue_class.replace("/", "")

    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, ipe_id, minimal_issue_json],
        ipe_id=ipe_id,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    branch_name = response.output.strip()

    # Strip markdown code fences if present
    if branch_name.startswith("```"):
        lines = branch_name.split("\n")
        # Remove first and last lines if they are code fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        branch_name = "\n".join(lines).strip()

    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    ipe_id: str,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.
    Returns (commit_message, error_message) tuple."""
    # Remove the leading slash from issue_class
    issue_type = issue_class.replace("/", "")

    # Create unique committer agent name by suffixing '_committer'
    unique_agent_name = f"{agent_name}_committer"

    # Use minimal payload like classify_issue does
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        slash_command="/ipe_commit",
        args=[agent_name, issue_type, minimal_issue_json],
        ipe_id=ipe_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit message: {commit_message}")
    return commit_message, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: IPEState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.
    Returns (pr_url, error_message) tuple."""

    # Get plan file from state (may be None for test runs)
    spec_file = state.get("spec_file") or "No plan file (test run)"
    ipe_id = state.get("ipe_id")

    # If we don't have issue data, try to construct minimal data
    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        # Try to reconstruct as GitHubIssue model which handles datetime serialization
        from .ipe_data_types import GitHubIssue

        try:
            issue_model = GitHubIssue(**issue)
            # Use minimal payload like classify_issue does
            issue_json = issue_model.model_dump_json(
                by_alias=True, include={"number", "title", "body"}
            )
        except Exception:
            # Fallback: use json.dumps with default str converter for datetime
            issue_json = json.dumps(issue, default=str)
    else:
        # Use minimal payload like classify_issue does
        issue_json = issue.model_dump_json(
            by_alias=True, include={"number", "title", "body"}
        )

    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/ipe_pull_request",
        args=[branch_name, issue_json, spec_file, ipe_id],
        ipe_id=ipe_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def ensure_plan_exists(state: IPEState, issue_number: str) -> str:
    """Find or error if no plan exists for issue.
    Used by isolated build workflows in standalone mode."""
    # Check if plan file is in state
    if state.get("spec_file"):
        return state.get("spec_file")

    # Check current branch
    from .ipe_git_ops import get_current_branch

    branch = get_current_branch()

    # Look for plan in branch name
    if f"-{issue_number}-" in branch:
        # Look for plan file
        plans = glob.glob(f"specs/*{issue_number}*.md")
        if plans:
            return plans[0]

    # No plan found
    raise ValueError(
        f"No plan found for issue {issue_number}. Run adw_plan_iso.py first."
    )


def ensure_ipe_id(
    issue_number: str,
    ipe_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get ADW ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create ADW ID for
        ipe_id: Optional existing ADW ID to use
        logger: Optional logger instance

    Returns:
        The ADW ID (existing or newly created)
    """
    # If ADW ID provided, check if state exists
    if ipe_id:
        state = IPEState.load(ipe_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ADW state for ID: {ipe_id}")
            else:
                print(f"Found existing ADW state for ID: {ipe_id}")
            return ipe_id
        # ADW ID provided but no state exists, create state
        state = IPEState(ipe_id)
        state.update(ipe_id=ipe_id, issue_number=issue_number)
        state.save("ensure_ipe_id")
        if logger:
            logger.info(f"Created new ADW state for provided ID: {ipe_id}")
        else:
            print(f"Created new ADW state for provided ID: {ipe_id}")
        return ipe_id

    # No ADW ID provided, create new one with state
    from .ipe_utils import make_ipe_id

    new_ipe_id = make_ipe_id()
    state = IPEState(new_ipe_id)
    state.update(ipe_id=new_ipe_id, issue_number=issue_number)
    state.save("ensure_ipe_id")
    if logger:
        logger.info(f"Created new ADW ID and state: {new_ipe_id}")
    else:
        print(f"Created new ADW ID and state: {new_ipe_id}")
    return new_ipe_id


def find_existing_branch_for_issue(
    issue_number: str, ipe_id: Optional[str] = None, cwd: Optional[str] = None
) -> Optional[str]:
    """Find an existing branch for the given issue number.
    Returns branch name if found, None otherwise."""
    # List all branches
    result = subprocess.run(
        ["git", "branch", "-a"], capture_output=True, text=True, cwd=cwd
    )

    if result.returncode != 0:
        return None

    branches = result.stdout.strip().split("\n")

    # Look for branch with standardized pattern: *-issue-{issue_number}-adw-{ipe_id}-*
    for branch in branches:
        branch = branch.strip().replace("* ", "").replace("remotes/origin/", "")
        # Check for the standardized pattern
        if f"-issue-{issue_number}-" in branch:
            if ipe_id and f"-adw-{ipe_id}-" in branch:
                return branch
            elif not ipe_id:
                # Return first match if no ipe_id specified
                return branch

    return None


def find_plan_for_issue(
    issue_number: str, ipe_id: Optional[str] = None
) -> Optional[str]:
    """Find plan file for the given issue number and optional ipe_id.
    Returns path to plan file if found, None otherwise."""
    import os

    # Get project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    agents_dir = os.path.join(project_root, "agents")

    if not os.path.exists(agents_dir):
        return None

    # If ipe_id is provided, check specific directory first
    if ipe_id:
        plan_path = os.path.join(agents_dir, ipe_id, AGENT_PLANNER, "plan.md")
        if os.path.exists(plan_path):
            return plan_path

    # Otherwise, search all agent directories
    for agent_id in os.listdir(agents_dir):
        agent_path = os.path.join(agents_dir, agent_id)
        if os.path.isdir(agent_path):
            plan_path = os.path.join(agent_path, AGENT_PLANNER, "plan.md")
            if os.path.exists(plan_path):
                # Check if this plan is for our issue by reading branch info or checking commits
                # For now, return the first plan found (can be improved)
                return plan_path

    return None


def create_or_find_branch(
    issue_number: str,
    issue: GitHubIssue,
    state: IPEState,
    logger: logging.Logger,
    cwd: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Create or find a branch for the given issue.

    1. First checks state for existing branch name
    2. Then looks for existing branches matching the issue
    3. If none found, classifies the issue and creates a new branch

    Returns (branch_name, error_message) tuple.
    """
    # 1. Check state for branch name
    branch_name = state.get("branch_name") or state.get("branch", {}).get("name")
    if branch_name:
        logger.info(f"Found branch in state: {branch_name}")
        # Check if we need to checkout
        from .ipe_git_ops import get_current_branch

        current = get_current_branch(cwd=cwd)
        if current != branch_name:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                # Branch might not exist locally, try to create from remote
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                )
                if result.returncode != 0:
                    return "", f"Failed to checkout branch: {result.stderr}"
        return branch_name, None

    # 2. Look for existing branch
    ipe_id = state.get("ipe_id")
    existing_branch = find_existing_branch_for_issue(issue_number, ipe_id, cwd=cwd)
    if existing_branch:
        logger.info(f"Found existing branch: {existing_branch}")
        # Checkout the branch
        result = subprocess.run(
            ["git", "checkout", existing_branch],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode != 0:
            return "", f"Failed to checkout branch: {result.stderr}"
        state.update(branch_name=existing_branch)
        return existing_branch, None

    # 3. Create new branch - classify issue first
    logger.info("No existing branch found, creating new one")

    # Classify the issue
    issue_command, error = classify_issue(issue, ipe_id, logger)
    if error:
        return "", f"Failed to classify issue: {error}"

    state.update(issue_class=issue_command)

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, ipe_id, logger)
    if error:
        return "", f"Failed to generate branch name: {error}"

    # Create the branch
    from .ipe_git_ops import create_branch

    success, error = create_branch(branch_name, cwd=cwd)
    if not success:
        return "", f"Failed to create branch: {error}"

    state.update(branch_name=branch_name)
    logger.info(f"Created and checked out new branch: {branch_name}")

    return branch_name, None


def find_spec_file(state: IPEState, logger: logging.Logger) -> Optional[str]:
    """Find the spec file from state or by examining git diff.

    For isolated workflows, automatically uses worktree_path from state.
    """
    # Get worktree path if in isolated workflow
    worktree_path = state.get("worktree_path")

    # Check if spec file is already in state (from plan phase)
    spec_file = state.get("spec_file")
    if spec_file:
        # If worktree_path exists and spec_file is relative, make it absolute
        if worktree_path and not os.path.isabs(spec_file):
            spec_file = os.path.join(worktree_path, spec_file)

        if os.path.exists(spec_file):
            logger.info(f"Using spec file from state: {spec_file}")
            return spec_file

    # Otherwise, try to find it from git diff
    logger.info("Looking for spec file in git diff")
    result = subprocess.run(
        ["git", "diff", "origin/main", "--name-only"],
        capture_output=True,
        text=True,
        cwd=worktree_path,
    )

    if result.returncode == 0:
        files = result.stdout.strip().split("\n")
        spec_files = [f for f in files if f.startswith("specs/") and f.endswith(".md")]

        if spec_files:
            # Use the first spec file found
            spec_file = spec_files[0]
            if worktree_path:
                spec_file = os.path.join(worktree_path, spec_file)
            logger.info(f"Found spec file: {spec_file}")
            return spec_file

    # If still not found, try to derive from branch name
    branch_name = state.get("branch_name")
    if branch_name:
        # Extract issue number from branch name
        import re

        match = re.search(r"issue-(\d+)", branch_name)
        if match:
            issue_num = match.group(1)
            ipe_id = state.get("ipe_id")

            # Look for spec files matching the pattern
            import glob

            # Use worktree_path if provided, otherwise current directory
            search_dir = worktree_path if worktree_path else os.getcwd()
            pattern = os.path.join(
                search_dir, f"specs/issue-{issue_num}-adw-{ipe_id}*.md"
            )
            spec_files = glob.glob(pattern)

            if spec_files:
                spec_file = spec_files[0]
                logger.info(f"Found spec file by pattern: {spec_file}")
                return spec_file

    logger.warning("No spec file found")
    return None


def create_and_implement_patch(
    ipe_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
    """Create a patch plan and implement it.
    Returns (patch_file_path, implement_response) tuple."""

    # Create patch plan using /ipe_patch command
    args = [ipe_id, review_change_request]

    # Add optional arguments in the correct order
    if spec_path:
        args.append(spec_path)
    else:
        args.append("")  # Empty string for optional spec_path

    args.append(agent_name_planner)

    if issue_screenshots:
        args.append(issue_screenshots)

    request = AgentTemplateRequest(
        agent_name=agent_name_planner,
        slash_command="/ipe_patch",
        args=args,
        ipe_id=ipe_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"Patch plan request: {request.model_dump_json(indent=2, by_alias=True)}"
    )

    response = execute_template(request)

    logger.debug(
        f"Patch plan response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        logger.error(f"Error creating patch plan: {response.output}")
        # Return None and a failed response
        return None, AgentPromptResponse(
            output=f"Failed to create patch plan: {response.output}", success=False
        )

    # Extract the patch plan file path from the response
    patch_file_path = response.output.strip()

    # Validate that it looks like a file path
    if "specs/patch/" not in patch_file_path or not patch_file_path.endswith(".md"):
        logger.error(f"Invalid patch plan path returned: {patch_file_path}")
        return None, AgentPromptResponse(
            output=f"Invalid patch plan path: {patch_file_path}", success=False
        )

    logger.info(f"Created patch plan: {patch_file_path}")

    # Now implement the patch plan using the provided implementor agent name
    implement_response = implement_plan(
        patch_file_path, ipe_id, logger, agent_name_implementor, working_dir=working_dir
    )

    return patch_file_path, implement_response
