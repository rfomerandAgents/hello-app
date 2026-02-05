#!/usr/bin/env python3
"""
Module Migration Orchestrator
Orchestrates the extraction of existing Terraform code into modules.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.hcl_parser import HCLParser
from parsers.resource_extractor import ResourceExtractor
from parsers.variable_inferrer import VariableInferrer
from parsers.output_generator import OutputGenerator
from parsers.state_migrator import StateMigrator


class MigrationOrchestrator:
    """
    Orchestrates the migration of existing Terraform code to modules
    """

    def __init__(self, dry_run: bool = False, quiet: bool = False):
        self.dry_run = dry_run
        self.quiet = quiet

        # Initialize components
        self.parser = HCLParser()
        self.extractor = ResourceExtractor(self.parser)
        self.inferrer = VariableInferrer()
        self.output_generator = OutputGenerator()
        self.state_migrator = StateMigrator()

    def migrate(
        self,
        source_file: Path,
        module_name: str,
        resource_category: str = None,
        resource_names: list = None,
        output_path: Path = None,
        preserve_state: bool = False
    ) -> bool:
        """
        Main migration workflow

        Args:
            source_file: Path to existing Terraform file
            module_name: Name for the new module
            resource_category: Category of resources to extract (vpc, ec2, etc.)
            resource_names: Specific resource names to extract
            output_path: Where to create the module
            preserve_state: Whether to generate state migration scripts

        Returns:
            True if successful, False otherwise
        """

        try:
            # Step 1: Parse source file
            if not self.quiet:
                print(f"\n→ Parsing {source_file}...")

            parsed_file = self.parser.parse_file(source_file)

            if not self.quiet:
                print(f"  Found {len(parsed_file.resources)} resources")
                print(f"  Found {len(parsed_file.data_sources)} data sources")
                print(f"  Found {len(parsed_file.variables)} variables")

            # Step 2: Extract resources
            if not self.quiet:
                print(f"\n→ Extracting resources...")

            if resource_category:
                extraction_result = self.extractor.extract_by_type(
                    parsed_file, resource_category, include_dependencies=True
                )
            elif resource_names:
                extraction_result = self.extractor.extract_by_resource_name(
                    parsed_file, resource_names, include_dependencies=True
                )
            else:
                print("Error: Must specify either --extract or --resources")
                return False

            if not extraction_result.primary_resources:
                print(f"Error: No resources found matching criteria")
                return False

            # Display extraction summary
            summary = self.extractor.get_extraction_summary(extraction_result)
            if not self.quiet:
                print(f"  Primary resources: {summary['primary_resources']}")
                print(f"  Related resources: {summary['related_resources']}")
                print(f"  Data sources: {summary['data_sources']}")
                print(f"  Locals: {summary['locals']}")

            # Step 3: Infer variables
            if not self.quiet:
                print(f"\n→ Inferring variables...")

            variables = self.inferrer.infer_variables(extraction_result)
            var_summary = self.inferrer.get_variable_summary(variables)

            if not self.quiet:
                print(f"  Inferred {var_summary['total_variables']} variables")
                print(f"  With defaults: {var_summary['with_defaults']}")
                print(f"  With validation: {var_summary['with_validation']}")

            # Step 4: Generate outputs
            if not self.quiet:
                print(f"\n→ Generating outputs...")

            outputs = self.output_generator.infer_outputs(extraction_result)
            output_summary = self.output_generator.get_output_summary(outputs)

            if not self.quiet:
                print(f"  Generated {output_summary['total_outputs']} outputs")

            # Step 5: Generate state migration (if requested)
            migration_commands = None
            if preserve_state:
                if not self.quiet:
                    print(f"\n→ Generating state migration commands...")

                migration_commands = self.state_migrator.generate_migration_commands(
                    extraction_result,
                    module_name,
                    module_path=str(output_path) if output_path else None
                )

                migration_summary = self.state_migrator.get_migration_summary(migration_commands)
                if not self.quiet:
                    print(f"  Generated {migration_summary['total_resources']} migration commands")

            # Dry run - just print what would be done
            if self.dry_run:
                self._print_dry_run_summary(
                    extraction_result, variables, outputs, migration_commands
                )
                return True

            # Step 6: Create module directory and files
            if not output_path:
                output_path = Path.cwd() / 'terraform' / 'modules' / module_name

            if not self.quiet:
                print(f"\n→ Creating module at {output_path}...")

            # Create directories
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / 'examples' / 'basic').mkdir(parents=True, exist_ok=True)

            # Generate main.tf
            main_tf = self.extractor.generate_main_tf(extraction_result)
            (output_path / 'main.tf').write_text(main_tf)
            if not self.quiet:
                print(f"  ✓ Generated main.tf")

            # Generate variables.tf
            variables_tf = self.inferrer.generate_variables_tf(variables)
            (output_path / 'variables.tf').write_text(variables_tf)
            if not self.quiet:
                print(f"  ✓ Generated variables.tf")

            # Generate outputs.tf
            outputs_tf = self.output_generator.generate_outputs_tf(outputs)
            (output_path / 'outputs.tf').write_text(outputs_tf)
            if not self.quiet:
                print(f"  ✓ Generated outputs.tf")

            # Generate versions.tf
            versions_tf = self._generate_versions_tf()
            (output_path / 'versions.tf').write_text(versions_tf)
            if not self.quiet:
                print(f"  ✓ Generated versions.tf")

            # Generate README.md
            readme_md = self._generate_readme(module_name, variables, outputs, extraction_result)
            (output_path / 'README.md').write_text(readme_md)
            if not self.quiet:
                print(f"  ✓ Generated README.md")

            # Generate example
            example_tf = self._generate_example(module_name, variables)
            (output_path / 'examples' / 'basic' / 'main.tf').write_text(example_tf)
            if not self.quiet:
                print(f"  ✓ Generated examples/basic/main.tf")

            # Generate state migration scripts (if requested)
            if preserve_state and migration_commands:
                migration_script = self.state_migrator.generate_migration_script(
                    migration_commands, module_name
                )
                migration_file = output_path / 'migrate_state.sh'
                migration_file.write_text(migration_script)
                migration_file.chmod(0o755)

                rollback_script = self.state_migrator.generate_rollback_script(
                    migration_commands, module_name
                )
                rollback_file = output_path / 'rollback_state.sh'
                rollback_file.write_text(rollback_script)
                rollback_file.chmod(0o755)

                migration_guide = self.state_migrator.generate_migration_guide(
                    migration_commands, module_name, str(output_path.relative_to(Path.cwd()))
                )
                (output_path / 'MIGRATION.md').write_text(migration_guide)

                if not self.quiet:
                    print(f"  ✓ Generated migrate_state.sh")
                    print(f"  ✓ Generated rollback_state.sh")
                    print(f"  ✓ Generated MIGRATION.md")

            # Success summary
            self._print_success_summary(
                module_name, output_path, summary, var_summary, output_summary, preserve_state
            )

            return True

        except Exception as e:
            print(f"\n✗ Error: {e}")
            if not self.quiet:
                import traceback
                traceback.print_exc()
            return False

    def _print_dry_run_summary(self, extraction, variables, outputs, migrations):
        """Print what would be extracted (dry run mode)"""

        print("\n" + "="*60)
        print("DRY RUN - Preview of Extraction")
        print("="*60)

        print("\nPrimary Resources:")
        for resource in extraction.primary_resources:
            print(f"  - {resource.full_name}")

        if extraction.related_resources:
            print("\nRelated Resources:")
            for resource in extraction.related_resources:
                print(f"  - {resource.full_name}")

        if extraction.data_sources:
            print("\nData Sources:")
            for ds in extraction.data_sources:
                print(f"  - data.{ds.full_name}")

        print(f"\nInferred Variables ({len(variables)}):")
        for var in variables[:10]:  # Show first 10
            default_str = f' = {var.default}' if var.default else ''
            print(f"  - {var.name}: {var.type}{default_str}")
        if len(variables) > 10:
            print(f"  ... and {len(variables) - 10} more")

        print(f"\nGenerated Outputs ({len(outputs)}):")
        for output in outputs[:10]:  # Show first 10
            print(f"  - {output.name}: {output.description}")
        if len(outputs) > 10:
            print(f"  ... and {len(outputs) - 10} more")

        if migrations:
            print(f"\nState Migrations ({len(migrations)}):")
            for cmd in migrations[:5]:
                print(f"  {cmd.source} -> {cmd.destination}")
            if len(migrations) > 5:
                print(f"  ... and {len(migrations) - 5} more")

        print("\n" + "="*60)
        print("No files were created (dry run mode)")
        print("="*60)

    def _print_success_summary(
        self, module_name, output_path, resource_summary, var_summary, output_summary, has_migration
    ):
        """Print success summary"""

        print("\n" + "="*60)
        print(f"Module '{module_name}' created successfully!")
        print("="*60)

        print(f"\nLocation: {output_path}")

        print(f"\nExtracted Resources:")
        print(f"  - Primary: {resource_summary['primary_resources']}")
        print(f"  - Related: {resource_summary['related_resources']}")
        print(f"  - Data sources: {resource_summary['data_sources']}")

        print(f"\nGenerated Files:")
        print(f"  - main.tf ({resource_summary['primary_resources'] + resource_summary['related_resources']} resources)")
        print(f"  - variables.tf ({var_summary['total_variables']} variables)")
        print(f"  - outputs.tf ({output_summary['total_outputs']} outputs)")
        print(f"  - versions.tf")
        print(f"  - README.md")
        print(f"  - examples/basic/main.tf")

        if has_migration:
            print(f"  - migrate_state.sh")
            print(f"  - rollback_state.sh")
            print(f"  - MIGRATION.md")

        print(f"\nNext Steps:")
        print(f"  1. Review generated files: cd {output_path}")
        print(f"  2. Customize variables and configuration as needed")
        print(f"  3. Update root module to use this module")
        if has_migration:
            print(f"  4. Review MIGRATION.md for state migration guide")
            print(f"  5. Run migrate_state.sh to migrate state")
            print(f"  6. Verify with: terraform plan (should show no changes)")
        else:
            print(f"  4. Test the module: cd examples/basic && terraform init")

        print("\n" + "="*60)

    def _generate_versions_tf(self) -> str:
        """Generate versions.tf content"""
        return """terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
"""

    def _generate_readme(self, module_name, variables, outputs, extraction):
        """Generate README.md content"""
        lines = []
        lines.append(f"# {module_name.replace('-', ' ').title()} Module")
        lines.append("")
        lines.append("Terraform module extracted from existing infrastructure.")
        lines.append("")

        lines.append("## Usage")
        lines.append("")
        lines.append("```hcl")
        lines.append(f'module "{module_name}" {{')
        lines.append(f'  source = "./io/io/terraform/modules/{module_name}"')
        lines.append("")
        for var in variables[:5]:  # Show first 5 required variables
            if var.default is None:
                lines.append(f'  {var.name} = "value"  # {var.description}')
        lines.append("}")
        lines.append("```")
        lines.append("")

        lines.append("## Resources")
        lines.append("")
        lines.append(f"This module manages {len(extraction.primary_resources)} primary resources:")
        for resource in extraction.primary_resources:
            lines.append(f"- `{resource.full_name}`")
        lines.append("")

        if variables:
            lines.append("## Inputs")
            lines.append("")
            lines.append("| Name | Description | Type | Default | Required |")
            lines.append("|------|-------------|------|---------|:--------:|")
            for var in variables:
                required = "yes" if var.default is None else "no"
                default = var.default if var.default else "n/a"
                lines.append(f"| {var.name} | {var.description} | `{var.type}` | `{default}` | {required} |")
            lines.append("")

        if outputs:
            lines.append("## Outputs")
            lines.append("")
            lines.append("| Name | Description |")
            lines.append("|------|-------------|")
            for output in outputs:
                lines.append(f"| {output.name} | {output.description} |")
            lines.append("")

        return '\n'.join(lines)

    def _generate_example(self, module_name, variables) -> str:
        """Generate example usage"""
        lines = []
        lines.append(f'# Example usage of {module_name} module')
        lines.append("")
        lines.append(f'module "{module_name}" {{')
        lines.append(f'  source = "../../"')
        lines.append("")
        for var in variables:
            if var.default is not None:
                lines.append(f'  # {var.name} = "{var.default}"  # {var.description}')
            else:
                lines.append(f'  {var.name} = "CHANGE_ME"  # {var.description}')
        lines.append("}")
        lines.append("")
        return '\n'.join(lines)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='Extract existing Terraform code into reusable modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract EC2 resources from main.tf
  %(prog)s --from-existing=io/terraform/main.tf --extract=ec2 --name=web-servers

  # Extract specific resources
  %(prog)s --from-existing=io/terraform/main.tf --resources=aws_instance.web,aws_security_group.web --name=web-module

  # Dry run to preview extraction
  %(prog)s --from-existing=io/terraform/main.tf --extract=vpc --name=my-vpc --dry-run

  # Extract with state migration
  %(prog)s --from-existing=io/terraform/main.tf --extract=ec2 --name=compute --preserve-state
        '''
    )

    parser.add_argument(
        '--from-existing',
        required=True,
        metavar='FILE',
        help='Path to existing Terraform file to extract from'
    )

    parser.add_argument(
        '--name',
        required=True,
        metavar='NAME',
        help='Name for the new module (kebab-case)'
    )

    parser.add_argument(
        '--extract',
        metavar='CATEGORY',
        help='Resource category to extract (vpc, ec2, s3, rds, iam, eks, lambda, api-gateway, security)'
    )

    parser.add_argument(
        '--resources',
        metavar='RESOURCES',
        help='Comma-separated list of specific resources to extract (e.g., aws_instance.web,aws_security_group.web)'
    )

    parser.add_argument(
        '--path',
        metavar='PATH',
        help='Output path for module (default: io/terraform/modules/NAME)'
    )

    parser.add_argument(
        '--preserve-state',
        action='store_true',
        help='Generate state migration scripts'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview extraction without creating files'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.extract and not args.resources:
        parser.error("Must specify either --extract or --resources")

    source_file = Path(args.from_existing)
    if not source_file.exists():
        print(f"Error: File not found: {source_file}")
        sys.exit(1)

    # Parse resource names if provided
    resource_names = None
    if args.resources:
        resource_names = [r.strip() for r in args.resources.split(',')]

    # Determine output path
    output_path = None
    if args.path:
        output_path = Path(args.path)

    # Run migration
    orchestrator = MigrationOrchestrator(dry_run=args.dry_run, quiet=args.quiet)

    success = orchestrator.migrate(
        source_file=source_file,
        module_name=args.name,
        resource_category=args.extract,
        resource_names=resource_names,
        output_path=output_path,
        preserve_state=args.preserve_state
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
