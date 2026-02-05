#!/usr/bin/env python3
"""
Output Generator
Detects common outputs by resource type and generates outputs.tf
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass

from .hcl_parser import ParsedBlock
from .resource_extractor import ExtractionResult


@dataclass
class InferredOutput:
    """Represents an inferred output"""
    name: str
    description: str
    value: str
    sensitive: bool = False


class OutputGenerator:
    """
    Analyzes extracted resources to generate useful outputs
    """

    # Common output patterns by resource type
    OUTPUT_PATTERNS = {
        'aws_instance': [
            {'name': 'instance_id', 'attr': 'id', 'description': 'EC2 instance ID'},
            {'name': 'public_ip', 'attr': 'public_ip', 'description': 'Public IP address'},
            {'name': 'private_ip', 'attr': 'private_ip', 'description': 'Private IP address'},
            {'name': 'public_dns', 'attr': 'public_dns', 'description': 'Public DNS name'},
            {'name': 'arn', 'attr': 'arn', 'description': 'Instance ARN'},
        ],
        'aws_vpc': [
            {'name': 'vpc_id', 'attr': 'id', 'description': 'VPC ID'},
            {'name': 'vpc_arn', 'attr': 'arn', 'description': 'VPC ARN'},
            {'name': 'vpc_cidr_block', 'attr': 'cidr_block', 'description': 'VPC CIDR block'},
            {'name': 'default_security_group_id', 'attr': 'default_security_group_id', 'description': 'Default security group ID'},
        ],
        'aws_subnet': [
            {'name': 'subnet_ids', 'attr': 'id', 'description': 'Subnet IDs', 'list': True},
            {'name': 'subnet_arns', 'attr': 'arn', 'description': 'Subnet ARNs', 'list': True},
            {'name': 'subnet_cidr_blocks', 'attr': 'cidr_block', 'description': 'Subnet CIDR blocks', 'list': True},
        ],
        'aws_security_group': [
            {'name': 'security_group_id', 'attr': 'id', 'description': 'Security group ID'},
            {'name': 'security_group_arn', 'attr': 'arn', 'description': 'Security group ARN'},
            {'name': 'security_group_name', 'attr': 'name', 'description': 'Security group name'},
        ],
        'aws_s3_bucket': [
            {'name': 'bucket_id', 'attr': 'id', 'description': 'S3 bucket name'},
            {'name': 'bucket_arn', 'attr': 'arn', 'description': 'S3 bucket ARN'},
            {'name': 'bucket_domain_name', 'attr': 'bucket_domain_name', 'description': 'S3 bucket domain name'},
            {'name': 'bucket_regional_domain_name', 'attr': 'bucket_regional_domain_name', 'description': 'S3 bucket region-specific domain name'},
        ],
        'aws_db_instance': [
            {'name': 'db_instance_id', 'attr': 'id', 'description': 'RDS instance ID'},
            {'name': 'db_instance_arn', 'attr': 'arn', 'description': 'RDS instance ARN'},
            {'name': 'db_instance_endpoint', 'attr': 'endpoint', 'description': 'RDS instance endpoint'},
            {'name': 'db_instance_address', 'attr': 'address', 'description': 'RDS instance address'},
            {'name': 'db_instance_port', 'attr': 'port', 'description': 'RDS instance port'},
        ],
        'aws_lb': [
            {'name': 'lb_id', 'attr': 'id', 'description': 'Load balancer ID'},
            {'name': 'lb_arn', 'attr': 'arn', 'description': 'Load balancer ARN'},
            {'name': 'lb_dns_name', 'attr': 'dns_name', 'description': 'Load balancer DNS name'},
            {'name': 'lb_zone_id', 'attr': 'zone_id', 'description': 'Load balancer zone ID'},
        ],
        'aws_iam_role': [
            {'name': 'role_id', 'attr': 'id', 'description': 'IAM role ID'},
            {'name': 'role_arn', 'attr': 'arn', 'description': 'IAM role ARN'},
            {'name': 'role_name', 'attr': 'name', 'description': 'IAM role name'},
        ],
        'aws_eks_cluster': [
            {'name': 'cluster_id', 'attr': 'id', 'description': 'EKS cluster ID'},
            {'name': 'cluster_arn', 'attr': 'arn', 'description': 'EKS cluster ARN'},
            {'name': 'cluster_endpoint', 'attr': 'endpoint', 'description': 'EKS cluster endpoint'},
            {'name': 'cluster_certificate_authority', 'attr': 'certificate_authority[0].data', 'description': 'EKS cluster certificate authority'},
        ],
        'aws_lambda_function': [
            {'name': 'function_name', 'attr': 'function_name', 'description': 'Lambda function name'},
            {'name': 'function_arn', 'attr': 'arn', 'description': 'Lambda function ARN'},
            {'name': 'function_invoke_arn', 'attr': 'invoke_arn', 'description': 'Lambda function invoke ARN'},
            {'name': 'function_version', 'attr': 'version', 'description': 'Lambda function version'},
        ],
        'aws_eip': [
            {'name': 'eip_id', 'attr': 'id', 'description': 'Elastic IP ID'},
            {'name': 'eip_public_ip', 'attr': 'public_ip', 'description': 'Elastic IP address'},
        ],
        'aws_nat_gateway': [
            {'name': 'nat_gateway_id', 'attr': 'id', 'description': 'NAT Gateway ID'},
            {'name': 'nat_gateway_public_ip', 'attr': 'public_ip', 'description': 'NAT Gateway public IP'},
        ],
        'aws_internet_gateway': [
            {'name': 'igw_id', 'attr': 'id', 'description': 'Internet Gateway ID'},
        ],
        'aws_route_table': [
            {'name': 'route_table_ids', 'attr': 'id', 'description': 'Route table IDs', 'list': True},
        ],
        'aws_key_pair': [
            {'name': 'key_pair_id', 'attr': 'id', 'description': 'Key pair ID'},
            {'name': 'key_pair_name', 'attr': 'key_name', 'description': 'Key pair name'},
            {'name': 'key_pair_fingerprint', 'attr': 'fingerprint', 'description': 'Key pair fingerprint'},
        ],
    }

    def __init__(self):
        self.inferred_outputs: Dict[str, InferredOutput] = {}

    def infer_outputs(self, extraction_result: ExtractionResult) -> List[InferredOutput]:
        """
        Analyze extracted resources and generate useful outputs

        Args:
            extraction_result: Resources extracted from Terraform

        Returns:
            List of inferred outputs
        """

        self.inferred_outputs = {}

        # Analyze primary resources (main focus)
        for resource in extraction_result.primary_resources:
            self._generate_outputs_for_resource(resource)

        # Also add key outputs from related resources
        for resource in extraction_result.related_resources:
            # Only generate for specific important related resources
            if resource.resource_type in ['aws_security_group', 'aws_subnet', 'aws_route_table']:
                self._generate_outputs_for_resource(resource)

        return list(self.inferred_outputs.values())

    def _generate_outputs_for_resource(self, resource: ParsedBlock):
        """Generate outputs for a single resource"""

        resource_type = resource.resource_type
        resource_name = resource.name

        # Get output patterns for this resource type
        patterns = self.OUTPUT_PATTERNS.get(resource_type, [])

        if not patterns:
            # Default pattern - just output ID
            patterns = [{'name': 'id', 'attr': 'id', 'description': f'{resource_type} ID'}]

        for pattern in patterns:
            # Generate unique output name
            if pattern.get('list', False):
                # For list outputs, use plural form
                output_name = pattern['name']
            else:
                # Include resource name to make it unique
                if resource_name and resource_name != 'main':
                    output_name = f"{resource_name}_{pattern['name']}"
                else:
                    output_name = pattern['name']

            # Skip if already added
            if output_name in self.inferred_outputs:
                continue

            # Build output value
            attr = pattern['attr']
            if pattern.get('list', False):
                # List output (e.g., all subnet IDs)
                value = f'{resource_type}.{resource_name}[*].{attr}'
            else:
                # Single value output
                value = f'{resource_type}.{resource_name}.{attr}'

            # Check if should be sensitive
            sensitive = 'key' in pattern['name'].lower() or 'password' in pattern['name'].lower()

            # Create output
            output = InferredOutput(
                name=output_name,
                description=pattern['description'],
                value=value,
                sensitive=sensitive
            )

            self.inferred_outputs[output_name] = output

    def generate_outputs_tf(self, outputs: List[InferredOutput]) -> str:
        """
        Generate outputs.tf content from inferred outputs

        Args:
            outputs: List of inferred outputs

        Returns:
            String content for outputs.tf
        """

        lines = []
        lines.append("# Inferred Outputs")
        lines.append("# Generated from extracted Terraform resources")
        lines.append("")

        for output in sorted(outputs, key=lambda o: o.name):
            lines.append(f'output "{output.name}" {{')
            lines.append(f'  description = "{output.description}"')
            lines.append(f'  value       = {output.value}')

            if output.sensitive:
                lines.append('  sensitive   = true')

            lines.append('}')
            lines.append('')

        return '\n'.join(lines)

    def get_output_summary(self, outputs: List[InferredOutput]) -> Dict[str, any]:
        """Get summary of inferred outputs"""

        summary = {
            'total_outputs': len(outputs),
            'sensitive_outputs': sum(1 for o in outputs if o.sensitive),
            'output_names': [o.name for o in outputs],
        }

        return summary
