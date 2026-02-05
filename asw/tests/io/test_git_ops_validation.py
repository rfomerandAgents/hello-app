#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest", "python-dotenv"]
# ///

"""
Unit tests for git operations validation functions.

Tests:
- Working directory status check
- Stash/unstash operations
- Merge conflict detection
- Pre-merge validation
"""

import pytest
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.git_ops import (
    check_working_directory_clean,
    stash_changes,
    unstash_changes,
    check_merge_conflicts,
    validate_pre_merge
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)

    # Create initial commit
    test_file = Path(temp_dir) / "README.md"
    test_file.write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True, capture_output=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_check_working_directory_clean_on_clean_repo(temp_git_repo):
    """Test that clean directory is correctly detected."""
    is_clean, error, files = check_working_directory_clean(cwd=temp_git_repo)

    assert is_clean is True
    assert error is None
    assert len(files) == 0


def test_check_working_directory_dirty_with_modifications(temp_git_repo):
    """Test detection of modified files."""
    # Modify a file
    readme = Path(temp_git_repo) / "README.md"
    readme.write_text("# Modified")

    is_clean, error, files = check_working_directory_clean(cwd=temp_git_repo)

    assert is_clean is False
    assert "README.md" in files


def test_check_working_directory_dirty_with_untracked(temp_git_repo):
    """Test detection of untracked files."""
    # Add new file
    new_file = Path(temp_git_repo) / "new.txt"
    new_file.write_text("New file")

    is_clean, error, files = check_working_directory_clean(cwd=temp_git_repo)

    assert is_clean is False
    assert "new.txt" in files


def test_stash_and_unstash_changes(temp_git_repo):
    """Test stashing and restoring changes."""
    # Create modification
    readme = Path(temp_git_repo) / "README.md"
    readme.write_text("# Modified")

    # Stash
    success, error, stash_id = stash_changes(
        message="Test stash",
        cwd=temp_git_repo
    )

    assert success is True
    assert stash_id is not None

    # Verify working directory is clean
    is_clean, _, _ = check_working_directory_clean(cwd=temp_git_repo)
    assert is_clean is True

    # Unstash
    success, error = unstash_changes(
        stash_id=stash_id,
        cwd=temp_git_repo
    )

    assert success is True
    assert readme.read_text() == "# Modified"


def test_stash_no_changes(temp_git_repo):
    """Test stashing when there are no changes."""
    success, error, stash_id = stash_changes(
        message="Empty stash",
        cwd=temp_git_repo
    )

    assert success is True
    assert stash_id is None  # No stash created


def test_unstash_empty_stash(temp_git_repo):
    """Test unstashing when stash is empty."""
    success, error = unstash_changes(cwd=temp_git_repo)

    # Should succeed (no-op)
    assert success is True


def test_merge_conflict_detection_no_conflicts(temp_git_repo):
    """Test that clean merges are detected correctly."""
    # Create feature branch with non-conflicting change
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=temp_git_repo, check=True, capture_output=True)

    new_file = Path(temp_git_repo) / "feature.txt"
    new_file.write_text("Feature content")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Feature change"], cwd=temp_git_repo, check=True, capture_output=True)

    # Switch back to main (need to use master on old git, main on new)
    result = subprocess.run(["git", "branch", "-l", "main"], cwd=temp_git_repo, capture_output=True, text=True)
    main_branch = "main" if "main" in result.stdout else "master"
    subprocess.run(["git", "checkout", main_branch], cwd=temp_git_repo, check=True, capture_output=True)

    # Check for conflicts
    has_conflicts, error, files = check_merge_conflicts(
        branch_name="feature",
        target_branch=main_branch,
        cwd=temp_git_repo
    )

    assert has_conflicts is False


def test_merge_conflict_detection_with_conflicts(temp_git_repo):
    """Test detection of merge conflicts."""
    # Get main branch name
    result = subprocess.run(["git", "branch", "-l", "main"], cwd=temp_git_repo, capture_output=True, text=True)
    main_branch = "main" if "main" in result.stdout else "master"

    # Create feature branch with conflicting change
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=temp_git_repo, check=True, capture_output=True)

    readme = Path(temp_git_repo) / "README.md"
    readme.write_text("# Feature Change")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Feature change"], cwd=temp_git_repo, check=True, capture_output=True)

    # Switch back to main and make conflicting change
    subprocess.run(["git", "checkout", main_branch], cwd=temp_git_repo, check=True, capture_output=True)
    readme.write_text("# Main Change")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Main change"], cwd=temp_git_repo, check=True, capture_output=True)

    # Check for conflicts
    has_conflicts, error, files = check_merge_conflicts(
        branch_name="feature",
        target_branch=main_branch,
        cwd=temp_git_repo
    )

    assert has_conflicts is True


def test_validate_pre_merge_success(temp_git_repo):
    """Test successful pre-merge validation."""
    # Get main branch name
    result = subprocess.run(["git", "branch", "-l", "main"], cwd=temp_git_repo, capture_output=True, text=True)
    main_branch = "main" if "main" in result.stdout else "master"

    # Create clean feature branch
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=temp_git_repo, check=True, capture_output=True)

    new_file = Path(temp_git_repo) / "feature.txt"
    new_file.write_text("Feature")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add feature"], cwd=temp_git_repo, check=True, capture_output=True)

    # Switch to main
    subprocess.run(["git", "checkout", main_branch], cwd=temp_git_repo, check=True, capture_output=True)

    # Validate
    is_valid, errors, details = validate_pre_merge(
        branch_name="feature",
        target_branch=main_branch,
        check_ci=False,  # Skip CI check for tests
        cwd=temp_git_repo
    )

    assert is_valid is True
    assert len(errors) == 0


def test_validate_pre_merge_dirty_working_dir(temp_git_repo):
    """Test pre-merge validation fails with dirty working directory."""
    # Get main branch name
    result = subprocess.run(["git", "branch", "-l", "main"], cwd=temp_git_repo, capture_output=True, text=True)
    main_branch = "main" if "main" in result.stdout else "master"

    # Create feature branch
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=temp_git_repo, check=True, capture_output=True)
    new_file = Path(temp_git_repo) / "feature.txt"
    new_file.write_text("Feature")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add feature"], cwd=temp_git_repo, check=True, capture_output=True)

    # Switch to main and make uncommitted changes
    subprocess.run(["git", "checkout", main_branch], cwd=temp_git_repo, check=True, capture_output=True)
    dirty_file = Path(temp_git_repo) / "dirty.txt"
    dirty_file.write_text("Uncommitted")

    # Validate
    is_valid, errors, details = validate_pre_merge(
        branch_name="feature",
        target_branch=main_branch,
        check_ci=False,
        cwd=temp_git_repo
    )

    assert is_valid is False
    assert any("clean" in err.lower() or "uncommitted" in err.lower() for err in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
