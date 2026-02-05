#!/usr/bin/env python3
"""
Resource Extractor
Extracts specific resources from Terraform files with dependency awareness.
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

from .hcl_parser import HCLParser, ParsedFile, ParsedBlock


@dataclass
class ExtractionResult:
    """Result of resource extraction"""
    primary_resources: List[ParsedBlock]
    related_resources: List[ParsedBlock]
    data_sources: List[ParsedBlock]
    locals: List[ParsedBlock]
    variables_used: Set[str]  # Variable names referenced
    module_references: Set[str]  # Module references


class ResourceExtractor:
    """
    Extracts resources from Terraform files based on type/category
    Automatically includes dependencies and related resources
    """

    # Resource type groupings for intelligent extraction
    RESOURCE_GROUPS = {
        'vpc': [
            'aws_vpc',
            'aws_subnet',
            'aws_internet_gateway',
            'aws_nat_gateway',
            'aws_eip',  # For NAT
            'aws_route_table',
            'aws_route_table_association',
            'aws_route',
            'aws_network_acl',
            'aws_network_acl_rule',
            'aws_vpc_endpoint',
            'aws_vpc_peering_connection',
            'aws_vpn_gateway',
            'aws_customer_gateway',
            'aws_vpn_connection',
        ],
        'ec2': [
            'aws_instance',
            'aws_launch_template',
            'aws_launch_configuration',
            'aws_autoscaling_group',
            'aws_autoscaling_policy',
            'aws_placement_group',
            'aws_key_pair',
            'aws_eip',  # Elastic IPs for instances
            'aws_eip_association',
            'aws_network_interface',
            'aws_security_group',
            'aws_security_group_rule',
        ],
        's3': [
            'aws_s3_bucket',
            'aws_s3_bucket_policy',
            'aws_s3_bucket_public_access_block',
            'aws_s3_bucket_versioning',
            'aws_s3_bucket_lifecycle_configuration',
            'aws_s3_bucket_server_side_encryption_configuration',
            'aws_s3_bucket_logging',
            'aws_s3_bucket_cors_configuration',
            'aws_s3_bucket_website_configuration',
            'aws_s3_object',
        ],
        'rds': [
            'aws_db_instance',
            'aws_db_subnet_group',
            'aws_db_parameter_group',
            'aws_db_option_group',
            'aws_rds_cluster',
            'aws_rds_cluster_instance',
            'aws_db_proxy',
            'aws_db_snapshot',
        ],
        'iam': [
            'aws_iam_role',
            'aws_iam_role_policy',
            'aws_iam_role_policy_attachment',
            'aws_iam_policy',
            'aws_iam_user',
            'aws_iam_group',
            'aws_iam_group_membership',
            'aws_iam_instance_profile',
            'aws_iam_access_key',
        ],
        'eks': [
            'aws_eks_cluster',
            'aws_eks_node_group',
            'aws_eks_fargate_profile',
            'aws_eks_addon',
            'aws_iam_role',  # Often needed for EKS
            'aws_iam_role_policy_attachment',
        ],
        'lambda': [
            'aws_lambda_function',
            'aws_lambda_permission',
            'aws_lambda_alias',
            'aws_lambda_event_source_mapping',
            'aws_lambda_layer_version',
            'aws_iam_role',  # For Lambda execution
            'aws_iam_role_policy_attachment',
        ],
        'api-gateway': [
            'aws_api_gateway_rest_api',
            'aws_api_gateway_resource',
            'aws_api_gateway_method',
            'aws_api_gateway_integration',
            'aws_api_gateway_deployment',
            'aws_api_gateway_stage',
            'aws_apigatewayv2_api',
            'aws_apigatewayv2_stage',
            'aws_apigatewayv2_integration',
            'aws_apigatewayv2_route',
        ],
        'security': [
            'aws_security_group',
            'aws_security_group_rule',
            'aws_network_acl',
            'aws_network_acl_rule',
            'aws_key_pair',
        ],
    }

    def __init__(self, parser: Optional[HCLParser] = None):
        self.parser = parser or HCLParser()

    def extract_by_type(
        self,
        parsed_file: ParsedFile,
        resource_category: str,
        include_dependencies: bool = True
    ) -> ExtractionResult:
        """
        Extract resources by category (vpc, ec2, s3, etc.)

        Args:
            parsed_file: Parsed Terraform file
            resource_category: Category to extract (vpc, ec2, s3, etc.)
            include_dependencies: Whether to include dependent resources

        Returns:
            ExtractionResult with primary resources and dependencies
        """

        # Get resource types for this category
        resource_types = self.RESOURCE_GROUPS.get(resource_category, [])

        if not resource_types:
            # If not a known category, treat as custom
            resource_types = [resource_category]

        # Find primary resources matching the types
        primary_resources = []
        for resource in parsed_file.resources:
            if resource.resource_type in resource_types:
                primary_resources.append(resource)

        if not primary_resources:
            return ExtractionResult(
                primary_resources=[],
                related_resources=[],
                data_sources=[],
                locals=[],
                variables_used=set(),
                module_references=set()
            )

        # Build dependency graph
        if include_dependencies:
            related_resources, data_sources, locals_used = self._extract_dependencies(
                parsed_file, primary_resources
            )
        else:
            related_resources = []
            data_sources = []
            locals_used = []

        # Find all variable references
        variables_used = self._extract_variable_references(
            primary_resources + related_resources
        )

        # Find module references
        module_references = self._extract_module_references(
            primary_resources + related_resources
        )

        return ExtractionResult(
            primary_resources=primary_resources,
            related_resources=related_resources,
            data_sources=data_sources,
            locals=locals_used,
            variables_used=variables_used,
            module_references=module_references
        )

    def extract_by_resource_name(
        self,
        parsed_file: ParsedFile,
        resource_names: List[str],
        include_dependencies: bool = True
    ) -> ExtractionResult:
        """
        Extract specific resources by their full names

        Args:
            parsed_file: Parsed Terraform file
            resource_names: List of resource names (e.g., ["aws_instance.web"])
            include_dependencies: Whether to include dependent resources
        """

        # Find resources by name
        primary_resources = []
        for name in resource_names:
            resource = parsed_file.get_resource_by_name(name)
            if resource:
                primary_resources.append(resource)

        if not primary_resources:
            return ExtractionResult(
                primary_resources=[],
                related_resources=[],
                data_sources=[],
                locals=[],
                variables_used=set(),
                module_references=set()
            )

        # Extract dependencies
        if include_dependencies:
            related_resources, data_sources, locals_used = self._extract_dependencies(
                parsed_file, primary_resources
            )
        else:
            related_resources = []
            data_sources = []
            locals_used = []

        variables_used = self._extract_variable_references(
            primary_resources + related_resources
        )

        module_references = self._extract_module_references(
            primary_resources + related_resources
        )

        return ExtractionResult(
            primary_resources=primary_resources,
            related_resources=related_resources,
            data_sources=data_sources,
            locals=locals_used,
            variables_used=variables_used,
            module_references=module_references
        )

    def _extract_dependencies(
        self,
        parsed_file: ParsedFile,
        primary_resources: List[ParsedBlock]
    ) -> tuple[List[ParsedBlock], List[ParsedBlock], List[ParsedBlock]]:
        """
        Extract all dependencies (resources, data sources, locals)

        Returns:
            Tuple of (related_resources, data_sources, locals)
        """

        # Track what we've already included
        included_resource_names = {r.full_name for r in primary_resources}
        included_data_names = set()
        included_local_names = set()

        # Resources to process
        to_process = list(primary_resources)
        related_resources = []
        data_sources = []
        locals_blocks = []

        # BFS through dependencies
        while to_process:
            current = to_process.pop(0)

            for dep in current.dependencies:
                # Resource dependency
                if '.' in dep and not dep.startswith(('var.', 'data.', 'local.', 'module.')):
                    if dep not in included_resource_names:
                        dep_resource = parsed_file.get_resource_by_name(dep)
                        if dep_resource:
                            included_resource_names.add(dep)
                            related_resources.append(dep_resource)
                            to_process.append(dep_resource)  # Process its dependencies too

                # Data source dependency
                elif dep.startswith('data.'):
                    data_name = dep[5:]  # Remove 'data.' prefix
                    if data_name not in included_data_names:
                        data_source = parsed_file.get_data_source_by_name(data_name)
                        if data_source:
                            included_data_names.add(data_name)
                            data_sources.append(data_source)

                # Local dependency
                elif dep.startswith('local.'):
                    local_name = dep[6:]  # Remove 'local.' prefix
                    if local_name not in included_local_names:
                        # Find local block
                        for local_block in parsed_file.locals:
                            if local_block.name == local_name:
                                included_local_names.add(local_name)
                                locals_blocks.append(local_block)
                                break

        return related_resources, data_sources, locals_blocks

    def _extract_variable_references(self, resources: List[ParsedBlock]) -> Set[str]:
        """Extract all variable references from resources"""
        variables = set()

        for resource in resources:
            for dep in resource.dependencies:
                if dep.startswith('var.'):
                    var_name = dep[4:]  # Remove 'var.' prefix
                    variables.add(var_name)

        return variables

    def _extract_module_references(self, resources: List[ParsedBlock]) -> Set[str]:
        """Extract all module references from resources"""
        modules = set()

        for resource in resources:
            for dep in resource.dependencies:
                if dep.startswith('module.'):
                    module_name = dep[7:]  # Remove 'module.' prefix
                    # Extract just the module name (before any attribute access)
                    if '.' in module_name:
                        module_name = module_name.split('.')[0]
                    modules.add(module_name)

        return modules

    def generate_main_tf(self, extraction_result: ExtractionResult) -> str:
        """
        Generate main.tf content from extracted resources

        Args:
            extraction_result: Result from extract_by_type or extract_by_resource_name

        Returns:
            String content for main.tf file
        """

        lines = []

        # Add comment header
        lines.append("# Extracted Terraform Resources")
        lines.append("# Primary resources and their dependencies")
        lines.append("")

        # Add locals if any
        if extraction_result.locals:
            lines.append("# Local values")
            lines.append("locals {")
            for local_block in extraction_result.locals:
                lines.append(f"  {local_block.raw_content}")
            lines.append("}")
            lines.append("")

        # Add data sources if any
        if extraction_result.data_sources:
            lines.append("# Data sources")
            for ds in extraction_result.data_sources:
                lines.append(ds.raw_content)
                lines.append("")

        # Add primary resources
        if extraction_result.primary_resources:
            lines.append("# Primary resources")
            for resource in extraction_result.primary_resources:
                lines.append(resource.raw_content)
                lines.append("")

        # Add related resources
        if extraction_result.related_resources:
            lines.append("# Related/dependent resources")
            for resource in extraction_result.related_resources:
                lines.append(resource.raw_content)
                lines.append("")

        return '\n'.join(lines)

    def get_extraction_summary(self, extraction_result: ExtractionResult) -> Dict[str, any]:
        """Get a summary of what was extracted"""

        summary = {
            'primary_resources': len(extraction_result.primary_resources),
            'related_resources': len(extraction_result.related_resources),
            'data_sources': len(extraction_result.data_sources),
            'locals': len(extraction_result.locals),
            'variables_referenced': len(extraction_result.variables_used),
            'modules_referenced': len(extraction_result.module_references),
            'resource_details': {
                'primary': [r.full_name for r in extraction_result.primary_resources],
                'related': [r.full_name for r in extraction_result.related_resources],
                'data': [d.full_name for d in extraction_result.data_sources],
            }
        }

        return summary
