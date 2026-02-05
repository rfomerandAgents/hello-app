#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv", "httpx", "pytest"]
# ///

"""
Test Suite for Unified Webhook Router

Tests workflow detection and routing for both ADW and IPE workflows.

Usage: uv run test_unified_webhook.py
"""

import pytest
import sys
import os

# Add parent directory to path for imports
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, "triggers"))

from trigger_webhook import detect_workflow_type, extract_workflow_info


def test_adw_workflow_detection():
    """Test ADW workflow detection."""

    # Test adw_plan_iso detection
    content = "Please run adw_plan_iso for this issue"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "adw"
    assert workflow_command == "adw_plan_iso"

    # Test adw_build_iso detection
    content = "adw_build_iso adw-12345678"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "adw"
    assert workflow_command == "adw_build_iso"

    # Test adw_test_iso detection
    content = "Run adw_test_iso adw-12345678 sonnet"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "adw"
    assert workflow_command == "adw_test_iso"


def test_ipe_workflow_detection():
    """Test IPE workflow detection."""

    # Test ipe_plan_iso detection
    content = "Please run ipe_plan_iso for this infrastructure change"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_plan_iso"

    # Test ipe_build_iso detection
    content = "ipe_build_iso ipe-87654321"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_build_iso"

    # Test ipe_test_iso detection
    content = "Run ipe_test_iso ipe-87654321 haiku"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_test_iso"


def test_priority_ipe_first():
    """Test that IPE workflows are detected first when both present."""

    # IPE should be detected first
    content = "Run ipe_plan_iso and then adw_build_iso"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_plan_iso"


def test_no_workflow_detected():
    """Test that non-workflow content is ignored."""

    content = "This is a bug report about the authentication system"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type is None
    assert workflow_command is None

    content = "Fix the CSS styling issue"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type is None
    assert workflow_command is None


def test_case_insensitive():
    """Test that workflow detection is case-insensitive."""

    content = "ADW_PLAN_ISO please"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "adw"
    assert workflow_command == "adw_plan_iso"

    content = "IPE_TEST_ISO ipe-12345678"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_test_iso"


def test_bot_identifier_prevention():
    """Test that bot messages would be ignored."""

    from trigger_webhook import BOT_IDENTIFIERS

    # Check that bot identifiers exist
    assert "[ADW-AGENTS]" in BOT_IDENTIFIERS
    assert "🤖 IPE" in BOT_IDENTIFIERS

    # Test bot message detection
    content = "[ADW-AGENTS] Webhook: Starting adw_plan_iso"
    assert any(bot_id in content for bot_id in BOT_IDENTIFIERS)

    content = "🤖 IPE Webhook: Starting ipe_plan_iso"
    assert any(bot_id in content for bot_id in BOT_IDENTIFIERS)


def test_all_adw_workflows():
    """Test detection of all ADW workflows."""

    adw_workflows = [
        "adw_plan_iso",
        "adw_build_iso",
        "adw_test_iso",
        "adw_review_iso",
        "adw_document_iso",
        "adw_ship_iso",
        "adw_sdlc_iso",
        "adw_patch_iso",
    ]

    for workflow in adw_workflows:
        content = f"Run {workflow} now"
        workflow_type, workflow_command = detect_workflow_type(content)
        assert workflow_type == "adw", f"Failed to detect {workflow}"
        assert workflow_command == workflow, f"Wrong command for {workflow}"


def test_all_ipe_workflows():
    """Test detection of all IPE workflows."""

    ipe_workflows = [
        "ipe_plan_iso",
        "ipe_build_iso",
        "ipe_test_iso",
        "ipe_review_iso",
        "ipe_document_iso",
        "ipe_ship_iso",
        "ipe_sdlc_iso",
    ]

    for workflow in ipe_workflows:
        content = f"Run {workflow} now"
        workflow_type, workflow_command = detect_workflow_type(content)
        assert workflow_type == "ipe", f"Failed to detect {workflow}"
        assert workflow_command == workflow, f"Wrong command for {workflow}"


def test_dependent_workflows():
    """Test that dependent workflow lists are defined."""

    from trigger_webhook import ADW_DEPENDENT_WORKFLOWS, IPE_DEPENDENT_WORKFLOWS

    # Check ADW dependent workflows
    assert "adw_build_iso" in ADW_DEPENDENT_WORKFLOWS
    assert "adw_test_iso" in ADW_DEPENDENT_WORKFLOWS
    assert "adw_review_iso" in ADW_DEPENDENT_WORKFLOWS
    assert "adw_ship_iso" in ADW_DEPENDENT_WORKFLOWS

    # Check IPE dependent workflows
    assert "ipe_build_iso" in IPE_DEPENDENT_WORKFLOWS
    assert "ipe_test_iso" in IPE_DEPENDENT_WORKFLOWS
    assert "ipe_review_iso" in IPE_DEPENDENT_WORKFLOWS
    assert "ipe_ship_iso" in IPE_DEPENDENT_WORKFLOWS


def test_workflow_with_id_and_model():
    """Test parsing workflow with ID and model set."""

    # ADW workflow with ID and model
    content = "adw_test_iso adw-12345678 sonnet"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "adw"
    assert workflow_command == "adw_test_iso"

    # IPE workflow with ID and model
    content = "ipe_test_iso ipe-87654321 haiku"
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_test_iso"


def test_multiline_content():
    """Test workflow detection in multiline content."""

    content = """
    This is a feature request for adding dark mode.

    Please run adw_plan_iso to implement this feature.

    Thanks!
    """
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "adw"
    assert workflow_command == "adw_plan_iso"


def test_markdown_formatted_content():
    """Test workflow detection in markdown formatted content."""

    content = """
    ## Infrastructure Change Request

    We need to update the Terraform configuration.

    **Action**: `ipe_plan_iso`

    Please review and approve.
    """
    workflow_type, workflow_command = detect_workflow_type(content)
    assert workflow_type == "ipe"
    assert workflow_command == "ipe_plan_iso"


def test_e2b_mode_detection():
    """Test E2B execution mode detection."""
    from trigger_webhook import detect_e2b_mode

    # Positive cases - standalone flags
    assert detect_e2b_mode("Run adw_plan_iso --e2b") == True
    assert detect_e2b_mode("adw_plan_iso -e2b") == True
    assert detect_e2b_mode("--e2b adw_plan_iso") == True
    assert detect_e2b_mode("-e2b adw_plan_iso") == True

    # Positive cases - with equals
    assert detect_e2b_mode("adw_plan_iso e2b=true") == True
    assert detect_e2b_mode("Run adw_plan_iso --e2b=true") == True
    assert detect_e2b_mode("adw_plan_iso --e2b=true") == True
    assert detect_e2b_mode("e2b=true adw_plan_iso") == True

    # Positive cases - case insensitive
    assert detect_e2b_mode("ADW_PLAN_ISO E2B=TRUE") == True
    assert detect_e2b_mode("ADW_PLAN_ISO --E2B") == True
    assert detect_e2b_mode("ADW_PLAN_ISO -E2B") == True

    # Positive cases - with whitespace variations
    assert detect_e2b_mode("adw_plan_iso e2b = true") == True
    assert detect_e2b_mode("adw_plan_iso e2b= true") == True
    assert detect_e2b_mode("adw_plan_iso e2b =true") == True

    # Negative cases
    assert detect_e2b_mode("Run adw_plan_iso") == False
    assert detect_e2b_mode("adw_plan_iso") == False
    assert detect_e2b_mode("adw_plan_iso e2b=false") == False
    assert detect_e2b_mode("use2b flag") == False  # Should not match partial
    assert detect_e2b_mode("note2business") == False  # Should not match partial
    assert detect_e2b_mode("e2b") == False  # No word boundary at start
    assert detect_e2b_mode("Let's use e2b later") == False  # Should not match without flag syntax


def test_e2b_mode_in_workflow_info():
    """Test that E2B mode is included in workflow info extraction."""
    from trigger_webhook import extract_workflow_info

    # Test ADW workflow with E2B flag
    content = "adw_plan_iso --e2b"
    temp_id = "adw-test1234"
    info = extract_workflow_info(content, "adw", temp_id)
    assert info.get("e2b_mode") == True

    # Test ADW workflow without E2B flag
    content = "adw_plan_iso"
    info = extract_workflow_info(content, "adw", temp_id)
    assert info.get("e2b_mode") == False

    # Test IPE workflow with E2B flag
    content = "ipe_plan_iso e2b=true"
    temp_id = "ipe-test5678"
    info = extract_workflow_info(content, "ipe", temp_id)
    assert info.get("e2b_mode") == True

    # Test IPE workflow without E2B flag
    content = "ipe_plan_iso"
    info = extract_workflow_info(content, "ipe", temp_id)
    assert info.get("e2b_mode") == False


def test_e2b_mode_with_other_params():
    """Test E2B mode detection alongside other workflow parameters."""
    from trigger_webhook import extract_workflow_info

    # ADW workflow with ID and E2B
    # Note: ADW uses AI classifier for model_set extraction, so we just verify E2B is detected
    content = "adw_test_iso adw-12345678 --e2b"
    temp_id = "adw-temp9999"
    info = extract_workflow_info(content, "adw", temp_id)
    assert info.get("e2b_mode") == True
    # Workflow ID extraction depends on AI classifier, so we just verify e2b_mode

    # IPE workflow with ID and E2B
    content = "ipe_build_iso ipe-87654321 e2b=true"
    temp_id = "ipe-temp8888"
    info = extract_workflow_info(content, "ipe", temp_id)
    assert info.get("e2b_mode") == True
    assert info.get("workflow_id") == "ipe-87654321"


if __name__ == "__main__":
    # Run tests
    print("Running Unified Webhook Router Tests...\n")

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
