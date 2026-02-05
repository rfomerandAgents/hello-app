#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Claude Code Setup Hook: Repository Maintenance

Triggered by: claude --maintenance
Purpose: Run periodic maintenance tasks like dependency updates, security checks,
and cleanup operations.

This hook runs BEFORE the Claude Code session starts, ensuring deterministic
maintenance that can be validated by an agentic prompt afterward.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Log file in the same directory as this script
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "setup.maintenance.log"


class Logger:
    """Simple logger that writes to both stderr and a log file (appends)."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"=== Maintenance Hook Started: {datetime.now().isoformat()} ===\n")
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
        for line in result.stdout.strip().split("\n")[:20]:
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


def check_tool(tool: str) -> bool:
    """Check if a tool is available."""
    try:
        subprocess.run([tool, "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


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

    trigger = hook_input.get("trigger", "maintenance")
    session_id = hook_input.get("session_id", "unknown")

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    logger.log("Claude Code Setup Hook: Running Maintenance")
    logger.log("-" * 60)
    logger.log(f"Trigger: --{trigger}")
    logger.log(f"Session ID: {session_id}")
    logger.log(f"Project directory: {project_dir}")
    logger.log(f"Log file: {LOG_FILE}")

    # Track what we did for the summary
    actions = []
    warnings = []
    updates = []

    # ============================================
    # Python Dependency Updates (uv)
    # ============================================
    pyproject = Path(project_dir) / "pyproject.toml"
    if pyproject.exists() and check_tool("uv"):
        logger.log("\n>>> Updating Python dependencies...")
        
        # Check for outdated packages
        success, output = run(["uv", "pip", "list", "--outdated"], cwd=project_dir, allow_fail=True)
        if success and output.strip():
            outdated_count = len(output.strip().split("\n")) - 1  # Subtract header
            if outdated_count > 0:
                updates.append(f"Python: {outdated_count} packages have updates available")
        
        # Sync to ensure lockfile is up to date
        success, _ = run(["uv", "sync", "--all-extras"], cwd=project_dir, allow_fail=True)
        if success:
            actions.append("Synced Python dependencies")
        else:
            warnings.append("Python uv sync encountered issues")

    # ============================================
    # Node.js Dependency Updates
    # ============================================
    package_json = Path(project_dir) / "package.json"
    if package_json.exists():
        logger.log("\n>>> Checking Node.js dependencies...")
        
        if check_tool("npm"):
            # Check for outdated packages
            success, output = run(["npm", "outdated", "--json"], cwd=project_dir, allow_fail=True)
            if output.strip() and output.strip() != "{}":
                try:
                    outdated = json.loads(output)
                    if outdated:
                        updates.append(f"Node.js: {len(outdated)} packages have updates available")
                except json.JSONDecodeError:
                    pass
            
            # Run audit for security vulnerabilities
            success, output = run(["npm", "audit", "--json"], cwd=project_dir, allow_fail=True)
            try:
                audit = json.loads(output) if output.strip() else {}
                vulns = audit.get("metadata", {}).get("vulnerabilities", {})
                total_vulns = sum(vulns.values()) if isinstance(vulns, dict) else 0
                if total_vulns > 0:
                    warnings.append(f"npm audit found {total_vulns} vulnerabilities")
                else:
                    actions.append("npm audit: no vulnerabilities found")
            except json.JSONDecodeError:
                pass

    # ============================================
    # Git Status Check
    # ============================================
    if check_tool("git"):
        logger.log("\n>>> Checking git status...")
        
        # Check for uncommitted changes
        success, output = run(["git", "status", "--porcelain"], cwd=project_dir, allow_fail=True)
        if output.strip():
            change_count = len(output.strip().split("\n"))
            warnings.append(f"Git: {change_count} uncommitted changes")
        else:
            actions.append("Git: working directory clean")
        
        # Check if we're behind remote
        run(["git", "fetch", "--quiet"], cwd=project_dir, allow_fail=True)
        success, output = run(["git", "rev-list", "--count", "HEAD..@{upstream}"], cwd=project_dir, allow_fail=True)
        if success and output.strip() and int(output.strip()) > 0:
            updates.append(f"Git: {output.strip()} commits behind remote")

    # ============================================
    # Cleanup Stale Files
    # ============================================
    logger.log("\n>>> Checking for stale files...")
    
    stale_patterns = [
        ("*.pyc", "Python bytecode"),
        ("__pycache__", "Python cache directories"),
        (".pytest_cache", "Pytest cache"),
        (".coverage", "Coverage files"),
        ("*.log", "Log files"),
    ]
    
    stale_found = []
    for pattern, description in stale_patterns:
        found = list(Path(project_dir).rglob(pattern))
        found = [p for p in found if not any(x in str(p) for x in ["node_modules", ".git", ".venv"])]
        if found:
            stale_found.append(f"{description}: {len(found)} files")
    
    if stale_found:
        actions.append(f"Found stale files: {', '.join(stale_found)}")

    # ============================================
    # Check Worktrees
    # ============================================
    worktrees_dir = Path(project_dir) / ".worktrees"
    if worktrees_dir.exists():
        logger.log("\n>>> Checking worktrees...")
        worktrees = list(worktrees_dir.iterdir())
        if worktrees:
            actions.append(f"Found {len(worktrees)} active worktrees")

    # ============================================
    # Summary
    # ============================================
    logger.log("\n" + "-" * 60)
    logger.log("Maintenance Complete!")
    logger.log("-" * 60)

    summary = "Maintenance completed!\n\n"
    
    if actions:
        summary += "**Completed:**\n"
        for action in actions:
            summary += f"  - ✓ {action}\n"
    
    if updates:
        summary += "\n**Updates Available:**\n"
        for update in updates:
            summary += f"  - 📦 {update}\n"
    
    if warnings:
        summary += "\n**Warnings:**\n"
        for warning in warnings:
            summary += f"  - ⚠️ {warning}\n"
    
    summary += f"\n**Log file:** {LOG_FILE}\n"
    summary += "\n**Next steps:**\n"
    summary += "  - Review updates and apply as needed\n"
    summary += "  - Address any security warnings\n"
    summary += "  - Check app_docs/maintenance_results.md for details\n"

    hook_output = output_result(summary)

    logger.log("")
    logger.log("HOOK OUTPUT (JSON returned via stdout to Claude Code):")
    logger.log("-" * 60)
    logger.log(json.dumps(hook_output, indent=2))

    # Log completion timestamp
    with open(LOG_FILE, "a") as f:
        f.write(f"\n=== Maintenance Hook Completed: {datetime.now().isoformat()} ===\n")

    # Output the JSON to stdout for Claude Code to consume
    print(json.dumps(hook_output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
