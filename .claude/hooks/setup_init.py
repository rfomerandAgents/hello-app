#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Claude Code Setup Hook: Repository Initialization

Triggered by: claude --init or claude --init-only
Purpose: Install dependencies and initialize the codebase for first-time setup

This hook runs BEFORE the Claude Code session starts, ensuring deterministic
setup that can be validated by an agentic prompt afterward.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Log file in the same directory as this script
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "setup.init.log"


class Logger:
    """Simple logger that writes to both stderr and a log file (appends)."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Append to log file (preserves history)
        with open(self.log_path, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"=== Init Hook Started: {datetime.now().isoformat()} ===\n")
            f.write(f"{'='*60}\n")

    def log(self, message: str) -> None:
        """Print to stderr and append to log file."""
        print(message, file=sys.stderr)
        with open(self.log_path, "a") as f:
            f.write(message + "\n")


logger = Logger(LOG_FILE)


def read_hook_input() -> dict:
    """Read the JSON payload from stdin."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return {}


def output_result(context: str) -> dict:
    """Build and return structured JSON result."""
    return {
        "hookSpecificOutput": {"hookEventName": "Setup", "additionalContext": context}
    }


def run(cmd: list[str], cwd: str | None = None, allow_fail: bool = False) -> tuple[bool, str]:
    """Run a command, log output. Returns (success, output)."""
    logger.log(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    output_lines = []
    if result.stdout:
        for line in result.stdout.strip().split("\n")[:10]:
            logger.log(f"    {line}")
            output_lines.append(line)

    if result.returncode != 0:
        logger.log(f"  ERROR: Command failed with code {result.returncode}")
        if result.stderr:
            logger.log(f"  STDERR: {result.stderr[:500]}")
        if not allow_fail:
            return False, result.stderr or "Command failed"
        return False, "\n".join(output_lines)

    return True, "\n".join(output_lines)


def check_tool(tool: str) -> tuple[bool, str]:
    """Check if a tool is available and return its version."""
    try:
        result = subprocess.run([tool, "--version"], capture_output=True, text=True)
        version = result.stdout.strip().split("\n")[0] if result.stdout else "installed"
        return True, version
    except FileNotFoundError:
        return False, "not found"


def main() -> None:
    # ============================================
    # Read and log INPUT from Claude Code
    # ============================================
    hook_input = read_hook_input()

    logger.log("")
    logger.log("HOOK INPUT (JSON received via stdin from Claude Code):")
    logger.log("-" * 60)
    logger.log(json.dumps(hook_input, indent=2) if hook_input else "{}")
    logger.log("")

    trigger = hook_input.get("trigger", "init")
    session_id = hook_input.get("session_id", "unknown")

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    env_file = os.environ.get("CLAUDE_ENV_FILE")

    logger.log("Claude Code Setup Hook: Initializing Repository")
    logger.log("-" * 60)
    logger.log(f"Trigger: --{trigger}")
    logger.log(f"Session ID: {session_id}")
    logger.log(f"Project directory: {project_dir}")
    logger.log(f"Log file: {LOG_FILE}")

    # Track what we did for the summary
    actions = []
    warnings = []
    errors = []

    # ============================================
    # Check Available Tools
    # ============================================
    logger.log("\n>>> Checking available tools...")
    
    tools_status = {}
    for tool in ["uv", "python3", "node", "npm", "bun", "terraform", "packer", "git"]:
        available, version = check_tool(tool)
        tools_status[tool] = {"available": available, "version": version}
        if available:
            logger.log(f"  ✓ {tool}: {version}")
        else:
            logger.log(f"  ✗ {tool}: not found")
    
    actions.append(f"Checked tools: {sum(1 for t in tools_status.values() if t['available'])}/{len(tools_status)} available")

    # ============================================
    # Python Setup (uv)
    # ============================================
    pyproject = Path(project_dir) / "pyproject.toml"
    if pyproject.exists() and tools_status["uv"]["available"]:
        logger.log("\n>>> Setting up Python environment with uv...")
        success, _ = run(["uv", "sync", "--all-extras"], cwd=project_dir, allow_fail=True)
        if success:
            actions.append("Installed Python dependencies with uv")
        else:
            warnings.append("Python uv sync failed - may need manual setup")
    elif pyproject.exists():
        warnings.append("pyproject.toml found but uv not available")

    # ============================================
    # Node.js Setup (npm/bun)
    # ============================================
    package_json = Path(project_dir) / "package.json"
    if package_json.exists():
        if tools_status["bun"]["available"]:
            logger.log("\n>>> Setting up Node.js environment with bun...")
            success, _ = run(["bun", "install"], cwd=project_dir, allow_fail=True)
            if success:
                actions.append("Installed Node.js dependencies with bun")
            else:
                warnings.append("Bun install failed")
        elif tools_status["npm"]["available"]:
            logger.log("\n>>> Setting up Node.js environment with npm...")
            success, _ = run(["npm", "install"], cwd=project_dir, allow_fail=True)
            if success:
                actions.append("Installed Node.js dependencies with npm")
            else:
                warnings.append("npm install failed")
        else:
            warnings.append("package.json found but neither bun nor npm available")

    # ============================================
    # Discover Project Structure
    # ============================================
    logger.log("\n>>> Discovering project structure...")
    
    # Find subprojects
    subprojects = []
    for pattern, proj_type in [
        ("**/package.json", "node"),
        ("**/pyproject.toml", "python"),
        ("**/*.tf", "terraform"),
        ("**/*.pkr.hcl", "packer"),
    ]:
        found = list(Path(project_dir).glob(pattern))
        # Exclude node_modules, .git, .worktrees
        found = [p for p in found if not any(x in str(p) for x in ["node_modules", ".git", ".worktrees", ".terraform"])]
        for f in found[:5]:  # Limit to 5 per type
            subprojects.append({"type": proj_type, "path": str(f.relative_to(project_dir))})
    
    if subprojects:
        logger.log(f"  Found {len(subprojects)} subproject files")
        actions.append(f"Discovered {len(subprojects)} subproject configurations")

    # ============================================
    # Setup environment variables for Claude session
    # ============================================
    if env_file:
        logger.log("\n>>> Setting up session environment variables...")
        with open(env_file, "a") as f:
            f.write(f"export PROJECT_ROOT={project_dir}\n")
        actions.append("Set PROJECT_ROOT environment variable")

    # ============================================
    # Summary
    # ============================================
    logger.log("\n" + "-" * 60)
    logger.log("Setup Complete!")
    logger.log("-" * 60)

    summary = "Setup completed!\n\n"
    
    if actions:
        summary += "**What was done:**\n"
        for action in actions:
            summary += f"  - {action}\n"
    
    if warnings:
        summary += "\n**Warnings:**\n"
        for warning in warnings:
            summary += f"  - ⚠️ {warning}\n"
    
    if errors:
        summary += "\n**Errors:**\n"
        for error in errors:
            summary += f"  - ❌ {error}\n"
    
    summary += "\n**Available Tools:**\n"
    for tool, status in tools_status.items():
        icon = "✓" if status["available"] else "✗"
        summary += f"  {icon} {tool}: {status['version']}\n"
    
    summary += f"\n**Log file:** {LOG_FILE}\n"
    summary += "\n**Next steps:**\n"
    summary += "  - Run `/prime` to load project context\n"
    summary += "  - Check app_docs/install_results.md for details\n"

    hook_output = output_result(summary)

    logger.log("")
    logger.log("HOOK OUTPUT (JSON returned via stdout to Claude Code):")
    logger.log("-" * 60)
    logger.log(json.dumps(hook_output, indent=2))

    # Log completion timestamp
    with open(LOG_FILE, "a") as f:
        f.write(f"\n=== Init Hook Completed: {datetime.now().isoformat()} ===\n")

    # Output the JSON to stdout for Claude Code to consume
    print(json.dumps(hook_output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
