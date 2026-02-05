#!/usr/bin/env python3
"""Refactor ADWS module to IPE equivalent.

This script automates the transformation of ADWS application workflow code
to IPE infrastructure code by applying systematic naming transformations.

Usage:
    python refactor_module.py --source adws/adw_modules/state.py --target ../ipe/ipe_modules/ipe_state.py
    python refactor_module.py --source adws/adw_modules/state.py --target-dir ../ipe/ipe_modules/
    python refactor_module.py --batch adws/adw_modules/ --target-dir ../ipe/ipe_modules/
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Comprehensive substitution mappings
CLASS_SUBSTITUTIONS = {
    "ADWState": "IPEState",
    "ADWStateData": "IPEStateData",
    "ADWConfig": "IPEConfig",
    "ADWWorkflow": "IPEWorkflow",
}

FUNCTION_SUBSTITUTIONS = {
    "make_adw_id": "make_ipe_id",
    "ensure_adw_id": "ensure_ipe_id",
    "validate_adw_state": "validate_ipe_state",
    "get_adw_config": "get_ipe_config",
    "load_adw_state": "load_ipe_state",
    "save_adw_state": "save_ipe_state",
    "list_all_adws": "list_all_ipes",
    "start_adw_workflow": "start_ipe_workflow",
    "run_adw_agent": "run_ipe_agent",
    "create_adw_branch": "create_ipe_branch",
    "append_adw_id": "append_ipe_id",
}

VARIABLE_SUBSTITUTIONS = {
    "adw_id": "ipe_id",
    "plan_file": "spec_file",
    "all_adws": "all_ipes",
    "shipped_at": "deployed_at",
}

STRING_LITERAL_SUBSTITUTIONS = {
    '"adw_state.json"': '"ipe_state.json"',
    "'adw_state.json'": "'ipe_state.json'",
    '"/tmp/adws/"': '"/tmp/ipes/"',
    "'/tmp/adws/'": "'/tmp/ipes/'",
    '"[🤖 ADW]"': '"[🤖 IPE]"',
    "'[🤖 ADW]'": "'[🤖 IPE]'",
    'f"[🤖 ADW]': 'f"[🤖 IPE]',
    "f'[🤖 ADW]": "f'[🤖 IPE]",
    '"adw_"': '"ipe_"',
    "'adw_'": "'ipe_'",
    'f"adw_': 'f"ipe_',
    "f'adw_": "f'ipe_",
}

SLASH_COMMAND_SUBSTITUTIONS = {
    '"/implement"': '"/ipe_build"',
    '"/commit"': '"/ipe_commit"',
    '"/ship"': '"/ipe_deploy"',
    '"/test"': '"/ipe_validate"',
    '"/status"': '"/ipe_status"',
    '"/rollback"': '"/ipe_rollback"',
}

# Import transformation patterns
IMPORT_PATTERNS = [
    (r'from adw_modules\.(\w+) import', r'from .ipe_\1 import'),
    (r'from adw_modules import (\w+)', r'from . import ipe_\1'),
    (r'import adw_modules\.(\w+)', r'from . import ipe_\1'),
]

# Docstring terminology transformations
DOCSTRING_TERMINOLOGY = {
    "Application Developer Workflow": "Infrastructure Platform Engineer",
    "ADW workflow": "IPE workflow",
    "ADW system": "IPE system",
    "application code": "infrastructure code",
    "backend/frontend": "Terraform/Packer",
}


def transform_imports(content: str) -> str:
    """Transform import statements from ADWS to IPE pattern.

    Converts absolute imports to relative imports and updates module names.
    """
    for pattern, replacement in IMPORT_PATTERNS:
        content = re.sub(pattern, replacement, content)
    return content


def transform_class_names(content: str) -> str:
    """Transform class names from ADW* to IPE*."""
    for old_name, new_name in CLASS_SUBSTITUTIONS.items():
        # Use word boundaries to avoid partial matches
        content = re.sub(rf'\b{old_name}\b', new_name, content)
    return content


def transform_function_names(content: str) -> str:
    """Transform function names containing adw_ to ipe_."""
    for old_name, new_name in FUNCTION_SUBSTITUTIONS.items():
        content = re.sub(rf'\b{old_name}\b', new_name, content)
    return content


def transform_variable_names(content: str) -> str:
    """Transform variable names from adw_* to ipe_*."""
    for old_name, new_name in VARIABLE_SUBSTITUTIONS.items():
        content = re.sub(rf'\b{old_name}\b', new_name, content)
    return content


def transform_string_literals(content: str) -> str:
    """Transform string literals containing ADWS references."""
    for old_str, new_str in STRING_LITERAL_SUBSTITUTIONS.items():
        content = content.replace(old_str, new_str)
    return content


def transform_slash_commands(content: str) -> str:
    """Transform slash commands from /implement to /ipe_*."""
    for old_cmd, new_cmd in SLASH_COMMAND_SUBSTITUTIONS.items():
        content = content.replace(old_cmd, new_cmd)
    return content


def transform_docstrings(content: str) -> str:
    """Transform terminology in docstrings and comments."""
    for old_term, new_term in DOCSTRING_TERMINOLOGY.items():
        content = content.replace(old_term, new_term)
    return content


def transform_generic_adw_references(content: str) -> str:
    """Transform remaining generic adw_ and ADW references.

    This is a catch-all for any patterns not covered by specific transformations.
    Uses word boundaries to avoid breaking URLs or other content.
    """
    # Transform adw_ to ipe_ (catch-all for missed patterns)
    content = re.sub(r'\badw_(\w+)', r'ipe_\1', content)

    # Transform ADW to IPE in contexts not already handled
    # But preserve it in migration notes (lines containing "Migrated from")
    lines = content.split('\n')
    transformed_lines = []
    for line in lines:
        if 'Migrated from ADW' not in line and 'Migration from ADW' not in line:
            line = re.sub(r'\bADW\b', 'IPE', line)
        transformed_lines.append(line)
    content = '\n'.join(transformed_lines)

    return content


def add_migration_note(content: str, source_file: str) -> str:
    """Add a migration note at the top of the file."""
    # Find the module docstring
    docstring_match = re.match(r'^("""[\s\S]*?""")', content)

    if docstring_match:
        docstring = docstring_match.group(1)
        rest = content[len(docstring):]

        # Add migration note after docstring
        migration_note = f"\n# Migration Note: This module was refactored from {source_file}\n# All adw_* references have been transformed to ipe_*\n"
        return docstring + migration_note + rest
    else:
        # No docstring, add at top
        migration_note = f'"""Migrated from {source_file}.\n\nAll adw_* references have been transformed to ipe_*.\n"""\n\n'
        return migration_note + content


def refactor_content(content: str, source_file: str = "") -> str:
    """Apply all transformations to file content.

    Args:
        content: The source file content
        source_file: Original source file path (for migration note)

    Returns:
        Transformed content ready for IPE
    """
    # Apply transformations in order
    content = transform_imports(content)
    content = transform_class_names(content)
    content = transform_function_names(content)
    content = transform_variable_names(content)
    content = transform_string_literals(content)
    content = transform_slash_commands(content)
    content = transform_docstrings(content)
    content = transform_generic_adw_references(content)

    # Add migration note
    if source_file:
        content = add_migration_note(content, source_file)

    return content


def determine_target_filename(source_path: Path) -> str:
    """Determine the IPE filename from ADWS source filename.

    Examples:
        state.py -> ipe_state.py
        agent.py -> ipe_agent.py
        workflow_ops.py -> ipe_workflow_ops.py
    """
    stem = source_path.stem
    suffix = source_path.suffix

    # If it already has ipe_ prefix (unlikely but possible)
    if stem.startswith('ipe_'):
        return f"{stem}{suffix}"

    # Add ipe_ prefix
    return f"ipe_{stem}{suffix}"


def validate_source_file(source_path: Path) -> bool:
    """Validate that source file is a Python file from adw_modules."""
    if not source_path.exists():
        print(f"Error: Source file does not exist: {source_path}", file=sys.stderr)
        return False

    if source_path.suffix != '.py':
        print(f"Error: Source file is not a Python file: {source_path}", file=sys.stderr)
        return False

    if '__pycache__' in str(source_path):
        print(f"Skipping cache file: {source_path}")
        return False

    return True


def refactor_single_file(source_path: Path, target_path: Path, dry_run: bool = False) -> bool:
    """Refactor a single ADWS module to IPE.

    Args:
        source_path: Path to source ADWS file
        target_path: Path to target IPE file
        dry_run: If True, don't write files, just show what would be done

    Returns:
        True if successful, False otherwise
    """
    print(f"Refactoring: {source_path} -> {target_path}")

    if not validate_source_file(source_path):
        return False

    # Read source content
    try:
        content = source_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading source file: {e}", file=sys.stderr)
        return False

    # Transform content
    transformed_content = refactor_content(content, str(source_path))

    if dry_run:
        print("\n--- Transformed Content Preview (first 50 lines) ---")
        lines = transformed_content.split('\n')
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3d}: {line}")
        print("--- End Preview ---\n")
        return True

    # Write target file
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(transformed_content, encoding='utf-8')
        print(f"✓ Successfully refactored to: {target_path}")
        return True
    except Exception as e:
        print(f"Error writing target file: {e}", file=sys.stderr)
        return False


def refactor_batch(source_dir: Path, target_dir: Path, dry_run: bool = False) -> Tuple[int, int]:
    """Refactor all Python files in a directory.

    Args:
        source_dir: Directory containing ADWS modules
        target_dir: Directory for IPE modules
        dry_run: If True, don't write files

    Returns:
        Tuple of (success_count, total_count)
    """
    if not source_dir.is_dir():
        print(f"Error: Source directory does not exist: {source_dir}", file=sys.stderr)
        return (0, 0)

    # Find all Python files (excluding __init__.py and __pycache__)
    python_files = [
        f for f in source_dir.glob('*.py')
        if f.name != '__init__.py' and '__pycache__' not in str(f)
    ]

    if not python_files:
        print(f"No Python files found in: {source_dir}")
        return (0, 0)

    print(f"Found {len(python_files)} files to refactor\n")

    success_count = 0
    for source_path in python_files:
        target_filename = determine_target_filename(source_path)
        target_path = target_dir / target_filename

        if refactor_single_file(source_path, target_path, dry_run):
            success_count += 1
        print()  # Blank line between files

    return (success_count, len(python_files))


def validate_target_directory(target_dir: Path) -> bool:
    """Validate that target directory is the correct IPE location."""
    # Check if path contains 'ipe' and is outside current project
    target_str = str(target_dir.resolve())

    if 'ipe' not in target_str.lower():
        print(f"Warning: Target directory doesn't contain 'ipe': {target_dir}", file=sys.stderr)
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Refactor ADWS module to IPE equivalent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Refactor single file
  %(prog)s --source adws/adw_modules/state.py --target ../ipe/ipe_modules/ipe_state.py

  # Refactor single file to directory (auto-name)
  %(prog)s --source adws/adw_modules/state.py --target-dir ../ipe/ipe_modules/

  # Refactor all files in directory
  %(prog)s --batch adws/adw_modules/ --target-dir ../ipe/ipe_modules/

  # Dry run (preview only)
  %(prog)s --source adws/adw_modules/state.py --target-dir ../ipe/ipe_modules/ --dry-run
        """
    )

    parser.add_argument(
        '--source',
        type=Path,
        help='Source ADWS file to refactor'
    )

    parser.add_argument(
        '--target',
        type=Path,
        help='Target IPE file path'
    )

    parser.add_argument(
        '--target-dir',
        type=Path,
        help='Target directory for IPE modules (filename auto-generated)'
    )

    parser.add_argument(
        '--batch',
        type=Path,
        help='Refactor all files in source directory'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview transformations without writing files'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip target directory validation'
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.batch and args.source:
        parser.error("Cannot use both --batch and --source")

    if not args.batch and not args.source:
        parser.error("Must specify either --source or --batch")

    if args.target and args.target_dir:
        parser.error("Cannot use both --target and --target-dir")

    if not args.target and not args.target_dir:
        parser.error("Must specify either --target or --target-dir")

    # Batch mode
    if args.batch:
        if not args.target_dir:
            parser.error("--batch requires --target-dir")

        if not args.force and not validate_target_directory(args.target_dir):
            print("Use --force to override target directory validation")
            return 1

        success, total = refactor_batch(args.batch, args.target_dir, args.dry_run)

        print(f"\n{'='*60}")
        print(f"Batch refactoring complete: {success}/{total} files successful")
        if args.dry_run:
            print("(Dry run - no files were written)")
        print(f"{'='*60}")

        return 0 if success == total else 1

    # Single file mode
    else:
        if args.target_dir:
            # Auto-generate target filename
            target_filename = determine_target_filename(args.source)
            target_path = args.target_dir / target_filename
        else:
            target_path = args.target

        if not args.force and args.target_dir:
            if not validate_target_directory(args.target_dir):
                print("Use --force to override target directory validation")
                return 1

        success = refactor_single_file(args.source, target_path, args.dry_run)

        if args.dry_run:
            print("\n(Dry run - no files were written)")

        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
