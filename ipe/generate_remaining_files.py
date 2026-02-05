#!/usr/bin/env python3
"""
Script to generate remaining IPE workflow files from ADW templates.
This automates the refactoring of the remaining files per the plan.
"""

import os
import re
from pathlib import Path

# Define the transformation rules
TRANSFORMATIONS = {
    'adw_': 'ipe_',
    'ADW': 'IPE',
    'adws/': 'ipe/',
    'adw_modules': 'ipe_modules',
    'plan_file': 'spec_file',
    'shipped_at': 'deployed_at',
    'all_adws': 'all_ipes',
    '[🤖 ADW]': '[🤖 IPE]',
    '/implement': '/ipe_build',
    '/commit': '/ipe_commit',
    '/ship': '/ipe_deploy',
    '/test': '/ipe_validate',
    'adw_state.json': 'ipe_state.json',
    'ADWState': 'IPEState',
    'ADWStateData': 'IPEStateData',
    'AGENT_IMPLEMENTOR': 'AGENT_BUILDER',
    'AGENT_TESTER': 'AGENT_VALIDATOR',
}

# Files that should NOT include port-related code
PORT_REMOVALS = [
    'backend_port',
    'frontend_port',
    '.ports.env',
]

def transform_content(content: str, is_infrastructure: bool = True) -> str:
    """Apply transformations to file content."""
    result = content

    # Apply standard transformations
    for old, new in TRANSFORMATIONS.items():
        result = result.replace(old, new)

    # Remove port-related code if this is infrastructure
    if is_infrastructure:
        # Remove lines containing port references
        lines = result.split('\n')
        result = '\n'.join([
            line for line in lines
            if not any(port_ref in line for port_ref in PORT_REMOVALS)
        ])

    # Update docstrings
    result = result.replace('AI Developer Workflow', 'Infrastructure Platform Engineer')
    result = result.replace('Application Developer', 'Infrastructure Platform Engineer')
    result = result.replace('application', 'infrastructure')

    return result

def read_source_file(source_path: Path) -> str:
    """Read source file content."""
    try:
        with open(source_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {source_path}: {e}")
        return None

def write_target_file(target_path: Path, content: str):
    """Write content to target file."""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w') as f:
            f.write(content)
        print(f"✅ Created: {target_path}")
    except Exception as e:
        print(f"❌ Error writing {target_path}: {e}")

def process_file_mapping(source_file: str, target_file: str, repo_root: Path):
    """Process a single file mapping."""
    source_path = repo_root / source_file
    target_path = repo_root / target_file

    # Skip if target already exists
    if target_path.exists():
        print(f"⏭️  Skipped (exists): {target_path}")
        return

    # Read source
    content = read_source_file(source_path)
    if content is None:
        return

    # Transform content
    transformed = transform_content(content, is_infrastructure=True)

    # Write target
    write_target_file(target_path, transformed)

def main():
    """Main entry point."""
    # Get repo root
    repo_root = Path(__file__).parent.parent

    # Define file mappings for remaining Phase 1 files
    phase1_files = [
        ('adws/adw_review_iso.py', 'ipe/ipe_review_iso.py'),
        ('adws/adw_document_iso.py', 'ipe/ipe_document_iso.py'),
        ('adws/adw_ship_iso.py', 'ipe/ipe_ship_iso.py'),
        ('adws/adw_patch_iso.py', 'ipe/ipe_patch_iso.py'),
        ('adws/adw_sdlc_zte_iso.py', 'ipe/ipe_sdlc_zte_iso.py'),
    ]

    # Define file mappings for Phase 2 (composite workflows)
    phase2_files = [
        ('adws/adw_plan_build_review_iso.py', 'ipe/ipe_plan_build_review_iso.py'),
        ('adws/adw_plan_build_test_review_iso.py', 'ipe/ipe_plan_build_test_review_iso.py'),
        ('adws/adw_plan_build_document_iso.py', 'ipe/ipe_plan_build_document_iso.py'),
    ]

    # Define file mappings for Phase 3 (support scripts)
    phase3_files = [
        ('adws/adw_prompt.py', 'ipe/ipe_prompt.py'),
        ('adws/adw_slash_command.py', 'ipe/ipe_slash_command.py'),
        ('adws/adw_chore_implement.py', 'ipe/ipe_chore_implement.py'),
    ]

    print("=" * 60)
    print("Phase 1: Core Workflow Scripts")
    print("=" * 60)
    for source, target in phase1_files:
        process_file_mapping(source, target, repo_root)

    print("\n" + "=" * 60)
    print("Phase 2: Composite Workflow Scripts")
    print("=" * 60)
    for source, target in phase2_files:
        process_file_mapping(source, target, repo_root)

    print("\n" + "=" * 60)
    print("Phase 3: Support Scripts")
    print("=" * 60)
    for source, target in phase3_files:
        process_file_mapping(source, target, repo_root)

    print("\n" + "=" * 60)
    print("Generation complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review generated files for correctness")
    print("2. Run syntax validation: python3 -m py_compile ipe/ipe_*.py")
    print("3. Create trigger and test files manually or run additional generators")

if __name__ == "__main__":
    main()
