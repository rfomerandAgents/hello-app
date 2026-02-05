#!/usr/bin/env python3
"""
Variable Inferrer
Detects hardcoded values and generates variable definitions with validation rules.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

from .hcl_parser import ParsedBlock
from .resource_extractor import ExtractionResult


@dataclass
class InferredVariable:
    """Represents an inferred variable"""
    name: str
    type: str  # string, number, bool, list(string), etc.
    description: str
    default: Optional[str] = None
    validation: Optional[Dict[str, str]] = None
    sensitive: bool = False
    original_value: str = ""  # The hardcoded value it replaces


class VariableInferrer:
    """
    Analyzes extracted resources to infer sensible variables
    Replaces hardcoded values with variable references
    """

    # Patterns for detecting different value types
    PATTERNS = {
        'instance_type': {
            'regex': r'"(t[23]\.[a-z0-9]+|m[456]\.[a-z0-9]+|c[456]\.[a-z0-9]+|r[456]\.[a-z0-9]+)"',
            'type': 'string',
            'validation': {
                'condition': 'can(regex("^[a-z][0-9]\\\\.", var.instance_type))',
                'error_message': 'Instance type must be valid AWS instance type (e.g., t3.micro).'
            }
        },
        'cidr_block': {
            'regex': r'"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})"',
            'type': 'string',
            'validation': {
                'condition': 'can(cidrhost(var.cidr_block, 0))',
                'error_message': 'Must be valid IPv4 CIDR block.'
            }
        },
        'port': {
            'regex': r'(?:port|from_port|to_port)\s*=\s*(\d+)',
            'type': 'number',
            'validation': {
                'condition': 'var.{name} >= 0 && var.{name} <= 65535',
                'error_message': 'Port must be between 0 and 65535.'
            }
        },
        'ami_id': {
            'regex': r'"(ami-[a-f0-9]{8,})"',
            'type': 'string',
            'validation': {
                'condition': 'can(regex("^ami-[a-f0-9]+$", var.ami_id))',
                'error_message': 'Must be valid AMI ID (starts with ami-).'
            }
        },
        'availability_zone': {
            'regex': r'"((?:us|eu|ap|sa|ca|me|af)-[a-z]+-\d+[a-z])"',
            'type': 'string',
            'validation': None
        },
        'environment': {
            'regex': r'"(dev|development|staging|stage|prod|production)"',
            'type': 'string',
            'validation': {
                'condition': 'contains(["dev", "staging", "prod"], var.environment)',
                'error_message': 'Environment must be dev, staging, or prod.'
            }
        },
    }

    # Common variable names and their patterns
    COMMON_VARIABLE_NAMES = {
        'name': {
            'patterns': [r'name\s*=\s*"([^"]+)"', r'Name"\s*=\s*"([^"]+)"'],
            'type': 'string',
            'description': 'Name prefix for all resources',
        },
        'environment': {
            'patterns': [r'Environment"\s*=\s*"([^"]+)"', r'environment\s*=\s*"([^"]+)"'],
            'type': 'string',
            'description': 'Environment name (dev, staging, prod)',
        },
        'region': {
            'patterns': [r'region\s*=\s*"([^"]+)"'],
            'type': 'string',
            'description': 'AWS region',
        },
        'tags': {
            'patterns': [r'tags\s*=\s*\{'],
            'type': 'map(string)',
            'description': 'Additional tags to apply to resources',
        },
    }

    def __init__(self):
        self.inferred_variables: Dict[str, InferredVariable] = {}
        self.replacements: List[Tuple[str, str]] = []  # (old_value, new_reference)

    def infer_variables(
        self,
        extraction_result: ExtractionResult,
        include_common: bool = True
    ) -> List[InferredVariable]:
        """
        Analyze extracted resources and infer variables

        Args:
            extraction_result: Resources extracted from Terraform
            include_common: Whether to include common variables (name, environment, tags)

        Returns:
            List of inferred variables
        """

        self.inferred_variables = {}
        self.replacements = []

        # Combine all resources for analysis
        all_resources = (
            extraction_result.primary_resources +
            extraction_result.related_resources
        )

        # Analyze each resource
        for resource in all_resources:
            content = resource.raw_content
            self._analyze_resource_content(content, resource.resource_type or '')

        # Add common variables if requested
        if include_common:
            self._add_common_variables(all_resources)

        # Add variables for referenced vars (from original file)
        for var_name in extraction_result.variables_used:
            if var_name not in self.inferred_variables:
                self.inferred_variables[var_name] = InferredVariable(
                    name=var_name,
                    type='string',  # Default type, could be enhanced
                    description=f'Variable from source: {var_name}',
                    default=None
                )

        return list(self.inferred_variables.values())

    def _analyze_resource_content(self, content: str, resource_type: str):
        """Analyze resource content for hardcoded values"""

        # Check for instance types
        if 'aws_instance' in resource_type or 'launch_template' in resource_type:
            instance_types = re.findall(self.PATTERNS['instance_type']['regex'], content)
            for instance_type in set(instance_types):
                if 'instance_type' not in self.inferred_variables:
                    self.inferred_variables['instance_type'] = InferredVariable(
                        name='instance_type',
                        type='string',
                        description='EC2 instance type',
                        default=instance_type,
                        validation=self.PATTERNS['instance_type']['validation'],
                        original_value=instance_type
                    )

        # Check for CIDR blocks
        if 'vpc' in resource_type or 'subnet' in resource_type:
            cidr_blocks = re.findall(self.PATTERNS['cidr_block']['regex'], content)
            for i, cidr in enumerate(set(cidr_blocks)):
                var_name = 'cidr_block' if i == 0 else f'cidr_block_{i}'
                if var_name not in self.inferred_variables:
                    self.inferred_variables[var_name] = InferredVariable(
                        name=var_name,
                        type='string',
                        description=f'CIDR block for {"VPC" if i == 0 else "subnet"}',
                        default=cidr,
                        validation=self.PATTERNS['cidr_block']['validation'],
                        original_value=cidr
                    )

        # Check for ports
        port_matches = re.findall(r'(from_port|to_port|port)\s*=\s*(\d+)', content)
        port_vars = {}
        for port_type, port_value in port_matches:
            # Create sensible variable names for common ports
            var_name = self._get_port_variable_name(port_value, port_type)
            if var_name not in self.inferred_variables and var_name not in port_vars:
                port_vars[var_name] = port_value
                self.inferred_variables[var_name] = InferredVariable(
                    name=var_name,
                    type='number',
                    description=f'Port number for {self._get_port_description(port_value)}',
                    default=port_value,
                    validation={
                        'condition': f'var.{var_name} >= 0 && var.{var_name} <= 65535',
                        'error_message': 'Port must be between 0 and 65535.'
                    },
                    original_value=port_value
                )

        # Check for AMI IDs
        ami_ids = re.findall(self.PATTERNS['ami_id']['regex'], content)
        if ami_ids and 'ami_id' not in self.inferred_variables:
            # Don't set default for AMI - usually should be from data source
            self.inferred_variables['ami_id'] = InferredVariable(
                name='ami_id',
                type='string',
                description='AMI ID for EC2 instances',
                default=None,  # Usually from data source
                validation=self.PATTERNS['ami_id']['validation'],
                original_value=ami_ids[0]
            )

    def _get_port_variable_name(self, port: str, port_type: str) -> str:
        """Generate sensible variable name for port"""
        port_names = {
            '22': 'ssh_port',
            '80': 'http_port',
            '443': 'https_port',
            '3306': 'mysql_port',
            '5432': 'postgresql_port',
            '6379': 'redis_port',
            '27017': 'mongodb_port',
            '8080': 'app_port',
            '9200': 'elasticsearch_port',
        }

        return port_names.get(port, f'{port_type}_{port}')

    def _get_port_description(self, port: str) -> str:
        """Get description for common ports"""
        descriptions = {
            '22': 'SSH',
            '80': 'HTTP',
            '443': 'HTTPS',
            '3306': 'MySQL',
            '5432': 'PostgreSQL',
            '6379': 'Redis',
            '27017': 'MongoDB',
            '8080': 'application',
            '9200': 'Elasticsearch',
        }
        return descriptions.get(port, 'custom service')

    def _add_common_variables(self, resources: List[ParsedBlock]):
        """Add common variables (name, environment, tags, etc.)"""

        # Check if resources use name tags
        has_names = False
        sample_name = None
        for resource in resources:
            if 'Name' in resource.raw_content or 'name' in resource.raw_content:
                has_names = True
                # Try to extract a sample name
                name_match = re.search(r'Name"\s*=\s*"([^"]+)"', resource.raw_content)
                if name_match:
                    sample_name = name_match.group(1)
                    break

        if has_names and 'name' not in self.inferred_variables:
            # Extract base name from sample
            default_name = None
            if sample_name:
                # Remove common suffixes to get base name
                default_name = re.sub(r'-(dev|staging|prod|test|vpc|ec2|sg|lb).*$', '', sample_name)

            self.inferred_variables['name'] = InferredVariable(
                name='name',
                type='string',
                description='Name prefix for all resources',
                default=default_name,
            )

        # Check for environment tags
        has_environment = False
        sample_env = None
        for resource in resources:
            env_match = re.search(r'Environment"\s*=\s*"([^"]+)"', resource.raw_content)
            if env_match:
                has_environment = True
                sample_env = env_match.group(1)
                break

        if has_environment and 'environment' not in self.inferred_variables:
            self.inferred_variables['environment'] = InferredVariable(
                name='environment',
                type='string',
                description='Environment name (dev, staging, prod)',
                default=sample_env,
                validation={
                    'condition': 'contains(["dev", "staging", "prod"], var.environment)',
                    'error_message': 'Environment must be dev, staging, or prod.'
                }
            )

        # Always add tags as optional
        if 'tags' not in self.inferred_variables:
            self.inferred_variables['tags'] = InferredVariable(
                name='tags',
                type='map(string)',
                description='Additional tags to apply to all resources',
                default='{}',
            )

    def generate_variables_tf(self, variables: List[InferredVariable]) -> str:
        """
        Generate variables.tf content from inferred variables

        Args:
            variables: List of inferred variables

        Returns:
            String content for variables.tf
        """

        lines = []
        lines.append("# Inferred Variables")
        lines.append("# Generated from extracted Terraform resources")
        lines.append("")

        for var in sorted(variables, key=lambda v: v.name):
            lines.append(f'variable "{var.name}" {{')
            lines.append(f'  description = "{var.description}"')
            lines.append(f'  type        = {var.type}')

            if var.default is not None:
                if var.type == 'string':
                    lines.append(f'  default     = "{var.default}"')
                elif var.type == 'number':
                    lines.append(f'  default     = {var.default}')
                elif var.type in ['map(string)', 'list(string)']:
                    lines.append(f'  default     = {var.default}')
                else:
                    lines.append(f'  default     = {var.default}')

            if var.sensitive:
                lines.append('  sensitive   = true')

            if var.validation:
                lines.append('')
                lines.append('  validation {')
                lines.append(f'    condition     = {var.validation["condition"]}')
                lines.append(f'    error_message = "{var.validation["error_message"]}"')
                lines.append('  }')

            lines.append('}')
            lines.append('')

        return '\n'.join(lines)

    def apply_variable_substitutions(
        self,
        content: str,
        variables: List[InferredVariable]
    ) -> str:
        """
        Replace hardcoded values with variable references

        Args:
            content: Original Terraform content
            variables: Variables to use for substitution

        Returns:
            Content with variables substituted
        """

        result = content

        # Build substitution map
        for var in variables:
            if var.original_value:
                # Create variable reference
                if var.type == 'string':
                    old_val = f'"{var.original_value}"'
                    new_val = f'var.{var.name}'
                else:
                    old_val = var.original_value
                    new_val = f'var.{var.name}'

                # Replace all occurrences
                result = result.replace(old_val, new_val)

        return result

    def get_variable_summary(self, variables: List[InferredVariable]) -> Dict[str, any]:
        """Get summary of inferred variables"""

        summary = {
            'total_variables': len(variables),
            'by_type': {},
            'with_defaults': sum(1 for v in variables if v.default is not None),
            'with_validation': sum(1 for v in variables if v.validation is not None),
            'sensitive': sum(1 for v in variables if v.sensitive),
        }

        # Count by type
        for var in variables:
            var_type = var.type
            summary['by_type'][var_type] = summary['by_type'].get(var_type, 0) + 1

        return summary
