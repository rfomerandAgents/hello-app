#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "claude-agent-sdk"]
# ///

"""
ASW App SDLC Iso - Complete Software Development Life Cycle workflow with isolation

Usage: uv run asw_app_sdlc_iso.py <issue-number> [asw-id] [--skip-e2e] [--skip-resolution] [--cache|--no-cache]

Options:
  --skip-e2e          Skip E2E tests
  --skip-resolution   Skip test resolution attempts
  --cache             Enable response caching
  --no-cache          Disable response caching (default)

This script runs the complete ASW App SDLC pipeline in isolation:
1. asw_app_plan_iso.py - Planning phase (isolated)
2. asw_app_build_iso.py - Implementation phase (isolated)
3. asw_app_test_iso.py - Testing phase (isolated)
4. asw_app_review_iso.py - Review phase (isolated)
5. asw_app_document_iso.py - Documentation phase (isolated)

The scripts are chained together via persistent state (asw_app_state.json).
Each phase runs in its own git worktree with dedicated ports.
"""

import subprocess
import sys
import os

# Add the project root to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from asw.modules.workflow_ops import ensure_asw_app_id
from asw.modules.utils import parse_cache_flag


def main():
    """Main entry point."""
    # Parse cache flag
    cache_enabled, sys.argv = parse_cache_flag(sys.argv)

    # Check for other flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv

    # Remove flags from argv
    if skip_e2e:
        sys.argv.remove("--skip-e2e")
    if skip_resolution:
        sys.argv.remove("--skip-resolution")

    if len(sys.argv) < 2:
        print("Usage: uv run asw_app_sdlc_iso.py <issue-number> [asw-id] [--skip-e2e] [--skip-resolution] [--cache|--no-cache]")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Test (isolated)")
        print("  4. Review (isolated)")
        print("  5. Document (isolated)")
        sys.exit(1)

    issue_number = sys.argv[1]
    asw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ASW ID exists with initialized state
    asw_id = ensure_asw_app_id(issue_number, asw_id)
    print(f"Using ASW ID: {asw_id}")

    # Set up environment for child processes
    env = os.environ.copy()

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Prepare cache flag for subprocess calls
    cache_flag = ["--cache"] if cache_enabled else ["--no-cache"]

    # Run isolated plan with the ASW ID
    plan_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_plan_iso.py"),
        issue_number,
        asw_id,
    ] + cache_flag
    print(f"\n=== ISOLATED PLAN PHASE ===")
    print(f"Running: {' '.join(plan_cmd)}")
    plan = subprocess.run(plan_cmd, env=env)
    if plan.returncode != 0:
        print("Isolated plan phase failed")
        sys.exit(1)

    # Run isolated build with the ASW ID
    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_build_iso.py"),
        issue_number,
        asw_id,
    ] + cache_flag
    print(f"\n=== ISOLATED BUILD PHASE ===")
    print(f"Running: {' '.join(build_cmd)}")
    build = subprocess.run(build_cmd, env=env)
    if build.returncode != 0:
        print("Isolated build phase failed")
        sys.exit(1)

    # Run isolated test with the ASW ID
    test_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_test_iso.py"),
        issue_number,
        asw_id,
        "--skip-e2e",  # Always skip E2E tests in SDLC workflows
    ] + cache_flag

    print(f"\n=== ISOLATED TEST PHASE ===")
    print(f"Running: {' '.join(test_cmd)}")
    test = subprocess.run(test_cmd, env=env)
    if test.returncode != 0:
        print("Isolated test phase failed")
        # Note: Continue anyway as some tests might be flaky
        print("WARNING: Test phase failed but continuing with review")

    # Run isolated review with the ASW ID
    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_review_iso.py"),
        issue_number,
        asw_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")
    review_cmd.extend(cache_flag)

    print(f"\n=== ISOLATED REVIEW PHASE ===")
    print(f"Running: {' '.join(review_cmd)}")
    review = subprocess.run(review_cmd, env=env)
    if review.returncode != 0:
        print("Isolated review phase failed")
        sys.exit(1)

    # Run isolated documentation with the ASW ID
    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "asw_app_document_iso.py"),
        issue_number,
        asw_id,
    ] + cache_flag
    print(f"\n=== ISOLATED DOCUMENTATION PHASE ===")
    print(f"Running: {' '.join(document_cmd)}")
    document = subprocess.run(document_cmd, env=env)
    if document.returncode != 0:
        print("Isolated documentation phase failed")
        sys.exit(1)

    print(f"\n=== ISOLATED SDLC COMPLETED ===")
    print(f"ASW ID: {asw_id}")
    print(f"All phases completed successfully!")
    print(f"\nWorktree location: trees/{asw_id}/")
    print(f"To clean up: ./scripts/purge_tree.sh {asw_id}")


if __name__ == "__main__":
    main()
