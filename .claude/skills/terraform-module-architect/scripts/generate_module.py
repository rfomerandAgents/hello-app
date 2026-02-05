#!/usr/bin/env python3
"""
Terraform Module Generator
Generates Terraform modules from templates with variable substitution.
"""

import os
import sys
import re
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

__version__ = "1.0.0"


def validate_module_name(name: str) -> bool:
    """Validate module name is kebab-case format"""
    pattern = r'^[a-z0-9-]+$'
    return bool(re.match(pattern, name))


def validate_module_type(module_type: str) -> bool:
    """Validate module type is supported"""
    supported_types = [
        'custom', 'vpc', 'ec2', 's3', 'rds', 'iam', 'eks', 'lambda', 'api-gateway'
    ]
    return module_type in supported_types


def get_git_user() -> str:
    """Get git user name or return default"""
    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False
        )
        author = result.stdout.strip()
        return author if author else 'Platform Engineering Team'
    except Exception:
        return 'Platform Engineering Team'


def prepare_variables(
    name: str,
    module_type: str,
    environment: Optional[str] = None,
    description: Optional[str] = None,
    provider: Optional[str] = None,
    version: Optional[str] = None
) -> Dict[str, str]:
    """Prepare substitution variables from user input"""

    # Get git user info
    author = get_git_user()

    # Get current date in ISO 8601
    date = datetime.now().isoformat()

    # Prepare all variables
    variables = {
        'MODULE_NAME': name,
        'MODULE_NAME_UNDERSCORED': name.replace('-', '_'),
        'MODULE_TYPE': module_type,
        'ENVIRONMENT': environment or 'dev',
        'DESCRIPTION': description or f'{module_type.upper()} module',
        'AUTHOR': author,
        'DATE': date,
        'TERRAFORM_VERSION': version or '>= 1.0',
        'PROVIDER': provider or 'aws',
    }

    return variables


def load_templates(module_type: str, skill_root: Path) -> Dict[str, str]:
    """Load all template files for a module type"""

    template_dir = skill_root / 'templates' / module_type

    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        sys.exit(1)

    templates = {}

    # Walk directory tree
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.template'):
                # Get full path
                template_path = Path(root) / file

                # Read template content
                with open(template_path, 'r') as f:
                    content = f.read()

                # Calculate relative path from template_dir
                rel_path = template_path.relative_to(template_dir)

                # Store template
                templates[str(rel_path)] = content

    return templates


def substitute_variables(template_content: str, variables: Dict[str, str]) -> str:
    """Replace all {{PLACEHOLDER}} with actual values"""

    result = template_content

    # Replace each variable
    for key, value in variables.items():
        placeholder = f'{{{{{key}}}}}'  # {{VARIABLE_NAME}}
        result = result.replace(placeholder, str(value))

    return result


def check_for_undefined_variables(content: str) -> list:
    """Check if any {{VARIABLE}} placeholders remain"""
    pattern = r'\{\{([A-Z_]+)\}\}'
    matches = re.findall(pattern, content)
    return matches


def generate_files(
    templates: Dict[str, str],
    variables: Dict[str, str],
    output_path: Path,
    quiet: bool = False
) -> list:
    """Generate all files from templates"""

    generated_files = []

    for template_path, template_content in templates.items():
        # Remove .template extension
        output_file = template_path.replace('.template', '')

        # Full output path
        full_output_path = output_path / output_file

        # Create directory if needed
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        # Substitute variables
        rendered_content = substitute_variables(template_content, variables)

        # Check for undefined variables
        undefined = check_for_undefined_variables(rendered_content)
        if undefined:
            print(f"  ⚠️  Warning: Undefined variables in {output_file}: {', '.join(undefined)}")

        # Write file
        with open(full_output_path, 'w') as f:
            f.write(rendered_content)

        generated_files.append(output_file)
        if not quiet:
            print(f'  ✓ Generated {output_file}')

    return generated_files


def run_terraform_fmt(output_path: Path) -> bool:
    """Run terraform fmt on generated files"""

    try:
        result = subprocess.run(
            ['terraform', 'fmt', '-recursive', str(output_path)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print("  ✓ Formatted with terraform fmt")
            return True
        else:
            print(f"  ⚠️  terraform fmt had warnings:\n{result.stderr}")
            return False
    except FileNotFoundError:
        print("  ⚠️  terraform not found in PATH, skipping fmt")
        return False
    except Exception as e:
        print(f"  ⚠️  terraform fmt failed: {e}")
        return False


def run_terraform_validate(output_path: Path) -> bool:
    """Run terraform init and validate on generated module"""

    try:
        # Run terraform init with backend=false
        print("  → Running terraform init...")
        init_result = subprocess.run(
            ['terraform', 'init', '-backend=false'],
            cwd=output_path,
            capture_output=True,
            text=True,
            check=False
        )

        if init_result.returncode != 0:
            print(f"  ✗ terraform init failed:\n{init_result.stderr}")
            return False

        print("  ✓ terraform init succeeded")

        # Run terraform validate
        print("  → Running terraform validate...")
        validate_result = subprocess.run(
            ['terraform', 'validate'],
            cwd=output_path,
            capture_output=True,
            text=True,
            check=False
        )

        if validate_result.returncode == 0:
            print("  ✓ terraform validate succeeded")
            return True
        else:
            print(f"  ✗ terraform validate failed:\n{validate_result.stderr}")
            return False
    except FileNotFoundError:
        print("  ⚠️  terraform not found in PATH, skipping validation")
        return False
    except Exception as e:
        print(f"  ⚠️  terraform validation failed: {e}")
        return False


def count_generated_elements(output_path: Path) -> dict:
    """Count variables, outputs, and resources in generated module"""

    counts = {'variables': 0, 'outputs': 0, 'resources': 0}

    # Count variables
    variables_file = output_path / 'variables.tf'
    if variables_file.exists():
        content = variables_file.read_text()
        counts['variables'] = len(re.findall(r'variable\s+"[^"]+"', content))

    # Count outputs
    outputs_file = output_path / 'outputs.tf'
    if outputs_file.exists():
        content = outputs_file.read_text()
        counts['outputs'] = len(re.findall(r'output\s+"[^"]+"', content))

    # Count resources (approximate)
    main_file = output_path / 'main.tf'
    if main_file.exists():
        content = main_file.read_text()
        counts['resources'] = len(re.findall(r'resource\s+"[^"]+"\s+"[^"]+"', content))

    return counts


def print_summary(
    name: str,
    module_type: str,
    output_path: Path,
    generated_files: list,
    counts: dict,
    validation_passed: bool
):
    """Print generation summary"""

    print(f"\n{'='*60}")
    print(f"Module '{name}' created successfully!")
    print(f"{'='*60}")
    print(f"\nLocation: {output_path}")
    print(f"\nGenerated Files:")

    # Group files by category
    core_files = [f for f in generated_files if '/' not in f]
    example_files = [f for f in generated_files if f.startswith('examples/')]
    test_files = [f for f in generated_files if f.startswith('tests/')]

    if core_files:
        print("  Core:")
        for f in sorted(core_files):
            print(f"    - {f}")

    if example_files:
        print("  Examples:")
        for f in sorted(example_files):
            print(f"    - {f}")

    if test_files:
        print("  Tests:")
        for f in sorted(test_files):
            print(f"    - {f}")

    print(f"\nModule Statistics:")
    print(f"  - Variables: {counts['variables']} (with validation)")
    print(f"  - Outputs: {counts['outputs']}")
    print(f"  - Resources: {counts['resources']}")
    print(f"  - Validation: {'✓ Passed' if validation_passed else '✗ Failed (manual fix needed)'}")

    print(f"\nNext Steps:")
    print(f"  1. Review generated files: cd {output_path}")
    print(f"  2. Customize variables and resources as needed")
    print(f"  3. Update README with specific usage details")
    print(f"  4. Test with example: cd {output_path}/examples/basic && terraform init")
    if test_files:
        print(f"  5. Run tests: cd {output_path}/tests && go test -v")
        print(f"  6. Commit to version control")
    else:
        print(f"  5. Commit to version control")

    print(f"\nDocumentation: {output_path}/README.md")
    print(f"{'='*60}\n")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all options"""

    parser = argparse.ArgumentParser(
        prog='generate_module.py',
        description='Generate production-ready Terraform modules from templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate a custom module
  %(prog)s custom my-module

  # Generate a VPC module for production
  %(prog)s vpc app-vpc --environment prod

  # Generate with custom output path
  %(prog)s ec2 web-server --path ./io/terraform/modules

  # Generate with all options
  %(prog)s s3 data-bucket \\
    --environment staging \\
    --path ./modules \\
    --description "S3 bucket for application data" \\
    --provider aws \\
    --version ">= 1.5"

Supported Module Types:
  custom        Minimal scaffold for any resource (P0)
  vpc           Full VPC with subnets, NAT, IGW (P0)
  ec2           Compute instances with security groups (P0)
  s3            Storage buckets with encryption (P0)
  rds           Database instances with backups (P1)
  iam           Roles and policies (P1)
  eks           Kubernetes clusters (P1)
  lambda        Serverless functions (P2)
  api-gateway   REST/HTTP APIs (P2)

Generated Structure:
  module-name/
  ├── main.tf              # Primary resource definitions
  ├── variables.tf         # Input variable declarations
  ├── outputs.tf           # Output value declarations
  ├── versions.tf          # Provider version constraints
  ├── README.md            # Module documentation
  ├── CHANGELOG.md         # Version history
  ├── LICENSE              # License file
  ├── examples/            # Usage examples
  │   ├── basic/
  │   └── complete/
  └── tests/               # Automated tests
      └── basic_test.go
        '''
    )

    # Version flag
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    # Required arguments
    parser.add_argument(
        'type',
        metavar='TYPE',
        help='Module type (custom, vpc, ec2, s3, rds, iam, eks, lambda, api-gateway)'
    )

    parser.add_argument(
        'name',
        metavar='NAME',
        help='Module name in kebab-case (e.g., app-vpc, web-server)'
    )

    # Optional arguments
    parser.add_argument(
        '-e', '--environment',
        metavar='ENV',
        default='dev',
        help='Target environment (dev, staging, prod). Default: dev'
    )

    parser.add_argument(
        '-p', '--path',
        metavar='PATH',
        help='Output directory path. Default: current directory'
    )

    parser.add_argument(
        '-d', '--description',
        metavar='DESC',
        help='Module description. Default: auto-generated'
    )

    parser.add_argument(
        '--provider',
        metavar='PROVIDER',
        default='aws',
        help='Cloud provider (aws, azure, gcp). Default: aws'
    )

    parser.add_argument(
        '--tf-version',
        metavar='VERSION',
        default='>= 1.0',
        help='Terraform version constraint. Default: >= 1.0'
    )

    parser.add_argument(
        '--skip-fmt',
        action='store_true',
        help='Skip terraform fmt formatting'
    )

    parser.add_argument(
        '--skip-validate',
        action='store_true',
        help='Skip terraform validate check'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing module directory'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output (only errors and summary)'
    )

    return parser


def main():
    """Main entry point"""

    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()

    module_type = args.type
    name = args.name
    environment = args.environment
    output_path_arg = args.path
    description = args.description
    provider = args.provider
    version = args.tf_version

    # Validate inputs
    if not validate_module_type(module_type):
        print(f"Error: Invalid module type '{module_type}'")
        print("Supported types: custom, vpc, ec2, s3, rds, iam, eks, lambda, api-gateway")
        sys.exit(1)

    if not validate_module_name(name):
        print(f"Error: Invalid module name '{name}'")
        print("Module names must be kebab-case (lowercase letters, numbers, and hyphens only)")
        print("Examples: app-vpc, web-server, data-bucket")
        sys.exit(1)

    # Determine paths
    script_dir = Path(__file__).parent
    skill_root = script_dir.parent  # .claude/skills/terraform-module-architect

    if output_path_arg:
        output_path = Path(output_path_arg).resolve() / name
    else:
        output_path = Path.cwd() / name

    # Check if output directory exists
    if output_path.exists():
        if args.force:
            if not args.quiet:
                print(f"⚠️  Overwriting existing directory: {output_path}")
            import shutil
            shutil.rmtree(output_path)
        else:
            print(f"Error: Directory already exists: {output_path}")
            print("Use --force to overwrite or choose a different name")
            sys.exit(1)

    if not args.quiet:
        print(f"\nGenerating {module_type} module '{name}'...")
        print(f"Output path: {output_path}\n")

    # Prepare variables
    if not args.quiet:
        print("→ Preparing variables...")
    variables = prepare_variables(name, module_type, environment, description, provider, version)
    if not args.quiet:
        for key, value in variables.items():
            print(f"  {key}: {value}")

    # Load templates
    if not args.quiet:
        print(f"\n→ Loading templates for '{module_type}' module...")
    templates = load_templates(module_type, skill_root)
    if not args.quiet:
        print(f"  Found {len(templates)} template files")

    # Generate files
    if not args.quiet:
        print(f"\n→ Generating files...")
    generated_files = generate_files(templates, variables, output_path, args.quiet)

    # Run terraform fmt
    validation_passed = True
    if not args.skip_fmt:
        if not args.quiet:
            print(f"\n→ Formatting Terraform files...")
        run_terraform_fmt(output_path)

    # Run terraform validate
    if not args.skip_validate:
        if not args.quiet:
            print(f"\n→ Validating generated module...")
        validation_passed = run_terraform_validate(output_path)

    # Count elements
    counts = count_generated_elements(output_path)

    # Print summary (always show, even in quiet mode)
    print_summary(name, module_type, output_path, generated_files, counts, validation_passed)


if __name__ == '__main__':
    main()
