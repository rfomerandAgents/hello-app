#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "claude-agent-sdk"]
# ///

"""
ASW IO SDLC Iso - Complete Infrastructure Development Life Cycle workflow with isolation

Usage: uv run asw_io_sdlc_iso.py <issue-number> [asw-id] [environment]

This script runs the complete ASW IO SDLC pipeline in isolation:
1. asw_io_plan_iso.py - Planning phase (isolated)
2. asw_io_build_iso.py - Implementation phase (isolated)
3. asw_io_test_iso.py - Validation phase (isolated terraform validate/plan)
4. asw_io_review_iso.py - Review phase (isolated)
5. asw_io_document_iso.py - Documentation phase (isolated)

The scripts are chained together via persistent state (asw_io_state.json).
Each phase runs in its own git worktree for the specified environment.

BEHAVIORAL DIFFERENCES FROM ADW:
- No E2E tests (infrastructure doesn't have E2E tests)
- Uses terraform validate/plan instead of pytest
- No port allocation (infrastructure vs application)
- Requires environment parameter (dev/staging/prod)
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'ipe'))

from ipe.ipe_modules.ipe_workflow_ops import ensure_ipe_id


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run asw_io_sdlc_iso.py <issue-number> [asw-id] [environment]")
        print("\nThis runs the complete isolated Infrastructure Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Validate (isolated)")
        print("  4. Review (isolated)")
        print("  5. Document (isolated)")
        print("\nArguments:")
        print("  issue-number: GitHub issue number (required)")
        print("  ipe-id: IPE workflow ID (optional, will be generated if not provided)")
        print("  environment: Target environment - dev/staging/prod/sandbox (optional, defaults to 'sandbox')")
        sys.exit(1)

    issue_number = sys.argv[1]
    ipe_id = sys.argv[2] if len(sys.argv) > 2 else None
    environment = sys.argv[3] if len(sys.argv) > 3 else "sandbox"

    # Validate environment
    valid_environments = ["dev", "staging", "prod", "sandbox"]
    if environment not in valid_environments:
        print(f"Error: Invalid environment '{environment}'")
        print(f"Must be one of: {', '.join(valid_environments)}")
        sys.exit(1)

    # Ensure IPE ID exists with initialized state
    ipe_id = ensure_asw_io_id(issue_number, ipe_id)
    print(f"Using IPE ID: {ipe_id}")
    print(f"Target environment: {environment}")

    # Set up environment for child processes
    env = os.environ.copy()

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run isolated plan with the IPE ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_plan_iso.py"),
        issue_number,
        ipe_id,
        environment,
    ]
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd, env=env)
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
    build = subprocess.run(build_cmd, env=env)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated validation with the IPE ID
    test_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_test_iso.py"),
        issue_number,
        ipe_id,
    ]

    print(f"\n=== ISOLATED VALIDATION PHASE ===")
    print(f"Running: {' '.join(test_cmd)}")
    test = subprocess.run(test_cmd, env=env)
    if test.returncode != 0:
        print("Isolated validation phase failed")
        # Note: Continue anyway as some validations might be warnings
        print("WARNING: Validation phase failed but continuing with review")

    # Run isolated review with the IPE ID
    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_review_iso.py"),
        issue_number,
        ipe_id,
    ]
    print(f"\n=== ISOLATED REVIEW PHASE ===")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd, env=env)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)

    # Run isolated documentation with the IPE ID
    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_io_document_iso.py"),
        issue_number,
        ipe_id,
    ]
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd, env=env)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)

    print(f"\n=== ISOLATED SDLC COMPLETED ===")
    print(f"IPE ID: {ipe_id}")
    print(f"Environment: {environment}")
    print(f"All phases completed!")
    print(f"\nWorktree location: trees/{ipe_id}/")
    print(f"To clean up: ./scripts/purge_tree.sh {ipe_id}")


if __name__ == "__main__":
    main()
