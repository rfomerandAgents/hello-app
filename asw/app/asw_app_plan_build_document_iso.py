#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "claude-agent-sdk"]
# ///

"""
ASW App Plan Build Document Iso - Compositional workflow for isolated planning, building, and documentation

Usage: uv run asw_app_plan_build_document_iso.py <issue-number> [asw-id]

This script runs:
1. asw_app_plan_iso.py - Planning phase (isolated)
2. asw_app_build_iso.py - Implementation phase (isolated)
3. asw_app_document_iso.py - Documentation phase (isolated)

The scripts are chained together via persistent state (asw_app_state.json).
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from asw.modules.workflow_ops import ensure_asw_app_id


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run asw_app_plan_build_document_iso.py <issue-number> [asw-id]")
        print("\nThis runs the isolated plan, build, and document workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Document (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_asw_app_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run isolated plan with the ADW ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_plan_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ADW ID
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_build_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated documentation with the ADW ID
    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_document_iso.py"),
        issue_number,
        adw_id,
    ]
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)

    print(f"\n=== ISOLATED WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")


if __name__ == "__main__":
    main()