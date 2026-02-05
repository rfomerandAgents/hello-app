#!/usr/bin/env python3
"""
Script to generate IPE triggers and test files from ADW templates.
"""

import os
import re
from pathlib import Path

def transform_content(content: str) -> str:
    """Apply ADW→IPE transformations to file content."""
    replacements = {
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
        'ADW_BOT_IDENTIFIER': 'IPE_BOT_IDENTIFIER',
        'AVAILABLE_ADW_WORKFLOWS': 'AVAILABLE_IPE_WORKFLOWS',
        'AI Developer Workflow': 'Infrastructure Platform Engineer',
        'Application Developer': 'Infrastructure Platform Engineer',
        'Backend port': 'Environment',
        'frontend_port': 'terraform_dir',
        'backend_port': 'environment',
    }

    result = content
    for old, new in replacements.items():
        result = result.replace(old, new)

    # Remove port-related lines
    lines = result.split('\n')
    result = '\n'.join([
        line for line in lines
        if not any(word in line for word in ['.ports.env', 'PORT_RANGE'])
    ])

    return result

def copy_and_transform(source: Path, target: Path):
    """Copy and transform a file."""
    if target.exists():
        print(f"⏭️  Skipped (exists): {target}")
        return

    try:
        content = source.read_text()
        transformed = transform_content(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(transformed)
        print(f"✅ Created: {target}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent

    # Create ipe_triggers directory
    triggers_dir = repo_root / 'ipe' / 'ipe_triggers'
    triggers_dir.mkdir(parents=True, exist_ok=True)

    # Create ipe_tests directory
    tests_dir = repo_root / 'ipe' / 'ipe_tests'
    tests_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 4: Triggers")
    print("=" * 60)

    # Copy trigger files
    trigger_files = [
        ('adws/adw_triggers/trigger_webhook.py', 'ipe/ipe_triggers/trigger_webhook.py'),
        ('adws/adw_triggers/trigger_cron.py', 'ipe/ipe_triggers/trigger_cron.py'),
    ]

    for source_rel, target_rel in trigger_files:
        source = repo_root / source_rel
        target = repo_root / target_rel
        copy_and_transform(source, target)

    print("\n" + "=" * 60)
    print("Phase 5: Tests")
    print("=" * 60)

    # Get all test files from adw_tests
    adw_tests_dir = repo_root / 'adws' / 'adw_tests'
    if adw_tests_dir.exists():
        for source_file in adw_tests_dir.glob('*.py'):
            target_name = source_file.name.replace('adw_', 'ipe_')
            target = tests_dir / target_name
            copy_and_transform(source_file, target)

        # Also copy markdown files
        for source_file in adw_tests_dir.glob('*.md'):
            target_name = source_file.name.replace('adw_', 'ipe_')
            target = tests_dir / target_name
            copy_and_transform(source_file, target)

    print("\n" + "=" * 60)
    print("Generation complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
