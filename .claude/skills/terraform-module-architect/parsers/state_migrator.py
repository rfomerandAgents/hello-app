#!/usr/bin/env python3
"""
State Migrator
Generates terraform state mv commands for migrating state to modules.
"""

from typing import List, Dict
from dataclasses import dataclass

from .hcl_parser import ParsedBlock
from .resource_extractor import ExtractionResult


@dataclass
class StateMigrationCommand:
    """Represents a state migration command"""
    source: str  # Original resource address
    destination: str  # New module resource address
    resource_type: str
    resource_name: str


class StateMigrator:
    """
    Generates state migration scripts for moving resources to modules
    """

    def __init__(self):
        self.commands: List[StateMigrationCommand] = []

    def generate_migration_commands(
        self,
        extraction_result: ExtractionResult,
        module_name: str,
        module_path: str = None
    ) -> List[StateMigrationCommand]:
        """
        Generate terraform state mv commands

        Args:
            extraction_result: Extracted resources
            module_name: Name of the module being created
            module_path: Path to module (for module.xxx references)

        Returns:
            List of state migration commands
        """

        self.commands = []

        # Module reference format
        if module_path:
            module_ref = f'module.{module_name}'
        else:
            module_ref = f'module.{module_name}'

        # Generate commands for primary resources
        for resource in extraction_result.primary_resources:
            self._generate_command(resource, module_ref)

        # Generate commands for related resources
        for resource in extraction_result.related_resources:
            self._generate_command(resource, module_ref)

        return self.commands

    def _generate_command(self, resource: ParsedBlock, module_ref: str):
        """Generate migration command for a single resource"""

        source = f'{resource.resource_type}.{resource.name}'
        destination = f'{module_ref}.{resource.resource_type}.{resource.name}'

        command = StateMigrationCommand(
            source=source,
            destination=destination,
            resource_type=resource.resource_type,
            resource_name=resource.name
        )

        self.commands.append(command)

    def generate_migration_script(
        self,
        commands: List[StateMigrationCommand],
        module_name: str,
        include_rollback: bool = True
    ) -> str:
        """
        Generate shell script for state migration

        Args:
            commands: List of migration commands
            module_name: Name of the module
            include_rollback: Whether to include rollback commands

        Returns:
            Shell script content
        """

        lines = []

        # Header
        lines.append("#!/bin/bash")
        lines.append("#")
        lines.append(f"# State Migration Script for {module_name} Module")
        lines.append("#")
        lines.append("# This script migrates Terraform state from root to module")
        lines.append("# WARNING: Always backup your state before running this!")
        lines.append("#")
        lines.append("# Usage:")
        lines.append("#   1. Review this script carefully")
        lines.append("#   2. Backup state: terraform state pull > backup.tfstate")
        lines.append("#   3. Run migration: bash migrate_state.sh")
        lines.append("#   4. Verify: terraform plan (should show no changes)")
        lines.append("#")
        lines.append("")

        # Safety check
        lines.append("set -e  # Exit on error")
        lines.append("set -u  # Exit on undefined variable")
        lines.append("")

        # Colors for output
        lines.append("RED='\\033[0;31m'")
        lines.append("GREEN='\\033[0;32m'")
        lines.append("YELLOW='\\033[1;33m'")
        lines.append("NC='\\033[0m'  # No Color")
        lines.append("")

        # Confirmation prompt
        lines.append("echo \"${YELLOW}WARNING: This will modify your Terraform state!${NC}\"")
        lines.append("echo \"Make sure you have a backup of your state file.\"")
        lines.append("echo \"\"")
        lines.append("read -p \"Do you want to continue? (yes/no): \" -r")
        lines.append("if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then")
        lines.append("    echo \"${RED}Migration cancelled${NC}\"")
        lines.append("    exit 1")
        lines.append("fi")
        lines.append("")

        # Create backup
        lines.append("echo \"${GREEN}Creating state backup...${NC}\"")
        lines.append("terraform state pull > state_backup_$(date +%Y%m%d_%H%M%S).tfstate")
        lines.append("echo \"${GREEN}Backup created${NC}\"")
        lines.append("")

        # Migration commands
        lines.append("echo \"${GREEN}Starting state migration...${NC}\"")
        lines.append("")

        for i, cmd in enumerate(commands, 1):
            lines.append(f"# Migrate {cmd.resource_type}.{cmd.resource_name}")
            lines.append(f"echo \"[{i}/{len(commands)}] Migrating {cmd.source} -> {cmd.destination}\"")
            lines.append(f"terraform state mv '{cmd.source}' '{cmd.destination}' || {{")
            lines.append(f"    echo \"${{RED}}Failed to migrate {cmd.source}${{NC}}\"")
            lines.append("    exit 1")
            lines.append("}")
            lines.append("")

        # Success message
        lines.append("echo \"${GREEN}Migration completed successfully!${NC}\"")
        lines.append("echo \"\"")
        lines.append("echo \"Next steps:\"")
        lines.append("echo \"  1. Run 'terraform plan' to verify no changes are needed\"")
        lines.append("echo \"  2. If plan shows unexpected changes, review the module configuration\"")
        lines.append("echo \"  3. Keep the backup file until you verify everything works\"")
        lines.append("")

        # Rollback section
        if include_rollback:
            lines.append("# ROLLBACK COMMANDS (if needed)")
            lines.append("# If something goes wrong, run these commands to revert:")
            lines.append("#")
            for cmd in reversed(commands):
                lines.append(f"# terraform state mv '{cmd.destination}' '{cmd.source}'")
            lines.append("")

        return '\n'.join(lines)

    def generate_rollback_script(
        self,
        commands: List[StateMigrationCommand],
        module_name: str
    ) -> str:
        """
        Generate rollback script to undo migration

        Args:
            commands: List of migration commands
            module_name: Name of the module

        Returns:
            Shell script content for rollback
        """

        lines = []

        lines.append("#!/bin/bash")
        lines.append("#")
        lines.append(f"# State Migration Rollback Script for {module_name} Module")
        lines.append("#")
        lines.append("# This script reverts the state migration")
        lines.append("#")
        lines.append("")

        lines.append("set -e")
        lines.append("set -u")
        lines.append("")

        lines.append("echo \"Rolling back state migration...\"")
        lines.append("")

        # Reverse the commands
        for i, cmd in enumerate(reversed(commands), 1):
            lines.append(f"# Rollback {cmd.resource_type}.{cmd.resource_name}")
            lines.append(f"echo \"[{i}/{len(commands)}] Rolling back {cmd.destination} -> {cmd.source}\"")
            lines.append(f"terraform state mv '{cmd.destination}' '{cmd.source}'")
            lines.append("")

        lines.append("echo \"Rollback completed!\"")
        lines.append("")

        return '\n'.join(lines)

    def generate_migration_guide(
        self,
        commands: List[StateMigrationCommand],
        module_name: str,
        module_path: str
    ) -> str:
        """
        Generate markdown guide for state migration

        Args:
            commands: Migration commands
            module_name: Name of module
            module_path: Path to module

        Returns:
            Markdown documentation
        """

        lines = []

        lines.append(f"# State Migration Guide: {module_name}")
        lines.append("")
        lines.append("## Overview")
        lines.append("")
        lines.append(f"This guide explains how to migrate {len(commands)} resources from root module to `{module_name}` module.")
        lines.append("")

        lines.append("## Prerequisites")
        lines.append("")
        lines.append("1. Terraform is installed and configured")
        lines.append("2. You have access to modify Terraform state")
        lines.append("3. The new module has been created and configured")
        lines.append("4. You have reviewed the module configuration")
        lines.append("")

        lines.append("## Resources to Migrate")
        lines.append("")
        lines.append("| Resource Type | Resource Name | New Address |")
        lines.append("|---------------|---------------|-------------|")
        for cmd in commands:
            lines.append(f"| `{cmd.resource_type}` | `{cmd.resource_name}` | `{cmd.destination}` |")
        lines.append("")

        lines.append("## Migration Steps")
        lines.append("")
        lines.append("### 1. Backup Current State")
        lines.append("")
        lines.append("```bash")
        lines.append("# Create a backup of current state")
        lines.append("terraform state pull > state_backup_$(date +%Y%m%d_%H%M%S).tfstate")
        lines.append("```")
        lines.append("")

        lines.append("### 2. Update Terraform Configuration")
        lines.append("")
        lines.append("Add the module to your root Terraform configuration:")
        lines.append("")
        lines.append("```hcl")
        lines.append(f'module "{module_name}" {{')
        lines.append(f'  source = "./{module_path}"')
        lines.append("")
        lines.append("  # Configure module variables here")
        lines.append("  # ...")
        lines.append("}")
        lines.append("```")
        lines.append("")

        lines.append("### 3. Run Migration Script")
        lines.append("")
        lines.append("```bash")
        lines.append("# Review the script first!")
        lines.append("cat migrate_state.sh")
        lines.append("")
        lines.append("# Make it executable")
        lines.append("chmod +x migrate_state.sh")
        lines.append("")
        lines.append("# Run the migration")
        lines.append("./migrate_state.sh")
        lines.append("```")
        lines.append("")

        lines.append("### 4. Verify Migration")
        lines.append("")
        lines.append("```bash")
        lines.append("# Plan should show no changes")
        lines.append("terraform plan")
        lines.append("```")
        lines.append("")
        lines.append("**Expected output**: `No changes. Your infrastructure matches the configuration.`")
        lines.append("")

        lines.append("## Rollback")
        lines.append("")
        lines.append("If something goes wrong:")
        lines.append("")
        lines.append("```bash")
        lines.append("# Option 1: Use rollback script")
        lines.append("chmod +x rollback_state.sh")
        lines.append("./rollback_state.sh")
        lines.append("")
        lines.append("# Option 2: Restore from backup")
        lines.append("terraform state push state_backup_YYYYMMDD_HHMMSS.tfstate")
        lines.append("```")
        lines.append("")

        lines.append("## Troubleshooting")
        lines.append("")
        lines.append("### Error: Resource not found")
        lines.append("- Verify resource exists: `terraform state list`")
        lines.append("- Check resource names match exactly")
        lines.append("")
        lines.append("### Plan shows changes after migration")
        lines.append("- Review module variable values")
        lines.append("- Check for differences in resource configuration")
        lines.append("- Ensure all dependencies are included in module")
        lines.append("")

        return '\n'.join(lines)

    def get_migration_summary(self, commands: List[StateMigrationCommand]) -> Dict[str, any]:
        """Get summary of migration"""

        summary = {
            'total_resources': len(commands),
            'by_type': {},
            'resources': [
                {
                    'source': cmd.source,
                    'destination': cmd.destination,
                    'type': cmd.resource_type
                }
                for cmd in commands
            ]
        }

        # Count by resource type
        for cmd in commands:
            res_type = cmd.resource_type
            summary['by_type'][res_type] = summary['by_type'].get(res_type, 0) + 1

        return summary
