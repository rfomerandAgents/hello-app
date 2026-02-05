#!/usr/bin/env python3
"""
Template Validation Script

Validates a decoupled template for completeness and quality.
Checks for required directories, configuration validity, and leaked project-specific content.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class ValidationReport:
    """Track validation results."""

    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []

    def add_check(self, name: str, passed: bool, message: str = ""):
        """Add a validation check result."""
        self.checks.append({
            'name': name,
            'passed': passed,
            'message': message
        })
        if not passed:
            self.errors.append(f"{name}: {message}")
        elif message:
            self.warnings.append(f"{name}: {message}")

    def print_report(self):
        """Print formatted validation report."""
        print("\n" + "=" * 70)
        print("TEMPLATE VALIDATION REPORT")
        print("=" * 70 + "\n")

        # Print checks
        for check in self.checks:
            symbol = "✓" if check['passed'] else "✗"
            status = "PASS" if check['passed'] else "FAIL"
            print(f"{symbol} {check['name']}: {status}")
            if check['message']:
                print(f"  → {check['message']}")

        # Summary
        passed = sum(1 for c in self.checks if c['passed'])
        total = len(self.checks)
        print(f"\n{'=' * 70}")
        print(f"Summary: {passed}/{total} checks passed")

        if self.warnings:
            print(f"\nWarnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print(f"\nErrors: {len(self.errors)}")
            for error in self.errors:
                print(f"  ✗ {error}")

        print("=" * 70)

    def exit_code(self) -> int:
        """Return appropriate exit code."""
        if self.errors:
            return 2  # Failures
        elif self.warnings:
            return 1  # Warnings
        else:
            return 0  # Success


def check_required_directories(template_dir: Path, report: ValidationReport):
    """Check that all required directories exist."""
    required_dirs = [
        '.claude',
        '.claude/commands',
        '.claude/hooks',
        'adws',
        'ipe',
        'specs/high-level',
        'specs/medium-level',
        'specs/low-level',
        'terraform',
        'app',
        'logs',
    ]

    missing = []
    for dir_name in required_dirs:
        dir_path = template_dir / dir_name
        if not dir_path.exists():
            missing.append(dir_name)

    if missing:
        report.add_check(
            "Required Directories",
            False,
            f"Missing: {', '.join(missing)}"
        )
    else:
        report.add_check(
            "Required Directories",
            True,
            f"All {len(required_dirs)} required directories present"
        )


def check_required_files(template_dir: Path, report: ValidationReport):
    """Check that required files exist."""
    required_files = [
        'README.md',
        '.gitignore',
        '.claude/settings.json',
    ]

    missing = []
    for file_name in required_files:
        file_path = template_dir / file_name
        if not file_path.exists():
            missing.append(file_name)

    if missing:
        report.add_check(
            "Required Files",
            False,
            f"Missing: {', '.join(missing)}"
        )
    else:
        report.add_check(
            "Required Files",
            True,
            f"All {len(required_files)} required files present"
        )


def check_settings_json(template_dir: Path, report: ValidationReport):
    """Validate .claude/settings.json is valid JSON."""
    settings_file = template_dir / '.claude' / 'settings.json'

    if not settings_file.exists():
        report.add_check("settings.json Format", False, "File not found")
        return

    try:
        with settings_file.open('r') as f:
            settings = json.load(f)

        # Check for secrets
        has_secrets = 'apiKeys' in settings or 'secrets' in settings
        if has_secrets:
            report.add_check(
                "settings.json Format",
                False,
                "Contains apiKeys or secrets that should be removed"
            )
        else:
            report.add_check(
                "settings.json Format",
                True,
                "Valid JSON, no secrets found"
            )
    except json.JSONDecodeError as e:
        report.add_check(
            "settings.json Format",
            False,
            f"Invalid JSON: {e}"
        )


def check_project_specific_content(template_dir: Path, report: ValidationReport):
    """Search for project-specific content that should be genericized."""
    readme_file = template_dir / 'README.md'

    if not readme_file.exists():
        report.add_check("Project-Specific Content", False, "README.md not found")
        return

    content = readme_file.read_text()

    # Search patterns - add project-specific terms here to detect in templates
    # Example: if your project is about "widgets", add patterns for widget-specific terms
    project_patterns = [
        (r'\b{{PROJECT_NAME}}\b', '{{PROJECT_NAME}}'),
        # Add your project-specific terms below:
        # (r'\bwidget\b', 'widget'),
        # (r'\bwidgets\b', 'widgets'),
        (r'github\.com/[^/]+/[^/]+\.farm', 'specific GitHub URL'),
        # (r'Your Project Description', 'project description'),
    ]

    found_issues = []
    for pattern, description in project_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Exclude matches that are part of placeholder syntax
            actual_matches = [m for m in matches if '{{' not in m and '}}' not in m]
            if actual_matches:
                found_issues.append(f"{description} ({len(actual_matches)} occurrences)")

    if found_issues:
        report.add_check(
            "Project-Specific Content",
            False,
            f"Found: {', '.join(found_issues)}"
        )
    else:
        report.add_check(
            "Project-Specific Content",
            True,
            "No project-specific content found"
        )


def check_terraform_syntax(template_dir: Path, report: ValidationReport):
    """Validate Terraform files syntax (if terraform CLI available)."""
    terraform_dir = template_dir / 'io' / 'terraform'

    if not terraform_dir.exists():
        report.add_check("Terraform Syntax", False, "io/terraform/ directory not found")
        return

    # Check if terraform CLI is available
    try:
        subprocess.run(
            ['terraform', 'version'],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        report.add_check(
            "Terraform Syntax",
            True,
            "Terraform CLI not available, skipping validation"
        )
        return

    # Validate Terraform configuration
    try:
        # Initialize (without backend)
        subprocess.run(
            ['terraform', 'init', '-backend=false'],
            cwd=terraform_dir,
            capture_output=True,
            check=True
        )

        # Validate
        result = subprocess.run(
            ['terraform', 'validate'],
            cwd=terraform_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            report.add_check(
                "Terraform Syntax",
                True,
                "Terraform configuration is valid"
            )
        else:
            report.add_check(
                "Terraform Syntax",
                False,
                f"Validation failed: {result.stderr}"
            )
    except subprocess.CalledProcessError as e:
        report.add_check(
            "Terraform Syntax",
            False,
            f"Terraform validation error: {e}"
        )


def check_git_repository(template_dir: Path, report: ValidationReport):
    """Check that template is a git repository."""
    git_dir = template_dir / '.git'

    if not git_dir.exists():
        report.add_check(
            "Git Repository",
            False,
            "Not a git repository"
        )
        return

    try:
        # Check for commits
        result = subprocess.run(
            ['git', 'log', '--oneline', '-1'],
            cwd=template_dir,
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            report.add_check(
                "Git Repository",
                True,
                f"Initialized with commit: {result.stdout.strip()}"
            )
        else:
            report.add_check(
                "Git Repository",
                False,
                "No commits found"
            )
    except subprocess.CalledProcessError:
        report.add_check(
            "Git Repository",
            False,
            "Could not check git status"
        )


def check_gitkeep_files(template_dir: Path, report: ValidationReport):
    """Check that empty directories have .gitkeep files."""
    empty_dirs = [
        'app',
        'ipe_logs',
        'logs',
        'agents',
        'trees',
        'specs/high-level',
        'specs/medium-level',
        'specs/low-level',
    ]

    missing = []
    for dir_name in empty_dirs:
        dir_path = template_dir / dir_name
        gitkeep = dir_path / '.gitkeep'
        if dir_path.exists() and not gitkeep.exists():
            missing.append(dir_name)

    if missing:
        report.add_check(
            ".gitkeep Files",
            False,
            f"Missing in: {', '.join(missing)}"
        )
    else:
        report.add_check(
            ".gitkeep Files",
            True,
            f"All {len(empty_dirs)} directories have .gitkeep"
        )


def check_python_dependencies(template_dir: Path, report: ValidationReport):
    """Check Python packages have valid dependencies."""
    python_dirs = [
        'adws',
        'ipe',
    ]

    issues = []
    for dir_name in python_dirs:
        dir_path = template_dir / dir_name

        if not dir_path.exists():
            issues.append(f"{dir_name} directory not found")
            continue

        # Check for pyproject.toml or requirements.txt
        has_pyproject = (dir_path / 'pyproject.toml').exists()
        has_requirements = (dir_path / 'requirements.txt').exists()

        if not has_pyproject and not has_requirements:
            issues.append(f"{dir_name} has no pyproject.toml or requirements.txt")

    if issues:
        report.add_check(
            "Python Dependencies",
            False,
            f"Issues: {', '.join(issues)}"
        )
    else:
        report.add_check(
            "Python Dependencies",
            True,
            "All Python packages have dependency files"
        )


def check_broken_symlinks(template_dir: Path, report: ValidationReport):
    """Check for broken symlinks."""
    broken_links = []

    for path in template_dir.rglob('*'):
        if path.is_symlink() and not path.exists():
            broken_links.append(str(path.relative_to(template_dir)))

    if broken_links:
        report.add_check(
            "Broken Symlinks",
            False,
            f"Found {len(broken_links)}: {', '.join(broken_links[:5])}"
        )
    else:
        report.add_check(
            "Broken Symlinks",
            True,
            "No broken symlinks found"
        )


def validate_template(template_dir: str) -> ValidationReport:
    """Run all validation checks."""
    template_path = Path(template_dir).resolve()

    if not template_path.exists():
        print(f"Error: Template directory does not exist: {template_dir}")
        sys.exit(2)

    report = ValidationReport()

    print(f"Validating template: {template_path}\n")

    # Run all checks
    check_required_directories(template_path, report)
    check_required_files(template_path, report)
    check_settings_json(template_path, report)
    check_project_specific_content(template_path, report)
    check_terraform_syntax(template_path, report)
    check_git_repository(template_path, report)
    check_gitkeep_files(template_path, report)
    check_python_dependencies(template_path, report)
    check_broken_symlinks(template_path, report)

    return report


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate decoupled template for completeness and quality"
    )
    parser.add_argument(
        'template_dir',
        help="Template directory to validate"
    )

    args = parser.parse_args()

    report = validate_template(args.template_dir)
    report.print_report()

    sys.exit(report.exit_code())


if __name__ == '__main__':
    main()
