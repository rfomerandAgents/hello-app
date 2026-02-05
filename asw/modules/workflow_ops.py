"""Shared ASW (Agentic Software Workflow) operations.

Supports both application (app) and infrastructure (io) workflows.
"""

import glob
import json
import logging
import os
import subprocess
import re
from typing import Tuple, Optional
from .data_types import (
    AppAgentTemplateRequest,
    IOAgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    AppIssueClassSlashCommand,
    IOIssueClassSlashCommand,
    ASWAppExtractionResult,
    ASWIOExtractionResult,
    RetryCode,
)
from .agent import execute_template
from .github import get_repo_url, extract_repo_path, ASW_APP_BOT_IDENTIFIER, ASW_IO_BOT_IDENTIFIER
from .utils import parse_json


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_BUILDER = "sdlc_builder"  # IO terminology for infrastructure implementation
AGENT_VALIDATOR = "sdlc_validator"  # IO terminology for infrastructure validation
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"

# Available ASW App workflows for runtime validation
# ORDERED BY SPECIFICITY - longest/most-specific first to prevent substring matching bugs
AVAILABLE_ASW_APP_WORKFLOWS = [
    # Compound workflows (most specific - longest names first)
    "asw_app_plan_build_test_review_iso",
    "asw_app_plan_build_document_iso",
    "asw_app_plan_build_review_iso",
    "asw_app_plan_build_test_iso",
    "asw_app_plan_build_iso",
    # SDLC variants (ZTE before base sdlc)
    "asw_app_sdlc_ZTE_iso",  # Zero Touch Execution workflow
    "asw_app_sdlc_iso",
    # Individual phase workflows
    "asw_app_document_iso",
    "asw_app_review_iso",
    "asw_app_build_iso",
    "asw_app_patch_iso",
    "asw_app_test_iso",
    "asw_app_plan_iso",
    "asw_app_ship_iso",
]

# Available ASW IO workflows for runtime validation
AVAILABLE_ASW_IO_WORKFLOWS = [
    # Compound workflows
    "asw_io_plan_build_test_review_iso",
    "asw_io_plan_build_document_iso",
    "asw_io_plan_build_review_iso",
    "asw_io_plan_build_test_iso",
    "asw_io_plan_build_iso",
    # SDLC variants
    "asw_io_sdlc_zte_iso",
    "asw_io_sdlc_iso",
    # Individual phase workflows
    "asw_io_plan_iso",
    "asw_io_patch_iso",
    "asw_io_build_iso",
    "asw_io_build_ami_iso",
    "asw_io_test_iso",
    "asw_io_review_iso",
    "asw_io_document_iso",
    "asw_io_ship_iso",
]

# Legacy aliases
AVAILABLE_ADW_WORKFLOWS = AVAILABLE_ASW_APP_WORKFLOWS
AVAILABLE_IPE_WORKFLOWS = AVAILABLE_ASW_IO_WORKFLOWS


def format_issue_message(
    asw_id: str, agent_name: str, message: str, session_id: Optional[str] = None, workflow_type: str = "app"
) -> str:
    """Format a message for issue comments with ASW tracking and bot identifier."""
    bot_identifier = ASW_APP_BOT_IDENTIFIER if workflow_type == "app" else ASW_IO_BOT_IDENTIFIER
    if session_id:
        return f"{bot_identifier} {asw_id}_{agent_name}_{session_id}: {message}"
    return f"{bot_identifier} {asw_id}_{agent_name}: {message}"


def extract_asw_app_info(text: str, temp_asw_id: str) -> ASWAppExtractionResult:
    """Extract app workflow, ID, and model_set from text using classify_asw_app agent.
    Returns ASWAppExtractionResult with workflow_command, asw_id, and model_set."""

    request = AppAgentTemplateRequest(
        agent_name="asw_classifier",
        slash_command="/classify_asw_app",
        args=[text],
        asw_id=temp_asw_id,
    )

    try:
        response = execute_template(request)

        if not response.success:
            print(f"Failed to classify ASW App: {response.output}")
            return ASWAppExtractionResult()

        try:
            data = parse_json(response.output, dict)
            asw_command = data.get("asw_slash_command", "").replace("/", "")
            asw_id = data.get("asw_id")
            model_set = data.get("model_set", "base")

            if asw_command and asw_command in AVAILABLE_ASW_APP_WORKFLOWS:
                return ASWAppExtractionResult(
                    workflow_command=asw_command,
                    asw_id=asw_id,
                    model_set=model_set
                )

            return ASWAppExtractionResult()

        except ValueError as e:
            print(f"Failed to parse classify_asw_app response: {e}")
            return ASWAppExtractionResult()

    except Exception as e:
        print(f"Error calling classify_asw_app: {e}")
        return ASWAppExtractionResult()


def extract_asw_io_info(text: str, temp_asw_id: str) -> ASWIOExtractionResult:
    """Extract IO workflow, ID, and model_set from text using classify_asw_io agent.
    Returns ASWIOExtractionResult with workflow_command, asw_id, and model_set."""

    request = IOAgentTemplateRequest(
        agent_name="asw_classifier",
        slash_command="/classify_asw_io",
        args=[text],
        asw_id=temp_asw_id,
    )

    try:
        response = execute_template(request)

        if not response.success:
            print(f"Failed to classify ASW IO: {response.output}")
            return ASWIOExtractionResult()

        try:
            data = parse_json(response.output, dict)
            asw_command = data.get("asw_slash_command", "").replace("/", "")
            asw_id = data.get("asw_id")
            model_set = data.get("model_set", "base")

            if asw_command and asw_command in AVAILABLE_ASW_IO_WORKFLOWS:
                return ASWIOExtractionResult(
                    workflow_command=asw_command,
                    asw_id=asw_id,
                    model_set=model_set
                )

            return ASWIOExtractionResult()

        except ValueError as e:
            print(f"Failed to parse classify_asw_io response: {e}")
            return ASWIOExtractionResult()

    except Exception as e:
        print(f"Error calling classify_asw_io: {e}")
        return ASWIOExtractionResult()


# Legacy aliases
extract_adw_info = extract_asw_app_info
extract_ipe_info = extract_asw_io_info


def classify_issue(
    issue: GitHubIssue, asw_id: str, logger: logging.Logger, cache_enabled: bool = True, workflow_type: str = "app"
) -> Tuple[Optional[str], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.
    Returns (command, error_message) tuple."""

    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    if workflow_type == "app":
        request = AppAgentTemplateRequest(
            agent_name=AGENT_CLASSIFIER,
            slash_command="/classify_issue",
            args=[minimal_issue_json],
            asw_id=asw_id,
            cache_enabled=cache_enabled,
        )
    else:
        request = IOAgentTemplateRequest(
            agent_name=AGENT_CLASSIFIER,
            slash_command="/classify_issue",
            args=[minimal_issue_json],
            asw_id=asw_id,
        )

    logger.debug(f"Classifying issue: {issue.title}")

    response = execute_template(request)

    logger.debug(
        f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        return None, response.output

    output = response.output.strip()

    # Look for classification pattern
    if workflow_type == "app":
        classification_match = re.search(r"(/chore|/bug|/feature|/patch|\b0\b)", output)
        valid_commands = ["/chore", "/bug", "/feature", "/patch"]
    else:
        classification_match = re.search(r"(/asw_io_chore|/asw_io_bug|/asw_io_feature|\b0\b)", output)
        valid_commands = ["/asw_io_chore", "/asw_io_bug", "/asw_io_feature"]

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in valid_commands:
        return None, f"Invalid command selected: {response.output}"

    return issue_command, None


def build_plan(
    issue: GitHubIssue,
    command: str,
    asw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    cache_enabled: bool = True,
    workflow_type: str = "app",
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command."""

    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    if workflow_type == "app":
        request = AppAgentTemplateRequest(
            agent_name=AGENT_PLANNER,
            slash_command=command,
            args=[str(issue.number), asw_id, minimal_issue_json],
            asw_id=asw_id,
            working_dir=working_dir,
            cache_enabled=cache_enabled,
        )
    else:
        request = IOAgentTemplateRequest(
            agent_name=AGENT_PLANNER,
            slash_command=command,
            args=[str(issue.number), asw_id, minimal_issue_json],
            asw_id=asw_id,
            working_dir=working_dir,
        )

    logger.debug(
        f"Plan request: {request.model_dump_json(indent=2, by_alias=True)}"
    )

    response = execute_template(request)

    logger.debug(
        f"Plan response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    return response


def implement_plan(
    plan_file: str,
    asw_id: str,
    logger: logging.Logger,
    agent_name: Optional[str] = None,
    working_dir: Optional[str] = None,
    cache_enabled: bool = True,
    workflow_type: str = "app",
) -> AgentPromptResponse:
    """Implement the plan using the /implement or /asw_io_build command."""
    implementor_name = agent_name or AGENT_IMPLEMENTOR

    if workflow_type == "app":
        request = AppAgentTemplateRequest(
            agent_name=implementor_name,
            slash_command="/implement",
            args=[plan_file],
            asw_id=asw_id,
            working_dir=working_dir,
            cache_enabled=cache_enabled,
        )
    else:
        request = IOAgentTemplateRequest(
            agent_name=implementor_name,
            slash_command="/asw_io_build",
            args=[plan_file],
            asw_id=asw_id,
            working_dir=working_dir,
        )

    logger.debug(
        f"Implement request: {request.model_dump_json(indent=2, by_alias=True)}"
    )

    response = execute_template(request)

    logger.debug(
        f"Implement response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    return response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: str,
    asw_id: str,
    logger: logging.Logger,
    cache_enabled: bool = True,
    workflow_type: str = "app",
) -> Tuple[Optional[str], Optional[str]]:
    """Generate a git branch name for the issue.
    Returns (branch_name, error_message) tuple."""
    issue_type = issue_class.replace("/", "")

    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    if workflow_type == "app":
        request = AppAgentTemplateRequest(
            agent_name=AGENT_BRANCH_GENERATOR,
            slash_command="/generate_branch_name",
            args=[issue_type, asw_id, minimal_issue_json],
            asw_id=asw_id,
            cache_enabled=cache_enabled,
        )
    else:
        request = IOAgentTemplateRequest(
            agent_name=AGENT_BRANCH_GENERATOR,
            slash_command="/generate_branch_name",
            args=[issue_type, asw_id, minimal_issue_json],
            asw_id=asw_id,
        )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    output_lines = [line.strip() for line in response.output.strip().split('\n') if line.strip()]

    branch_name = None
    for line in reversed(output_lines):
        if line in ['```', '```bash', '```text']:
            continue
        if '-issue-' in line and '-asw-' in line:
            branch_name = line
            break

    if not branch_name:
        branch_name = output_lines[-1] if output_lines else response.output.strip()

    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: str,
    asw_id: str,
    logger: logging.Logger,
    working_dir: str,
    cache_enabled: bool = True,
    workflow_type: str = "app",
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.
    Returns (commit_message, error_message) tuple."""
    issue_type = issue_class.replace("/", "")
    unique_agent_name = f"{agent_name}_committer"

    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    if workflow_type == "app":
        request = AppAgentTemplateRequest(
            agent_name=unique_agent_name,
            slash_command="/commit",
            args=[agent_name, issue_type, minimal_issue_json],
            asw_id=asw_id,
            working_dir=working_dir,
            cache_enabled=cache_enabled,
        )
    else:
        request = IOAgentTemplateRequest(
            agent_name=unique_agent_name,
            slash_command="/asw_io_commit",
            args=[agent_name, issue_type, minimal_issue_json],
            asw_id=asw_id,
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
    state,
    logger: logging.Logger,
    working_dir: str,
    workflow_type: str = "app",
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.
    Returns (pr_url, error_message) tuple."""

    if workflow_type == "app":
        plan_file = state.get("plan_file") or "No plan file (test run)"
    else:
        plan_file = state.get("spec_file") or "No spec file (test run)"

    asw_id = state.get("asw_id")

    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        from .data_types import GitHubIssue as GHIssue
        try:
            issue_model = GHIssue(**issue)
            issue_json = issue_model.model_dump_json(
                by_alias=True, include={"number", "title", "body"}
            )
        except Exception:
            issue_json = json.dumps(issue, default=str)
    else:
        issue_json = issue.model_dump_json(
            by_alias=True, include={"number", "title", "body"}
        )

    if workflow_type == "app":
        request = AppAgentTemplateRequest(
            agent_name=AGENT_PR_CREATOR,
            slash_command="/pull_request",
            args=[branch_name, issue_json, plan_file, asw_id],
            asw_id=asw_id,
            working_dir=working_dir,
        )
    else:
        request = IOAgentTemplateRequest(
            agent_name=AGENT_PR_CREATOR,
            slash_command="/asw_io_pull_request",
            args=[branch_name, issue_json, plan_file, asw_id],
            asw_id=asw_id,
            working_dir=working_dir,
        )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def ensure_asw_app_id(
    issue_number: str,
    asw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get app ASW ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create ASW ID for
        asw_id: Optional existing ASW ID to use
        logger: Optional logger instance

    Returns:
        The ASW ID (existing or newly created)
    """
    from .state import ASWAppState
    from .utils import make_asw_app_id

    if asw_id:
        state = ASWAppState.load(asw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ASW App state for ID: {asw_id}")
            else:
                print(f"Found existing ASW App state for ID: {asw_id}")
            return asw_id
        state = ASWAppState(asw_id)
        state.update(asw_id=asw_id, issue_number=issue_number)
        state.save("ensure_asw_app_id")
        if logger:
            logger.info(f"Created new ASW App state for provided ID: {asw_id}")
        else:
            print(f"Created new ASW App state for provided ID: {asw_id}")
        return asw_id

    new_asw_id = make_asw_app_id()
    state = ASWAppState(new_asw_id)
    state.update(asw_id=new_asw_id, issue_number=issue_number)
    state.save("ensure_asw_app_id")
    if logger:
        logger.info(f"Created new ASW App ID and state: {new_asw_id}")
    else:
        print(f"Created new ASW App ID and state: {new_asw_id}")
    return new_asw_id


def ensure_asw_io_id(
    issue_number: str,
    asw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get IO ASW ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create ASW ID for
        asw_id: Optional existing ASW ID to use
        logger: Optional logger instance

    Returns:
        The ASW ID (existing or newly created)
    """
    from .state import ASWIOState
    from .utils import make_asw_io_id

    if asw_id:
        state = ASWIOState.load(asw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ASW IO state for ID: {asw_id}")
            else:
                print(f"Found existing ASW IO state for ID: {asw_id}")
            return asw_id
        state = ASWIOState(asw_id)
        state.update(asw_id=asw_id, issue_number=issue_number)
        state.save("ensure_asw_io_id")
        if logger:
            logger.info(f"Created new ASW IO state for provided ID: {asw_id}")
        else:
            print(f"Created new ASW IO state for provided ID: {asw_id}")
        return asw_id

    new_asw_id = make_asw_io_id()
    state = ASWIOState(new_asw_id)
    state.update(asw_id=new_asw_id, issue_number=issue_number)
    state.save("ensure_asw_io_id")
    if logger:
        logger.info(f"Created new ASW IO ID and state: {new_asw_id}")
    else:
        print(f"Created new ASW IO ID and state: {new_asw_id}")
    return new_asw_id


# Legacy aliases
ensure_adw_id = ensure_asw_app_id
ensure_ipe_id = ensure_asw_io_id


def find_spec_file(state, logger: logging.Logger, workflow_type: str = "app") -> Optional[str]:
    """Find the spec file from state or by examining git diff."""
    worktree_path = state.get("worktree_path")

    if workflow_type == "app":
        spec_file = state.get("plan_file")
    else:
        spec_file = state.get("spec_file")

    if spec_file:
        if worktree_path and not os.path.isabs(spec_file):
            spec_file = os.path.join(worktree_path, spec_file)
        if os.path.exists(spec_file):
            logger.info(f"Using spec file from state: {spec_file}")
            return spec_file

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
            spec_file = spec_files[0]
            if worktree_path:
                spec_file = os.path.join(worktree_path, spec_file)
            logger.info(f"Found spec file: {spec_file}")
            return spec_file

    branch_name = state.get("branch_name")
    if branch_name:
        match = re.search(r"issue-(\d+)", branch_name)
        if match:
            issue_num = match.group(1)
            asw_id = state.get("asw_id")

            search_dir = worktree_path if worktree_path else os.getcwd()
            pattern = os.path.join(
                search_dir, f"specs/issue-{issue_num}-asw-{asw_id}*.md"
            )
            spec_files = glob.glob(pattern)

            if spec_files:
                spec_file = spec_files[0]
                logger.info(f"Found spec file by pattern: {spec_file}")
                return spec_file

    logger.warning("No spec file found")
    return None


def detect_full_deploy(description: str) -> bool:
    """Check if description contains 'full-deploy' keyword."""
    if not description:
        return False
    pattern = r'\bfull[-\s]?deploy\b'
    return bool(re.search(pattern, description, re.IGNORECASE))
