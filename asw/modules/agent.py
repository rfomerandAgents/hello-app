"""Claude Code agent module for executing prompts programmatically.

Supports both application (app) and infrastructure (io) workflows.
"""

import subprocess
import sys
import os
import json
import re
import logging
import time
from typing import Optional, List, Dict, Any, Tuple, Final
from dotenv import load_dotenv
from .data_types import (
    AgentPromptResponse,
    AppAgentPromptRequest,
    AppAgentTemplateRequest,
    IOAgentPromptRequest,
    IOAgentTemplateRequest,
    AppSlashCommand,
    IOSlashCommand,
    ModelSet,
    RetryCode,
)
from .cache import (
    create_fingerprint,
    load_cache_entry,
    save_cache_entry,
    CacheEntry,
)

# Load environment variables
load_dotenv()

# Get Claude Code CLI path from environment
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")

# Model selection mapping for app slash commands
APP_SLASH_COMMAND_MODEL_MAP: Final[Dict[AppSlashCommand, Dict[ModelSet, str]]] = {
    "/classify_issue": {"base": "sonnet", "heavy": "opus"},
    "/classify_asw_app": {"base": "sonnet", "heavy": "opus"},
    "/generate_branch_name": {"base": "sonnet", "heavy": "opus"},
    "/implement": {"base": "sonnet", "heavy": "opus"},
    "/test": {"base": "sonnet", "heavy": "opus"},
    "/resolve_failed_test": {"base": "sonnet", "heavy": "opus"},
    "/test_e2e": {"base": "sonnet", "heavy": "opus"},
    "/resolve_failed_e2e_test": {"base": "sonnet", "heavy": "opus"},
    "/review": {"base": "sonnet", "heavy": "opus"},
    "/document": {"base": "sonnet", "heavy": "opus"},
    "/commit": {"base": "sonnet", "heavy": "opus"},
    "/pull_request": {"base": "sonnet", "heavy": "opus"},
    "/chore": {"base": "sonnet", "heavy": "opus"},
    "/bug": {"base": "sonnet", "heavy": "opus"},
    "/feature": {"base": "sonnet", "heavy": "opus"},
    "/patch": {"base": "sonnet", "heavy": "opus"},
    "/install_worktree": {"base": "sonnet", "heavy": "opus"},
    "/track_agentic_kpis": {"base": "sonnet", "heavy": "opus"},
}

# Model selection mapping for IO slash commands
IO_SLASH_COMMAND_MODEL_MAP: Final[Dict[IOSlashCommand, Dict[ModelSet, str]]] = {
    "/classify_asw_io": {"base": "sonnet", "heavy": "opus"},
    "/generate_branch_name": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_build": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_test": {"base": "sonnet", "heavy": "opus"},
    "/resolve_failed_test": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_review": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_document": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_commit": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_pull_request": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_chore": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_bug": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_feature": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_patch": {"base": "sonnet", "heavy": "opus"},
    "/install_worktree": {"base": "sonnet", "heavy": "opus"},
    "/asw_io_track_agentic_kpis": {"base": "sonnet", "heavy": "opus"},
}


def get_model_for_app_command(
    request: AppAgentTemplateRequest, default: str = "sonnet"
) -> str:
    """Get the appropriate model for an app template request.

    Args:
        request: The template request containing the slash command and asw_id
        default: Default model if not found in mapping

    Returns:
        Model name to use (e.g., "sonnet" or "opus")
    """
    from .state import ASWAppState

    # Load state to get model_set
    model_set: ModelSet = "base"  # Default model set
    state = ASWAppState.load(request.asw_id)
    if state:
        model_set = state.get("model_set", "base")

    # Get the model configuration for the command
    command_config = APP_SLASH_COMMAND_MODEL_MAP.get(request.slash_command)

    if command_config:
        return command_config.get(model_set, command_config.get("base", default))

    return default


def get_model_for_io_command(
    request: IOAgentTemplateRequest, default: str = "sonnet"
) -> str:
    """Get the appropriate model for an IO template request.

    Args:
        request: The template request containing the slash command and asw_id
        default: Default model if not found in mapping

    Returns:
        Model name to use (e.g., "sonnet" or "opus")
    """
    from .state import ASWIOState

    # Load state to get model_set
    model_set: ModelSet = "base"  # Default model set
    state = ASWIOState.load(request.asw_id)
    if state:
        model_set = state.get("model_set", "base")

    # Get the model configuration for the command
    command_config = IO_SLASH_COMMAND_MODEL_MAP.get(request.slash_command)

    if command_config:
        return command_config.get(model_set, command_config.get("base", default))

    return default


def truncate_output(
    output: str, max_length: int = 500, suffix: str = "... (truncated)"
) -> str:
    """Truncate output to a reasonable length for display.

    Special handling for JSONL data - if the output appears to be JSONL,
    try to extract just the meaningful part.
    """
    # Check if this looks like JSONL data
    if output.startswith('{"type":') and '\n{"type":' in output:
        lines = output.strip().split("\n")
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "result":
                    result = data.get("result", "")
                    if result:
                        return truncate_output(result, max_length, suffix)
                elif data.get("type") == "assistant" and data.get("message"):
                    content = data["message"].get("content", [])
                    if isinstance(content, list) and content:
                        text = content[0].get("text", "")
                        if text:
                            return truncate_output(text, max_length, suffix)
            except:
                pass
        return f"[JSONL output with {len(lines)} messages]{suffix}"

    if len(output) <= max_length:
        return output

    truncate_at = max_length - len(suffix)
    newline_pos = output.rfind("\n", truncate_at - 50, truncate_at)
    if newline_pos > 0:
        return output[:newline_pos] + suffix

    space_pos = output.rfind(" ", truncate_at - 20, truncate_at)
    if space_pos > 0:
        return output[:space_pos] + suffix

    return output[:truncate_at] + suffix


def check_claude_installed() -> Optional[str]:
    """Check if Claude Code CLI is installed. Return error message if not."""
    try:
        result = subprocess.run(
            [CLAUDE_PATH, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    except FileNotFoundError:
        return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    return None


def parse_jsonl_output(
    output_file: str,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse JSONL output file and return all messages and the result message."""
    try:
        with open(output_file, "r") as f:
            messages = [json.loads(line) for line in f if line.strip()]
            result_message = None
            for message in reversed(messages):
                if message.get("type") == "result":
                    result_message = message
                    break
            return messages, result_message
    except Exception as e:
        return [], None


def convert_jsonl_to_json(jsonl_file: str) -> str:
    """Convert JSONL file to JSON array file."""
    json_file = jsonl_file.replace(".jsonl", ".json")
    messages, _ = parse_jsonl_output(jsonl_file)
    with open(json_file, "w") as f:
        json.dump(messages, f, indent=2)
    return json_file


def get_claude_env() -> Dict[str, str]:
    """Get only the required environment variables for Claude Code execution."""
    from .utils import get_safe_subprocess_env
    return get_safe_subprocess_env()


def save_prompt(prompt: str, asw_id: str, agent_name: str = "ops") -> None:
    """Save a prompt to the appropriate logging directory."""
    match = re.match(r"^(/\w+)", prompt)
    if not match:
        return

    slash_command = match.group(1)
    command_name = slash_command[1:]

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompt_dir = os.path.join(project_root, "agents", asw_id, agent_name, "prompts")
    os.makedirs(prompt_dir, exist_ok=True)

    prompt_file = os.path.join(prompt_dir, f"{command_name}.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)


def prompt_claude_code_with_retry(
    request,
    max_retries: int = 3,
    retry_delays: List[int] = None,
) -> AgentPromptResponse:
    """Execute Claude Code with retry logic for certain error types."""
    if retry_delays is None:
        retry_delays = [1, 3, 5]

    while len(retry_delays) < max_retries:
        retry_delays.append(retry_delays[-1] + 2)

    last_response = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            delay = retry_delays[attempt - 1]
            time.sleep(delay)

        response = prompt_claude_code(request)
        last_response = response

        if response.success or response.retry_code == RetryCode.NONE:
            return response

        if response.retry_code in [
            RetryCode.CLAUDE_CODE_ERROR,
            RetryCode.TIMEOUT_ERROR,
            RetryCode.EXECUTION_ERROR,
            RetryCode.ERROR_DURING_EXECUTION,
        ]:
            if attempt < max_retries:
                continue
            else:
                return response

    return last_response


def prompt_claude_code(request) -> AgentPromptResponse:
    """Execute Claude Code with the given prompt configuration.

    Accepts either AppAgentPromptRequest or IOAgentPromptRequest.
    """
    error_msg = check_claude_installed()
    if error_msg:
        return AgentPromptResponse(
            output=error_msg,
            success=False,
            session_id=None,
            retry_code=RetryCode.NONE,
            duration_ms=None,
        )

    # Get asw_id from request (works for both App and IO requests)
    asw_id = request.asw_id
    save_prompt(request.prompt, asw_id, request.agent_name)

    # Check cache if enabled (only for app requests with caching)
    logger = logging.getLogger(f"asw_{asw_id}")
    cache_enabled = getattr(request, 'cache_enabled', False)

    if cache_enabled:
        fingerprint = create_fingerprint(
            prompt=request.prompt,
            model=request.model,
            working_dir=request.working_dir,
            slash_command=None,
        )
        cached = load_cache_entry(asw_id, fingerprint)
        if cached:
            age_seconds = int(time.time() - cached.created_at)
            age_minutes = age_seconds // 60
            logger.info(f"Cache HIT for fingerprint {fingerprint[:8]}... (age: {age_minutes}m {age_seconds % 60}s)")
            return AgentPromptResponse(
                output=cached.response_output,
                success=cached.response_success,
                session_id=cached.response_session_id,
                retry_code=RetryCode.NONE,
                duration_ms=None,
            )
        else:
            logger.debug(f"Cache MISS for fingerprint {fingerprint[:8]}...")

    # Create output directory if needed
    output_dir = os.path.dirname(request.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Build command
    cmd = [CLAUDE_PATH, "-p", request.prompt]
    cmd.extend(["--model", request.model])
    cmd.extend(["--output-format", "stream-json"])
    cmd.append("--verbose")

    # Check for MCP config in working directory
    if request.working_dir:
        mcp_config_path = os.path.join(request.working_dir, ".mcp.json")
        if os.path.exists(mcp_config_path):
            cmd.extend(["--mcp-config", mcp_config_path])

    if request.dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    env = get_claude_env()

    try:
        with open(request.output_file, "w") as output_f:
            result = subprocess.run(
                cmd,
                stdout=output_f,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=request.working_dir,
            )

        if result.returncode == 0:
            messages, result_message = parse_jsonl_output(request.output_file)
            json_file = convert_jsonl_to_json(request.output_file)

            if result_message:
                session_id = result_message.get("session_id")
                duration_ms = result_message.get("duration_ms")
                is_error = result_message.get("is_error", False)
                subtype = result_message.get("subtype", "")

                if subtype == "error_during_execution":
                    return AgentPromptResponse(
                        output="Error during execution: Agent encountered an error and did not return a result",
                        success=False,
                        session_id=session_id,
                        retry_code=RetryCode.ERROR_DURING_EXECUTION,
                        duration_ms=duration_ms,
                    )

                result_text = result_message.get("result", "")
                if is_error and len(result_text) > 1000:
                    result_text = truncate_output(result_text, max_length=800)

                response = AgentPromptResponse(
                    output=result_text,
                    success=not is_error,
                    session_id=session_id,
                    retry_code=RetryCode.NONE,
                    duration_ms=duration_ms,
                )

                # Save to cache if enabled and successful
                if cache_enabled and response.success:
                    fingerprint = create_fingerprint(
                        prompt=request.prompt,
                        model=request.model,
                        working_dir=request.working_dir,
                        slash_command=None,
                    )
                    cache_entry = CacheEntry(
                        fingerprint=fingerprint,
                        response_output=response.output,
                        response_success=response.success,
                        response_session_id=response.session_id,
                        created_at=time.time(),
                        ttl_seconds=getattr(request, 'cache_ttl_seconds', 172800),
                        prompt_preview=request.prompt[:100],
                        model=request.model,
                        slash_command=None,
                    )
                    save_cache_entry(asw_id, cache_entry)
                    logger.debug(f"Saved response to cache (fingerprint: {fingerprint[:8]}...)")

                return response
            else:
                error_msg = "No result message found in Claude Code output"
                try:
                    with open(request.output_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            last_lines = lines[-5:] if len(lines) > 5 else lines
                            for line in reversed(last_lines):
                                try:
                                    data = json.loads(line.strip())
                                    if data.get("type") == "assistant" and data.get("message"):
                                        content = data["message"].get("content", [])
                                        if isinstance(content, list) and content:
                                            text = content[0].get("text", "")
                                            if text:
                                                error_msg = f"Claude Code output: {text[:500]}"
                                                break
                                except:
                                    pass
                except:
                    pass

                return AgentPromptResponse(
                    output=truncate_output(error_msg, max_length=800),
                    success=False,
                    session_id=None,
                    retry_code=RetryCode.NONE,
                    duration_ms=None,
                )
        else:
            stderr_msg = result.stderr.strip() if result.stderr else ""
            stdout_msg = ""
            error_from_jsonl = None

            try:
                if os.path.exists(request.output_file):
                    messages, result_message = parse_jsonl_output(request.output_file)
                    if result_message and result_message.get("is_error"):
                        error_from_jsonl = result_message.get("result", "Unknown error")
                    elif messages:
                        for msg in reversed(messages[-5:]):
                            if msg.get("type") == "assistant" and msg.get("message", {}).get("content"):
                                content = msg["message"]["content"]
                                if isinstance(content, list) and content:
                                    text = content[0].get("text", "")
                                    if text and ("error" in text.lower() or "failed" in text.lower()):
                                        error_from_jsonl = text[:500]
                                        break

                    if not error_from_jsonl:
                        with open(request.output_file, "r") as f:
                            lines = f.readlines()
                            if lines:
                                stdout_msg = lines[-1].strip()[:200]
            except:
                pass

            if error_from_jsonl:
                error_msg = f"Claude Code error: {error_from_jsonl}"
            elif stdout_msg and not stderr_msg:
                error_msg = f"Claude Code error: {stdout_msg}"
            elif stderr_msg and not stdout_msg:
                error_msg = f"Claude Code error: {stderr_msg}"
            elif stdout_msg and stderr_msg:
                error_msg = f"Claude Code error: {stderr_msg}\nStdout: {stdout_msg}"
            else:
                error_msg = f"Claude Code error: Command failed with exit code {result.returncode}"

            return AgentPromptResponse(
                output=truncate_output(error_msg, max_length=800),
                success=False,
                session_id=None,
                retry_code=RetryCode.CLAUDE_CODE_ERROR,
                duration_ms=None,
            )

    except subprocess.TimeoutExpired:
        return AgentPromptResponse(
            output="Error: Claude Code command timed out after 5 minutes",
            success=False,
            session_id=None,
            retry_code=RetryCode.TIMEOUT_ERROR,
            duration_ms=None,
        )
    except Exception as e:
        return AgentPromptResponse(
            output=f"Error executing Claude Code: {e}",
            success=False,
            session_id=None,
            retry_code=RetryCode.EXECUTION_ERROR,
            duration_ms=None,
        )


def execute_template(request) -> AgentPromptResponse:
    """Execute a Claude Code template with slash command and arguments.

    Accepts either AppAgentTemplateRequest or IOAgentTemplateRequest.
    Automatically selects the appropriate model based on the slash command
    and the model_set stored in the ASW state.
    """
    # Determine if this is an app or io request based on type
    is_app_request = isinstance(request, AppAgentTemplateRequest)

    # Get the appropriate model for this request
    if is_app_request:
        mapped_model = get_model_for_app_command(request)
    else:
        mapped_model = get_model_for_io_command(request)

    request = request.model_copy(update={"model": mapped_model})

    # Construct prompt from slash command and args
    prompt = f"{request.slash_command} {' '.join(request.args)}"

    # Create output directory with asw_id at project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    output_dir = os.path.join(
        project_root, "agents", request.asw_id, request.agent_name
    )
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "raw_output.jsonl")

    # Create prompt request with specific parameters
    if is_app_request:
        prompt_request = AppAgentPromptRequest(
            prompt=prompt,
            asw_id=request.asw_id,
            agent_name=request.agent_name,
            model=request.model,
            dangerously_skip_permissions=True,
            output_file=output_file,
            working_dir=request.working_dir,
            cache_enabled=request.cache_enabled,
            cache_ttl_seconds=request.cache_ttl_seconds,
        )
    else:
        prompt_request = IOAgentPromptRequest(
            prompt=prompt,
            asw_id=request.asw_id,
            agent_name=request.agent_name,
            model=request.model,
            dangerously_skip_permissions=True,
            output_file=output_file,
            working_dir=request.working_dir,
        )

    return prompt_claude_code_with_retry(prompt_request)
