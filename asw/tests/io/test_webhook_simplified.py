#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv"]
# ///

"""
Test script to verify simplified webhook workflow support.
"""

import os

# Mirror the constants from trigger_webhook.py
DEPENDENT_WORKFLOWS = [
    "ipe_build", "ipe_test", "ipe_review", "ipe_document",
    "ipe_build_iso", "ipe_test_iso", "ipe_review_iso", "ipe_document_iso"
]

def test_workflow_support():
    """Test the simplified workflow support."""
    print("=== Simplified Webhook Workflow Support ===")
    print()
    
    print("Entry Point Workflows (can be triggered via webhook):")
    entry_points = [
        "ipe_plan",
        "ipe_patch", 
        "ipe_plan_build",
        "ipe_plan_build_test",
        "ipe_plan_build_test_review",
        "ipe_plan_build_document",
        "ipe_plan_build_review",
        "ipe_sdlc",
        "ipe_plan_iso",
        "ipe_patch_iso",
        "ipe_plan_build_iso",
        "ipe_plan_build_test_iso",
        "ipe_plan_build_test_review_iso",
        "ipe_plan_build_document_iso",
        "ipe_plan_build_review_iso",
        "ipe_sdlc_iso",
    ]
    
    for workflow in entry_points:
        emoji = "🏗️" if workflow.endswith("_iso") else "🔧"
        print(f"  {workflow:35} {emoji}")
    
    print()
    print("Dependent Workflows (require IPE ID):")
    for workflow in DEPENDENT_WORKFLOWS:
        emoji = "🏗️" if workflow.endswith("_iso") else "🔧"
        print(f"  {workflow:35} {emoji}")
    
    print()
    print("Testing workflow validation logic:")
    
    test_cases = [
        ("ipe_plan", None, True),
        ("ipe_plan_iso", None, True),
        ("ipe_build", None, False),  # Dependent, no ID
        ("ipe_build", "test-123", True),  # Dependent with ID
        ("ipe_build_iso", None, False),  # Dependent, no ID
        ("ipe_build_iso", "test-123", True),  # Dependent with ID
        ("ipe_plan_build", None, True),
        ("ipe_plan_build_iso", None, True),
        ("ipe_test_iso", None, False),  # Dependent, no ID
        ("ipe_sdlc_iso", None, True),
    ]
    
    for workflow, ipe_id, should_work in test_cases:
        if workflow in DEPENDENT_WORKFLOWS and not ipe_id:
            status = "❌ BLOCKED (requires IPE ID)"
        else:
            status = "✅ Can trigger"
        
        id_info = f" (with ID: {ipe_id})" if ipe_id else ""
        print(f"  {workflow:20}{id_info:20} {status}")


if __name__ == "__main__":
    test_workflow_support()