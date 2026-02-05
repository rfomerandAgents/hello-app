#!/usr/bin/env python3
"""
Code Decoupler Script

Automates the process of decoupling a project repository into a genericized template.
Extracts reusable automation patterns while removing project-specific content.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


# Directory mapping configuration
FULL_COPY_DIRS = [
    '.claude/commands',
    '.claude/agents',
    '.claude/hooks',
    '.claude/skills',
    'adws',
    'app_docs',
    'ipe',
    'scripts',
    'triggers',
    'mcp',
]

STRUCTURE_ONLY_DIRS = [
    'app',
    'ipe_logs',
    'logs',
    'agents',
    'trees',
]

SPECS_SUBDIRS = [
    'specs/high-level',
    'specs/medium-level',
    'specs/low-level',
]

# Files to exclude during copy
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.venv',
    '.pytest_cache',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
    'Thumbs.db',
    '*.log',
    '.git',
    'node_modules',
]


def log(message: str, level: str = "INFO", verbose: bool = True):
    """Print log message with level."""
    if not verbose and level == "DEBUG":
        return

    symbols = {
        "INFO": "✓",
        "WARN": "⚠",
        "ERROR": "✗",
        "DEBUG": "→",
    }

    symbol = symbols.get(level, "·")
    print(f"{symbol} {message}")


def validate_source(source_dir: Path, verbose: bool = True) -> bool:
    """Validate source directory is suitable for decoupling."""
    log("Validating source directory...", "INFO", verbose)

    if not source_dir.exists():
        log(f"Source directory does not exist: {source_dir}", "ERROR", verbose)
        return False

    if not (source_dir / ".git").exists():
        log(f"Source is not a git repository: {source_dir}", "ERROR", verbose)
        return False

    if not (source_dir / ".claude").exists():
        log("Source does not have .claude/ directory", "ERROR", verbose)
        return False

    # Check git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=source_dir,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            log("Source has uncommitted changes (continuing anyway)", "WARN", verbose)
    except subprocess.CalledProcessError:
        log("Could not check git status", "WARN", verbose)

    log("Source validation passed", "INFO", verbose)
    return True


def prepare_target(target_dir: Path, force: bool = False, verbose: bool = True) -> bool:
    """Prepare target directory for decoupling."""
    log("Preparing target directory...", "INFO", verbose)

    target_dir.mkdir(parents=True, exist_ok=True)

    # Check if target is empty
    if any(target_dir.iterdir()):
        if not force:
            log("Target directory is not empty. Use --force to overwrite", "ERROR", verbose)
            return False
        else:
            log("Target directory is not empty, but --force specified", "WARN", verbose)

    # Initialize git repository
    if not (target_dir / ".git").exists():
        try:
            subprocess.run(
                ["git", "init"],
                cwd=target_dir,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "Initial commit"],
                cwd=target_dir,
                capture_output=True,
                check=True
            )
            log("Initialized git repository in target", "INFO", verbose)
        except subprocess.CalledProcessError as e:
            log(f"Could not initialize git repository: {e}", "WARN", verbose)

    return True


def should_exclude(path: Path) -> bool:
    """Check if path should be excluded from copy."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith('*'):
            if path.suffix == pattern[1:]:
                return True
        elif pattern in str(path):
            return True
    return False


def copy_directory_full(src: Path, dst: Path, verbose: bool = True):
    """Copy directory with all files, excluding patterns."""
    if not src.exists():
        log(f"Skipping {src.name} (not found in source)", "WARN", verbose)
        return

    log(f"Copying {src.name}...", "DEBUG", verbose)

    # Create destination parent directory
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Copy directory tree
    try:
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=lambda dir, files: [
                f for f in files
                if should_exclude(Path(dir) / f)
            ]
        )
        log(f"Copied {src.name}", "INFO", verbose)
    except Exception as e:
        log(f"Error copying {src.name}: {e}", "ERROR", verbose)


def create_directory_structure(dst: Path, verbose: bool = True):
    """Create empty directory with .gitkeep."""
    dst.mkdir(parents=True, exist_ok=True)
    (dst / '.gitkeep').touch()
    log(f"Created empty directory {dst.name}", "INFO", verbose)


def genericize_readme(src_readme: Path, dst_readme: Path, verbose: bool = True):
    """Transform README.md with placeholder replacements."""
    if not src_readme.exists():
        log("Source README.md not found, skipping", "WARN", verbose)
        return

    log("Genericizing README.md...", "INFO", verbose)

    content = src_readme.read_text()

    # Text replacements
    replacements = {
        # Standard placeholders - update these for your project
        '{{PROJECT_NAME}}': '{{PROJECT_NAME}}',
        '{{PROJECT_DOMAIN}}': '{{DOMAIN}}',
        '{{PROJECT_SLUG}}': '{{PROJECT_NAME_SLUG}}',
        # Add project-specific replacements below:
        # 'Your Project Description': '{{PROJECT_DESCRIPTION}}',
        '{{GITHUB_REPO_URL}}': '{{GITHUB_REPO_URL}}',
        # 'your-github-username': '{{GITHUB_OWNER}}',
        'Port 3000': '{{APP_PORT}}',
        'Port 18333': '{{CONTROL_PLANE_PORT}}',
    }

    for find, replace in replacements.items():
        content = content.replace(find, replace)

    dst_readme.write_text(content)
    log("README.md genericized", "INFO", verbose)


def genericize_settings(src_settings: Path, dst_settings: Path, verbose: bool = True):
    """Copy settings.json with secrets removed."""
    if not src_settings.exists():
        log("Source settings.json not found, skipping", "WARN", verbose)
        return

    log("Genericizing .claude/settings.json...", "INFO", verbose)

    with src_settings.open('r') as f:
        settings = json.load(f)

    # Remove potential secrets
    if 'apiKeys' in settings:
        del settings['apiKeys']
        log("Removed apiKeys from settings.json", "WARN", verbose)

    if 'secrets' in settings:
        del settings['secrets']
        log("Removed secrets from settings.json", "WARN", verbose)

    # Ensure directory exists
    dst_settings.parent.mkdir(parents=True, exist_ok=True)

    with dst_settings.open('w') as f:
        json.dump(settings, f, indent=2)

    log(".claude/settings.json genericized", "INFO", verbose)


def create_terraform_scaffold(target_dir: Path, verbose: bool = True):
    """Generate Terraform scaffolding."""
    log("Creating Terraform scaffolding...", "INFO", verbose)

    terraform_dir = target_dir / 'terraform'
    terraform_dir.mkdir(parents=True, exist_ok=True)

    # Read templates from the skill's references
    skill_dir = Path(__file__).parent.parent
    scaffold_ref = skill_dir / 'references' / 'terraform_scaffolding.md'

    # For now, create basic templates inline
    # TODO: Extract from terraform_scaffolding.md

    # Create main.tf
    main_tf = terraform_dir / 'main.tf'
    main_tf.write_text("""# {{PROJECT_NAME}} Infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Add your resources here
# See io/terraform/README.md for examples
""")

    # Create variables.tf
    variables_tf = terraform_dir / 'variables.tf'
    variables_tf.write_text("""# Common Variables for {{PROJECT_NAME}}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "{{PROJECT_NAME_LOWER}}"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}
""")

    # Create outputs.tf
    outputs_tf = terraform_dir / 'outputs.tf'
    outputs_tf.write_text("""# Outputs for {{PROJECT_NAME}}

# Add your outputs here
""")

    # Create terraform.tf
    terraform_tf = terraform_dir / 'terraform.tf'
    terraform_tf.write_text("""# Terraform Backend Configuration

terraform {
  required_version = ">= 1.0"

  # Uncomment to use Terraform Cloud
  # cloud {
  #   organization = "{{ORGANIZATION}}"
  #   workspaces {
  #     name = "{{PROJECT_NAME_LOWER}}"
  #   }
  # }
}
""")

    # Create .gitignore
    gitignore = terraform_dir / '.gitignore'
    gitignore.write_text("""*.tfstate
*.tfstate.*
*.tfvars
!terraform.tfvars.example
.terraform/
.terraform.lock.hcl
logs/*.log
""")

    # Create README.md
    readme = terraform_dir / 'README.md'
    readme.write_text("""# {{PROJECT_NAME}} Infrastructure

This directory contains Terraform infrastructure code.

## Quick Start

1. Configure variables in `terraform.tfvars`
2. Run `terraform init`
3. Run `terraform plan`
4. Run `terraform apply`

See project README for detailed documentation.
""")

    # Create packer directory
    packer_dir = terraform_dir / 'packer'
    packer_dir.mkdir(exist_ok=True)
    (packer_dir / 'scripts').mkdir(exist_ok=True)
    (packer_dir / 'scripts' / '.gitkeep').touch()

    # Create scripts directory
    scripts_dir = terraform_dir / 'scripts'
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / '.gitkeep').touch()

    log("Terraform scaffolding created", "INFO", verbose)


def create_specs_readme(specs_dir: Path):
    """Create README for specs directory."""
    readme_content = """# Specifications

This directory contains specification documents at different abstraction levels.

## Directory Structure

- `high-level/` - Business requirements, user stories, conceptual designs
- `medium-level/` - Architecture designs, component specifications, API contracts
- `low-level/` - Detailed implementation plans, code-level specifications

## Usage

1. Create high-level spec first (what to build, why)
2. Create medium-level spec (how to architect it)
3. Create low-level spec (detailed implementation plan)
4. Use specs as input for /feature, /bug, /chore commands
"""

    readme = specs_dir / 'README.md'
    readme.write_text(readme_content)


def decouple(
    source_dir: str,
    target_dir: str,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = True
) -> int:
    """Main decoupling orchestration."""
    source_path = Path(source_dir).resolve()
    target_path = Path(target_dir).resolve()

    log(f"Decoupling {source_path} -> {target_path}", "INFO", verbose)

    if dry_run:
        log("DRY RUN MODE - No changes will be made", "WARN", verbose)

    # Step 1: Validate source
    if not validate_source(source_path, verbose):
        return 1

    # Step 2: Prepare target
    if not dry_run:
        if not prepare_target(target_path, force, verbose):
            return 1

    # Step 3: Full copy directories
    log("Copying reusable directories...", "INFO", verbose)
    for dir_name in FULL_COPY_DIRS:
        src = source_path / dir_name
        dst = target_path / dir_name
        if not dry_run:
            copy_directory_full(src, dst, verbose)
        else:
            log(f"Would copy {dir_name}", "DEBUG", verbose)

    # Step 4: Create empty structures
    log("Creating empty directory structures...", "INFO", verbose)
    for dir_name in STRUCTURE_ONLY_DIRS:
        dst = target_path / dir_name
        if not dry_run:
            create_directory_structure(dst, verbose)
        else:
            log(f"Would create empty {dir_name}", "DEBUG", verbose)

    # Create specs subdirectories
    for dir_name in SPECS_SUBDIRS:
        dst = target_path / dir_name
        if not dry_run:
            create_directory_structure(dst, verbose)
        else:
            log(f"Would create {dir_name}", "DEBUG", verbose)

    if not dry_run:
        create_specs_readme(target_path / 'specs')

    # Step 5: Terraform scaffolding
    if not dry_run:
        create_terraform_scaffold(target_path, verbose)
    else:
        log("Would create Terraform scaffolding", "DEBUG", verbose)

    # Step 6: Genericize files
    log("Genericizing configuration files...", "INFO", verbose)
    if not dry_run:
        genericize_readme(
            source_path / 'README.md',
            target_path / 'README.md',
            verbose
        )
        genericize_settings(
            source_path / '.claude' / 'settings.json',
            target_path / '.claude' / 'settings.json',
            verbose
        )

        # Copy .gitignore
        if (source_path / '.gitignore').exists():
            shutil.copy2(source_path / '.gitignore', target_path / '.gitignore')
            log("Copied .gitignore", "INFO", verbose)
    else:
        log("Would genericize README.md", "DEBUG", verbose)
        log("Would genericize settings.json", "DEBUG", verbose)
        log("Would copy .gitignore", "DEBUG", verbose)

    # Step 7: Create initial commit
    if not dry_run and (target_path / '.git').exists():
        try:
            subprocess.run(
                ['git', 'add', '.'],
                cwd=target_path,
                capture_output=True,
                check=True
            )

            commit_msg = """Initial commit - Genericized template

This template was created by decoupling reusable automation patterns.

Components:
- AI Developer Workflow (ADW) system
- Infrastructure Platform Engineer (IPE) workflows
- Claude Code CLI integration
- GitHub Actions deployment pipelines
- Terraform infrastructure templates
"""

            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=target_path,
                capture_output=True,
                check=True
            )
            log("Created initial git commit", "INFO", verbose)
        except subprocess.CalledProcessError as e:
            log(f"Could not create git commit: {e}", "WARN", verbose)

    log("Decoupling complete!", "INFO", verbose)
    log(f"Template created at: {target_path}", "INFO", verbose)

    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Decouple project repository into genericized template"
    )
    parser.add_argument(
        '--source',
        required=True,
        help="Source repository directory"
    )
    parser.add_argument(
        '--target',
        required=True,
        help="Target template directory"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Preview actions without making changes"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Overwrite target directory if not empty"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help="Verbose output (default: True)"
    )

    args = parser.parse_args()

    exit_code = decouple(
        source_dir=args.source,
        target_dir=args.target,
        dry_run=args.dry_run,
        force=args.force,
        verbose=args.verbose
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
