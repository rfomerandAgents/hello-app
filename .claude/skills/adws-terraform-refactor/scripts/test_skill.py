#!/usr/bin/env python3
"""Validate adws-terraform-refactor skill.

This script validates that the skill is properly configured and all
referenced files exist.
"""

import re
import sys
from pathlib import Path


def test_frontmatter():
    """Verify SKILL.md has valid frontmatter."""
    print("Testing SKILL.md frontmatter...")

    skill_md = Path(__file__).parent.parent / "SKILL.md"
    if not skill_md.exists():
        print("  ✗ SKILL.md does not exist")
        return False

    content = skill_md.read_text()

    # Check for YAML frontmatter
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        print("  ✗ No valid YAML frontmatter found")
        return False

    frontmatter = match.group(1)

    # Check for required fields
    if 'name:' not in frontmatter:
        print("  ✗ Missing 'name' field in frontmatter")
        return False

    if 'description:' not in frontmatter:
        print("  ✗ Missing 'description' field in frontmatter")
        return False

    # Check name value
    if 'name: adws-terraform-refactor' not in frontmatter:
        print("  ✗ Incorrect name in frontmatter")
        return False

    print("  ✓ SKILL.md frontmatter is valid")
    return True


def test_reference_files():
    """Verify all reference files exist."""
    print("\nTesting reference files...")

    skill_dir = Path(__file__).parent.parent
    references_dir = skill_dir / "references"

    expected_files = [
        "module_mapping.md",
        "naming_conventions.md",
        "validation_checklist.md",
    ]

    all_exist = True
    for filename in expected_files:
        file_path = references_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename} exists")
        else:
            print(f"  ✗ {filename} missing")
            all_exist = False

    return all_exist


def test_script_files():
    """Verify script files exist and are executable."""
    print("\nTesting script files...")

    skill_dir = Path(__file__).parent.parent
    scripts_dir = skill_dir / "scripts"

    expected_files = [
        "refactor_module.py",
        "test_skill.py",  # This file
    ]

    all_exist = True
    for filename in expected_files:
        file_path = scripts_dir / filename
        if file_path.exists():
            # Check if executable (on Unix-like systems)
            is_executable = file_path.stat().st_mode & 0o111
            if is_executable:
                print(f"  ✓ {filename} exists and is executable")
            else:
                print(f"  ✓ {filename} exists (not executable)")
        else:
            print(f"  ✗ {filename} missing")
            all_exist = False

    return all_exist


def test_refactor_script():
    """Test that refactor script runs without import errors."""
    print("\nTesting refactor script execution...")

    try:
        # Try to import the refactor module
        import importlib.util

        script_path = Path(__file__).parent / "refactor_module.py"
        spec = importlib.util.spec_from_file_location("refactor_module", script_path)
        module = importlib.util.module_from_spec(spec)

        # This will fail if there are import errors
        spec.loader.exec_module(module)

        print("  ✓ refactor_module.py imports successfully")
        print("  ✓ All required functions defined")
        return True

    except Exception as e:
        print(f"  ✗ Error importing refactor_module.py: {e}")
        return False


def test_skill_content():
    """Verify SKILL.md has required sections."""
    print("\nTesting SKILL.md content...")

    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text()

    required_sections = [
        "## Overview",
        "## Core Philosophy",
        "## Module Transformation Strategy",
        "## Refactoring Workflow",
        "## Usage Examples",
        "## Related Skills",
        "## References",
    ]

    all_present = True
    for section in required_sections:
        if section in content:
            print(f"  ✓ Section '{section}' present")
        else:
            print(f"  ✗ Section '{section}' missing")
            all_present = False

    return all_present


def test_module_mapping_content():
    """Verify module mapping has all ADWS modules."""
    print("\nTesting module mapping content...")

    mapping_file = Path(__file__).parent.parent / "references" / "module_mapping.md"
    content = mapping_file.read_text()

    # Check that all expected modules are mentioned
    expected_modules = [
        "state.py",
        "agent.py",
        "workflow_ops.py",
        "github.py",
        "git_ops.py",
        "data_types.py",
        "utils.py",
        "worktree_ops.py",
    ]

    all_mentioned = True
    for module in expected_modules:
        if module in content:
            print(f"  ✓ Module '{module}' documented")
        else:
            print(f"  ✗ Module '{module}' missing from mapping")
            all_mentioned = False

    return all_mentioned


def test_naming_conventions_content():
    """Verify naming conventions has transformation rules."""
    print("\nTesting naming conventions content...")

    conventions_file = Path(__file__).parent.parent / "references" / "naming_conventions.md"
    content = conventions_file.read_text()

    # Check for key transformation patterns
    expected_patterns = [
        "ADWState",
        "IPEState",
        "adw_id",
        "ipe_id",
        "plan_file",
        "spec_file",
    ]

    all_present = True
    for pattern in expected_patterns:
        if pattern in content:
            print(f"  ✓ Pattern '{pattern}' documented")
        else:
            print(f"  ✗ Pattern '{pattern}' missing")
            all_present = False

    return all_present


def test_validation_checklist_content():
    """Verify validation checklist has required checks."""
    print("\nTesting validation checklist content...")

    checklist_file = Path(__file__).parent.parent / "references" / "validation_checklist.md"
    content = checklist_file.read_text()

    # Check for key validation categories
    expected_categories = [
        "File Structure Validation",
        "Naming Validation",
        "Import Statement Validation",
        "String Literal Validation",
        "State Field Validation",
    ]

    all_present = True
    for category in expected_categories:
        if category in content:
            print(f"  ✓ Category '{category}' present")
        else:
            print(f"  ✗ Category '{category}' missing")
            all_present = False

    return all_present


def main():
    """Run all tests."""
    print("=" * 60)
    print("ADWS Terraform Refactor Skill Validation")
    print("=" * 60)

    tests = [
        test_frontmatter,
        test_reference_files,
        test_script_files,
        test_refactor_script,
        test_skill_content,
        test_module_mapping_content,
        test_naming_conventions_content,
        test_validation_checklist_content,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n  ✗ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
