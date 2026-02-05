#!/usr/bin/env python3
"""
HCL Parser for Terraform Files
Parses Terraform .tf files and builds Abstract Syntax Tree (AST) for analysis.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field


@dataclass
class ParsedBlock:
    """Represents a parsed HCL block (resource, variable, data, etc.)"""
    block_type: str  # resource, variable, data, output, locals, module
    resource_type: Optional[str] = None  # e.g., aws_instance
    name: str = ""  # Resource name
    attributes: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # References to other resources
    line_number: int = 0
    raw_content: str = ""

    @property
    def full_name(self) -> str:
        """Get full resource name (e.g., aws_instance.web)"""
        if self.resource_type and self.name:
            return f"{self.resource_type}.{self.name}"
        return self.name

    @property
    def reference_name(self) -> str:
        """Get reference name used in interpolations"""
        if self.block_type == "resource":
            return f"{self.resource_type}.{self.name}"
        elif self.block_type == "data":
            return f"data.{self.resource_type}.{self.name}"
        elif self.block_type == "variable":
            return f"var.{self.name}"
        elif self.block_type == "output":
            return f"output.{self.name}"
        elif self.block_type == "locals":
            return f"local.{self.name}"
        elif self.block_type == "module":
            return f"module.{self.name}"
        return self.name


@dataclass
class ParsedFile:
    """Represents a parsed Terraform file"""
    path: Path
    resources: List[ParsedBlock] = field(default_factory=list)
    data_sources: List[ParsedBlock] = field(default_factory=list)
    variables: List[ParsedBlock] = field(default_factory=list)
    outputs: List[ParsedBlock] = field(default_factory=list)
    locals: List[ParsedBlock] = field(default_factory=list)
    modules: List[ParsedBlock] = field(default_factory=list)
    providers: List[ParsedBlock] = field(default_factory=list)
    terraform_blocks: List[ParsedBlock] = field(default_factory=list)

    @property
    def all_blocks(self) -> List[ParsedBlock]:
        """Get all blocks from the file"""
        return (self.resources + self.data_sources + self.variables +
                self.outputs + self.locals + self.modules +
                self.providers + self.terraform_blocks)

    def get_resource_by_name(self, name: str) -> Optional[ParsedBlock]:
        """Find a resource by its full name (e.g., aws_instance.web)"""
        for resource in self.resources:
            if resource.full_name == name:
                return resource
        return None

    def get_data_source_by_name(self, name: str) -> Optional[ParsedBlock]:
        """Find a data source by its full name"""
        for ds in self.data_sources:
            if ds.full_name == name:
                return ds
        return None


class HCLParser:
    """
    Parser for Terraform HCL files
    Uses simple regex-based parsing for basic extraction
    Falls back to terraform show -json for complex cases
    """

    def __init__(self):
        self.current_file: Optional[Path] = None
        self.current_line: int = 0

    def parse_file(self, file_path: Path) -> ParsedFile:
        """Parse a Terraform .tf file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.current_file = file_path
        content = file_path.read_text()

        parsed_file = ParsedFile(path=file_path)

        # Parse different block types
        parsed_file.resources = self._parse_resources(content)
        parsed_file.data_sources = self._parse_data_sources(content)
        parsed_file.variables = self._parse_variables(content)
        parsed_file.outputs = self._parse_outputs(content)
        parsed_file.locals = self._parse_locals(content)
        parsed_file.modules = self._parse_modules(content)
        parsed_file.providers = self._parse_providers(content)
        parsed_file.terraform_blocks = self._parse_terraform_blocks(content)

        # Extract dependencies for all blocks
        self._extract_dependencies(parsed_file)

        return parsed_file

    def _parse_resources(self, content: str) -> List[ParsedBlock]:
        """Parse resource blocks"""
        resources = []

        # Pattern: resource "type" "name" { ... }
        pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            resource_type = match.group(1)
            name = match.group(2)
            body = match.group(3)

            # Get line number
            line_number = content[:match.start()].count('\n') + 1

            # Parse attributes
            attributes = self._parse_attributes(body)

            resource = ParsedBlock(
                block_type="resource",
                resource_type=resource_type,
                name=name,
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            resources.append(resource)

        return resources

    def _parse_data_sources(self, content: str) -> List[ParsedBlock]:
        """Parse data source blocks"""
        data_sources = []

        # Pattern: data "type" "name" { ... }
        pattern = r'data\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            resource_type = match.group(1)
            name = match.group(2)
            body = match.group(3)

            line_number = content[:match.start()].count('\n') + 1
            attributes = self._parse_attributes(body)

            data_source = ParsedBlock(
                block_type="data",
                resource_type=resource_type,
                name=name,
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            data_sources.append(data_source)

        return data_sources

    def _parse_variables(self, content: str) -> List[ParsedBlock]:
        """Parse variable blocks"""
        variables = []

        # Pattern: variable "name" { ... }
        pattern = r'variable\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)

            line_number = content[:match.start()].count('\n') + 1
            attributes = self._parse_attributes(body)

            variable = ParsedBlock(
                block_type="variable",
                name=name,
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            variables.append(variable)

        return variables

    def _parse_outputs(self, content: str) -> List[ParsedBlock]:
        """Parse output blocks"""
        outputs = []

        # Pattern: output "name" { ... }
        pattern = r'output\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)

            line_number = content[:match.start()].count('\n') + 1
            attributes = self._parse_attributes(body)

            output = ParsedBlock(
                block_type="output",
                name=name,
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            outputs.append(output)

        return outputs

    def _parse_locals(self, content: str) -> List[ParsedBlock]:
        """Parse locals blocks"""
        locals_blocks = []

        # Pattern: locals { name = value ... }
        pattern = r'locals\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            body = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Parse individual local variables
            local_pattern = r'(\w+)\s*=\s*([^#\n]+(?:\n\s+[^#\n]+)*)'
            for local_match in re.finditer(local_pattern, body):
                name = local_match.group(1).strip()
                value = local_match.group(2).strip()

                local_block = ParsedBlock(
                    block_type="locals",
                    name=name,
                    attributes={"value": value},
                    line_number=line_number,
                    raw_content=f"{name} = {value}"
                )

                locals_blocks.append(local_block)

        return locals_blocks

    def _parse_modules(self, content: str) -> List[ParsedBlock]:
        """Parse module blocks"""
        modules = []

        # Pattern: module "name" { ... }
        pattern = r'module\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)

            line_number = content[:match.start()].count('\n') + 1
            attributes = self._parse_attributes(body)

            module = ParsedBlock(
                block_type="module",
                name=name,
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            modules.append(module)

        return modules

    def _parse_providers(self, content: str) -> List[ParsedBlock]:
        """Parse provider blocks"""
        providers = []

        # Pattern: provider "name" { ... } or provider "name" "alias" { ... }
        pattern = r'provider\s+"([^"]+)"(?:\s+"([^"]+)")?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            alias = match.group(2) if match.group(2) else ""
            body = match.group(3)

            line_number = content[:match.start()].count('\n') + 1
            attributes = self._parse_attributes(body)

            if alias:
                attributes['alias'] = alias

            provider = ParsedBlock(
                block_type="provider",
                name=name,
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            providers.append(provider)

        return providers

    def _parse_terraform_blocks(self, content: str) -> List[ParsedBlock]:
        """Parse terraform configuration blocks"""
        terraform_blocks = []

        # Pattern: terraform { ... }
        pattern = r'terraform\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            body = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            attributes = self._parse_attributes(body)

            terraform_block = ParsedBlock(
                block_type="terraform",
                name="terraform",
                attributes=attributes,
                line_number=line_number,
                raw_content=match.group(0)
            )

            terraform_blocks.append(terraform_block)

        return terraform_blocks

    def _parse_attributes(self, body: str) -> Dict[str, Any]:
        """Parse attributes from a block body (simplified version)"""
        attributes = {}

        # Simple key = value pattern (doesn't handle nested blocks perfectly)
        # This is intentionally simplified - for complex cases, use terraform show -json
        pattern = r'(\w+)\s*=\s*(.+?)(?=\n\s*\w+\s*=|\n\s*\}|$)'

        for match in re.finditer(pattern, body, re.MULTILINE | re.DOTALL):
            key = match.group(1).strip()
            value = match.group(2).strip()

            # Remove trailing comments
            value = re.sub(r'\s*#.*$', '', value, flags=re.MULTILINE)
            value = value.strip()

            # Store raw value (we'll parse it more carefully if needed)
            attributes[key] = value

        return attributes

    def _extract_dependencies(self, parsed_file: ParsedFile):
        """Extract resource dependencies from all blocks"""

        # Patterns for different reference types
        patterns = {
            'resource': r'(?:^|[^\w])([a-z_]+\.[a-z_][a-z0-9_]*)',  # resource_type.name
            'data': r'data\.([a-z_]+\.[a-z_][a-z0-9_]*)',  # data.type.name
            'variable': r'var\.([a-z_][a-z0-9_]*)',  # var.name
            'local': r'local\.([a-z_][a-z0-9_]*)',  # local.name
            'module': r'module\.([a-z_][a-z0-9_]*)',  # module.name
        }

        for block in parsed_file.all_blocks:
            dependencies = set()

            # Search in attributes and raw content
            search_text = block.raw_content

            # Find resource references
            for ref_type, pattern in patterns.items():
                for match in re.finditer(pattern, search_text):
                    ref = match.group(1)

                    if ref_type == 'resource':
                        # Check if this is actually a resource (not the current one)
                        full_ref = ref
                        if full_ref != block.full_name:
                            dependencies.add(full_ref)
                    elif ref_type == 'data':
                        dependencies.add(f"data.{ref}")
                    elif ref_type == 'variable':
                        dependencies.add(f"var.{ref}")
                    elif ref_type == 'local':
                        dependencies.add(f"local.{ref}")
                    elif ref_type == 'module':
                        dependencies.add(f"module.{ref}")

            block.dependencies = sorted(list(dependencies))

    def get_resource_type_category(self, resource_type: str) -> str:
        """Categorize resource types for extraction purposes"""

        # VPC resources
        if any(x in resource_type for x in ['vpc', 'subnet', 'internet_gateway', 'nat_gateway',
                                              'route_table', 'network_acl', 'vpc_endpoint']):
            return 'vpc'

        # Compute resources
        if any(x in resource_type for x in ['instance', 'launch_template', 'autoscaling',
                                              'launch_configuration', 'placement_group']):
            return 'ec2'

        # Storage resources
        if any(x in resource_type for x in ['s3_bucket', 'ebs_volume', 'efs']):
            return 's3' if 's3' in resource_type else 'storage'

        # Database resources
        if any(x in resource_type for x in ['db_instance', 'db_subnet', 'rds', 'dynamodb',
                                              'elasticache', 'redshift']):
            return 'rds'

        # IAM resources
        if any(x in resource_type for x in ['iam_role', 'iam_policy', 'iam_user', 'iam_group',
                                              'iam_instance_profile']):
            return 'iam'

        # Security resources
        if any(x in resource_type for x in ['security_group', 'network_interface', 'key_pair',
                                              'eip', 'elastic_ip']):
            return 'security'

        # EKS resources
        if any(x in resource_type for x in ['eks_cluster', 'eks_node']):
            return 'eks'

        # Lambda resources
        if any(x in resource_type for x in ['lambda_function', 'lambda_']):
            return 'lambda'

        # API Gateway resources
        if any(x in resource_type for x in ['api_gateway', 'apigatewayv2']):
            return 'api-gateway'

        return 'custom'

    def detect_hardcoded_values(self, content: str) -> Dict[str, List[str]]:
        """Detect common hardcoded values that should be variables"""

        hardcoded = {
            'instance_types': [],
            'cidr_blocks': [],
            'ports': [],
            'ami_ids': [],
            'availability_zones': [],
            'names': [],
        }

        # Instance types
        instance_pattern = r'"(t[23]\.[a-z0-9]+|m[456]\.[a-z0-9]+|c[456]\.[a-z0-9]+)"'
        hardcoded['instance_types'] = list(set(re.findall(instance_pattern, content)))

        # CIDR blocks
        cidr_pattern = r'"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})"'
        hardcoded['cidr_blocks'] = list(set(re.findall(cidr_pattern, content)))

        # Port numbers (common ones)
        port_pattern = r'(?:port|from_port|to_port)\s*=\s*(\d+)'
        hardcoded['ports'] = list(set(re.findall(port_pattern, content)))

        # AMI IDs
        ami_pattern = r'"(ami-[a-f0-9]{8,})"'
        hardcoded['ami_ids'] = list(set(re.findall(ami_pattern, content)))

        # Availability zones
        az_pattern = r'"(us-[a-z]+-\d+[a-z]|eu-[a-z]+-\d+[a-z])"'
        hardcoded['availability_zones'] = list(set(re.findall(az_pattern, content)))

        return hardcoded
