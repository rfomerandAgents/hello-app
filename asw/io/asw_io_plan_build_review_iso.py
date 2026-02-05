#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "claude-agent-sdk"]
# ///

"""
ASW IO Plan Build Review Iso - Compositional workflow for isolated planning, building, and reviewing

Usage: uv run asw_io_plan_build_review_iso.py <issue-number> [adw-id] [--skip-resolution]

This script runs:
1. asw_io_plan_iso.py - Planning phase (isolated)
2. asw_io_build_iso.py - Implementation phase (isolated)
3. asw_io_review_iso.py - Review phase (isolated)

The scripts are chained together via persistent state (asw_io_state.json).
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from asw.modules.workflow_ops import ensure_asw_io_id


def main():
    """Main entry point."""
    # Check for --skip-resolution flag
    skip_resolution = "--skip-resolution" in sys.argv
    if skip_resolution:
        sys.argv.remove("--skip-resolution")
    
    if len(sys.argv) < 2:
        print("Usage: uv run asw_io_plan_build_review_iso.py <issue-number> [adw-id] [--skip-resolution]")
        print("\nThis runs the isolated plan, build, and review workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Review (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure IPE ID exists with initialized state
    ipe_id = ensure_asw_io_id(issue_number, ipe_id)
    print(f"Using IPE ID: {ipe_id}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run isolated plan with the IPE ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_plan_iso.py"),
        issue_number,
        ipe_id,
    ]
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the IPE ID
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_build_iso.py"),
        issue_number,
        ipe_id,
    ]
    print(f"\n=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated review with the IPE ID
    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_review_iso.py"),
        issue_number,
        ipe_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")
    
    print(f"\n=== ISOLATED REVIEW PHASE ===")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)

    print(f"\n=== ISOLATED WORKFLOW COMPLETED ===")
    print(f"IPE ID: {ipe_id}")
    print(f"All phases completed successfully!")


if __name__ == "__main__":
    main()