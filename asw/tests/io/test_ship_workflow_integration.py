#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest", "python-dotenv", "pydantic"]
# ///

"""
Integration tests for ship workflow.

Tests the complete ship workflow including:
- State validation
- State metadata updates
- State persistence
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.state import ASWIOState
from asw.modules.data_types import ASWIOStateData


@pytest.fixture
def mock_agents_dir():
    """Create temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    agents_dir = Path(temp_dir) / "agents"
    agents_dir.mkdir()

    yield temp_dir, agents_dir

    shutil.rmtree(temp_dir)


def test_state_data_includes_ship_metadata():
    """Test that ASWIOStateData model includes ship metadata fields."""
    data = ASWIOStateData(
        ipe_id="test1234",
        issue_number="123",
        branch_name="feature-test",
        deployed_at="2024-11-20T10:00:00Z",
        merge_commit="abc123def456",
        pr_number="42"
    )

    assert data.deployed_at == "2024-11-20T10:00:00Z"
    assert data.merge_commit == "abc123def456"
    assert data.pr_number == "42"


def test_state_data_ship_metadata_optional():
    """Test that ship metadata fields are optional."""
    data = ASWIOStateData(
        ipe_id="test1234",
        issue_number="123"
    )

    assert data.deployed_at is None
    assert data.merge_commit is None
    assert data.pr_number is None


def test_state_update_with_ship_metadata():
    """Test that state can be updated with ship metadata."""
    state = ASWIOState("test5678")
    state.update(
        deployed_at="2024-11-20T10:00:00Z",
        merge_commit="abc123def456",
        pr_number="42"
    )

    assert state.get("deployed_at") == "2024-11-20T10:00:00Z"
    assert state.get("merge_commit") == "abc123def456"
    assert state.get("pr_number") == "42"


def test_state_tracks_ship_workflow():
    """Test that ship workflow is tracked in all_ipes."""
    state = ASWIOState("test9999")

    # Simulate workflow progression
    state.append_ipe_id("ipe_plan_iso")
    state.append_ipe_id("ipe_build_iso")
    state.append_ipe_id("ipe_ship_iso")

    assert "ipe_plan_iso" in state.data["all_ipes"]
    assert "ipe_build_iso" in state.data["all_ipes"]
    assert "ipe_ship_iso" in state.data["all_ipes"]


def test_state_append_ipe_id_no_duplicates():
    """Test that append_ipe_id does not create duplicates."""
    state = ASWIOState("testdup")

    state.append_ipe_id("ipe_ship_iso")
    state.append_ipe_id("ipe_ship_iso")
    state.append_ipe_id("ipe_ship_iso")

    assert state.data["all_ipes"].count("ipe_ship_iso") == 1


def test_state_data_model_dump_includes_ship_metadata():
    """Test that model dump includes ship metadata."""
    data = ASWIOStateData(
        ipe_id="testdump",
        deployed_at="2024-11-20T10:00:00Z",
        merge_commit="abc123",
        pr_number="99"
    )

    dumped = data.model_dump()

    assert "deployed_at" in dumped
    assert "merge_commit" in dumped
    assert "pr_number" in dumped
    assert dumped["deployed_at"] == "2024-11-20T10:00:00Z"


def test_state_data_from_json_with_ship_metadata():
    """Test loading state data from JSON with ship metadata."""
    json_data = {
        "ipe_id": "testjson",
        "issue_number": "123",
        "branch_name": "feature-test",
        "deployed_at": "2024-11-20T12:00:00Z",
        "merge_commit": "def456",
        "pr_number": "100",
        "all_ipes": ["ipe_plan_iso", "ipe_ship_iso"]
    }

    data = ASWIOStateData(**json_data)

    assert data.deployed_at == "2024-11-20T12:00:00Z"
    assert data.merge_commit == "def456"
    assert data.pr_number == "100"
    assert "ipe_ship_iso" in data.all_ipes


def test_state_backward_compatibility():
    """Test that old state files without ship metadata load correctly."""
    # Old format without ship metadata
    json_data = {
        "ipe_id": "testold",
        "issue_number": "50",
        "branch_name": "feature-old",
        "spec_file": "specs/plan.md",
        "issue_class": "/feature",
        "all_ipes": ["ipe_plan_iso"]
    }

    # Should not raise an error
    data = ASWIOStateData(**json_data)

    assert data.ipe_id == "testold"
    assert data.deployed_at is None
    assert data.merge_commit is None
    assert data.pr_number is None


def test_full_ship_state_simulation():
    """Simulate a complete ship workflow state update."""
    state = ASWIOState("fullship")

    # Initial state from plan workflow
    state.update(
        issue_number="200",
        branch_name="feature-issue-200-adw-fullship",
        spec_file="specs/plan.md",
        issue_class="/feature",
        worktree_path="/tmp/trees/fullship",
        environment=8000,
        terraform_dir=3000
    )

    # Track workflow phases
    state.append_ipe_id("ipe_plan_iso")
    state.append_ipe_id("ipe_build_iso")
    state.append_ipe_id("ipe_test_iso")
    state.append_ipe_id("ipe_review_iso")
    state.append_ipe_id("ipe_document_iso")

    # Ship workflow completes
    state.update(
        deployed_at="2024-11-20T15:30:00Z",
        merge_commit="abc123def456789",
        pr_number="201"
    )
    state.append_ipe_id("ipe_ship_iso")

    # Verify complete state
    assert state.get("deployed_at") == "2024-11-20T15:30:00Z"
    assert state.get("merge_commit") == "abc123def456789"
    assert state.get("pr_number") == "201"
    assert "ipe_ship_iso" in state.data["all_ipes"]
    assert len(state.data["all_ipes"]) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
