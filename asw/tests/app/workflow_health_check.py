#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
Workflow Health Check - Monitor ADW workflow states and git status

Usage:
    uv run adws/adw_tests/workflow_health_check.py [--auto-fix]

Checks:
1. Main branch working directory is clean
2. No stuck workflows (state files without completed merges)
3. No orphaned worktrees
4. State file integrity
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.git_ops import check_working_directory_clean


class WorkflowHealthIssue(BaseModel):
    """Individual health issue detected."""
    severity: str  # "warning", "error", "critical"
    category: str
    description: str
    adw_id: Optional[str] = None
    auto_fixable: bool = False
    fix_command: Optional[str] = None


class WorkflowHealthReport(BaseModel):
    """Complete health check report."""
    timestamp: str
    healthy: bool
    issues: List[WorkflowHealthIssue]
    stats: Dict[str, Any]


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def check_main_branch_clean() -> List[WorkflowHealthIssue]:
    """Check if main branch has uncommitted changes."""
    issues = []
    project_root = get_project_root()

    is_clean, error, changed_files = check_working_directory_clean(cwd=str(project_root))

    if not is_clean:
        issues.append(WorkflowHealthIssue(
            severity="critical",
            category="working_directory",
            description=f"Main branch has uncommitted changes: {', '.join(changed_files[:5])}{'...' if len(changed_files) > 5 else ''}",
            auto_fixable=False
        ))

    return issues


def check_stuck_workflows() -> List[WorkflowHealthIssue]:
    """Find workflows that haven't completed ship phase."""
    issues = []

    project_root = get_project_root()
    agents_dir = project_root / "agents"

    if not agents_dir.exists():
        return issues

    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        state_file = adw_dir / "adw_state.json"
        if not state_file.exists():
            continue

        # Load state
        try:
            with open(state_file) as f:
                state_data = json.load(f)

            adw_id = state_data.get("adw_id")
            all_adws = state_data.get("all_adws", [])

            # Check if ship workflow completed
            if "adw_ship_iso" not in all_adws:
                # Determine age of workflow
                created_time = adw_dir.stat().st_ctime
                age_hours = (datetime.now().timestamp() - created_time) / 3600

                if age_hours > 24:  # Stuck for more than 24 hours
                    issues.append(WorkflowHealthIssue(
                        severity="warning",
                        category="stuck_workflow",
                        description=f"Workflow {adw_id} has been incomplete for {age_hours:.1f} hours",
                        adw_id=adw_id,
                        auto_fixable=False
                    ))
        except Exception as e:
            issues.append(WorkflowHealthIssue(
                severity="error",
                category="state_integrity",
                description=f"Failed to read state for {adw_dir.name}: {e}",
                adw_id=adw_dir.name,
                auto_fixable=False
            ))

    return issues


def check_orphaned_worktrees() -> List[WorkflowHealthIssue]:
    """Find worktrees without corresponding state files."""
    issues = []

    project_root = get_project_root()
    trees_dir = project_root / "trees"
    agents_dir = project_root / "agents"

    if not trees_dir.exists():
        return issues

    for worktree_dir in trees_dir.iterdir():
        if not worktree_dir.is_dir():
            continue

        adw_id = worktree_dir.name
        state_file = agents_dir / adw_id / "adw_state.json"

        if not state_file.exists():
            issues.append(WorkflowHealthIssue(
                severity="warning",
                category="orphaned_worktree",
                description=f"Worktree exists without state file: {adw_id}",
                adw_id=adw_id,
                auto_fixable=True,
                fix_command=f"./scripts/purge_tree.sh {adw_id}"
            ))

    return issues


def check_git_worktrees() -> List[WorkflowHealthIssue]:
    """Check for stale git worktrees."""
    issues = []
    project_root = get_project_root()

    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )

        if result.returncode == 0:
            # Parse worktree list
            worktrees = []
            current_worktree = {}

            for line in result.stdout.split("\n"):
                if line.startswith("worktree "):
                    if current_worktree:
                        worktrees.append(current_worktree)
                    current_worktree = {"path": line[9:]}
                elif line.startswith("branch "):
                    current_worktree["branch"] = line[7:]
                elif line.startswith("HEAD "):
                    current_worktree["head"] = line[5:]
                elif line == "prunable":
                    current_worktree["prunable"] = True

            if current_worktree:
                worktrees.append(current_worktree)

            # Check for prunable worktrees
            for wt in worktrees:
                if wt.get("prunable"):
                    issues.append(WorkflowHealthIssue(
                        severity="warning",
                        category="stale_worktree",
                        description=f"Stale git worktree: {wt.get('path', 'unknown')}",
                        auto_fixable=True,
                        fix_command="git worktree prune"
                    ))

    except Exception as e:
        issues.append(WorkflowHealthIssue(
            severity="error",
            category="git_error",
            description=f"Failed to check git worktrees: {e}",
            auto_fixable=False
        ))

    return issues


def run_health_check(auto_fix: bool = False) -> WorkflowHealthReport:
    """Run all health checks."""
    all_issues = []

    # Run checks
    all_issues.extend(check_main_branch_clean())
    all_issues.extend(check_stuck_workflows())
    all_issues.extend(check_orphaned_worktrees())
    all_issues.extend(check_git_worktrees())

    # Calculate stats
    stats = {
        "total_issues": len(all_issues),
        "critical": len([i for i in all_issues if i.severity == "critical"]),
        "errors": len([i for i in all_issues if i.severity == "error"]),
        "warnings": len([i for i in all_issues if i.severity == "warning"]),
        "auto_fixable": len([i for i in all_issues if i.auto_fixable])
    }

    # Auto-fix if requested
    if auto_fix:
        for issue in all_issues:
            if issue.auto_fixable and issue.fix_command:
                print(f"Auto-fixing: {issue.description}")
                print(f"Running: {issue.fix_command}")
                try:
                    subprocess.run(
                        issue.fix_command,
                        shell=True,
                        cwd=str(get_project_root())
                    )
                except Exception as e:
                    print(f"  Failed: {e}")

    return WorkflowHealthReport(
        timestamp=datetime.now().isoformat(),
        healthy=stats["critical"] == 0 and stats["errors"] == 0,
        issues=all_issues,
        stats=stats
    )


def main():
    auto_fix = "--auto-fix" in sys.argv
    json_output = "--json" in sys.argv

    print("Running Workflow Health Check...")
    report = run_health_check(auto_fix=auto_fix)

    if json_output:
        print(report.model_dump_json(indent=2))
        sys.exit(0 if report.healthy else 1)

    # Print report
    status_emoji = "HEALTHY" if report.healthy else "UNHEALTHY"
    print(f"\nStatus: {status_emoji}")
    print(f"Timestamp: {report.timestamp}")
    print(f"\nStatistics:")
    for key, value in report.stats.items():
        print(f"  {key}: {value}")

    if report.issues:
        print(f"\nIssues Found:")
        for issue in report.issues:
            severity_marker = {"critical": "[CRITICAL]", "error": "[ERROR]", "warning": "[WARNING]"}[issue.severity]
            print(f"\n{severity_marker} [{issue.category}] {issue.description}")
            if issue.auto_fixable:
                print(f"   Fix: {issue.fix_command}")

    # Exit with appropriate code
    sys.exit(0 if report.healthy else 1)


if __name__ == "__main__":
    main()
