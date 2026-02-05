#!/usr/bin/env python3
"""
Terraform Linter - Automated Terraform Best Practices Checker

This script analyzes Terraform files and identifies common issues and anti-patterns.
It is read-only and never modifies files.

Usage:
    python lint_terraform.py [path_to_terraform_dir]

Exit codes:
    0 - No issues found
    1 - Warnings found
    2 - Critical issues found
"""

import os
import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"


@dataclass
class Issue:
    """Represents a linting issue"""
    severity: Severity
    category: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class LintResults:
    """Container for all linting results"""
    issues: List[Issue] = field(default_factory=list)
    files_scanned: int = 0

    def add_issue(self, severity: Severity, category: str, message: str,
                  file_path: str, line_number: Optional[int] = None,
                  suggestion: Optional[str] = None):
        """Add an issue to the results"""
        self.issues.append(Issue(
            severity=severity,
            category=category,
            message=message,
            file_path=file_path,
            line_number=line_number,
            suggestion=suggestion
        ))

    def has_critical(self) -> bool:
        """Check if any critical issues exist"""
        return any(issue.severity == Severity.CRITICAL for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if any warnings exist"""
        return any(issue.severity == Severity.WARNING for issue in self.issues)

    def count_by_severity(self, severity: Severity) -> int:
        """Count issues by severity"""
        return sum(1 for issue in self.issues if issue.severity == severity)


class TerraformLinter:
    """Terraform best practices linter"""

    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.results = LintResults()

    def lint(self) -> LintResults:
        """Run all linting checks"""
        print(f"Scanning Terraform files in: {self.directory}")

        tf_files = list(self.directory.rglob("*.tf"))
        if not tf_files:
            print("No Terraform files found")
            return self.results

        for tf_file in tf_files:
            self._lint_file(tf_file)
            self.results.files_scanned += 1

        return self.results

    def _lint_file(self, file_path: Path):
        """Lint a single Terraform file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Run all checks
            self._check_hardcoded_credentials(content, file_path, lines)
            self._check_hardcoded_amis(content, file_path, lines)
            self._check_unencrypted_resources(content, file_path, lines)
            self._check_missing_tags(content, file_path, lines)
            self._check_variables(content, file_path, lines)
            self._check_security_groups(content, file_path, lines)
            self._check_imdsv2(content, file_path, lines)
            self._check_sensitive_outputs(content, file_path, lines)
            self._check_lifecycle_rules(content, file_path, lines)
            self._check_state_configuration(content, file_path, lines)

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def _check_hardcoded_credentials(self, content: str, file_path: Path, lines: List[str]):
        """Check for hardcoded credentials"""
        patterns = [
            (r'password\s*=\s*"[^$]', 'Hardcoded password detected'),
            (r'secret\s*=\s*"[^$]', 'Hardcoded secret detected'),
            (r'access_key\s*=\s*"[A-Z0-9]{20}"', 'Hardcoded AWS access key detected'),
            (r'secret_key\s*=\s*"[A-Za-z0-9/+=]{40}"', 'Hardcoded AWS secret key detected'),
        ]

        for pattern, message in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    self.results.add_issue(
                        severity=Severity.CRITICAL,
                        category="Security",
                        message=message,
                        file_path=str(file_path),
                        line_number=i,
                        suggestion="Use AWS Secrets Manager or environment variables"
                    )

    def _check_hardcoded_amis(self, content: str, file_path: Path, lines: List[str]):
        """Check for hardcoded AMI IDs"""
        pattern = r'(ami|source_ami)\s*=\s*"ami-[a-f0-9]+"'

        for i, line in enumerate(lines, 1):
            if re.search(pattern, line) and not line.strip().startswith('#'):
                self.results.add_issue(
                    severity=Severity.WARNING,
                    category="Maintainability",
                    message="Hardcoded AMI ID detected",
                    file_path=str(file_path),
                    line_number=i,
                    suggestion="Use data source with filters to lookup latest AMI"
                )

    def _check_unencrypted_resources(self, content: str, file_path: Path, lines: List[str]):
        """Check for unencrypted resources"""
        # Check RDS encryption
        if 'aws_db_instance' in content:
            if 'storage_encrypted' not in content:
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="RDS instance may not be encrypted",
                    file_path=str(file_path),
                    suggestion="Add 'storage_encrypted = true' to aws_db_instance"
                )

        # Check EBS encryption
        if 'aws_ebs_volume' in content or 'root_block_device' in content:
            if not re.search(r'encrypted\s*=\s*true', content):
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="EBS volume may not be encrypted",
                    file_path=str(file_path),
                    suggestion="Add 'encrypted = true' to EBS volumes"
                )

        # Check S3 encryption
        if 'aws_s3_bucket"' in content:
            if 'aws_s3_bucket_server_side_encryption_configuration' not in content:
                self.results.add_issue(
                    severity=Severity.WARNING,
                    category="Security",
                    message="S3 bucket may not have encryption configured",
                    file_path=str(file_path),
                    suggestion="Add aws_s3_bucket_server_side_encryption_configuration resource"
                )

    def _check_missing_tags(self, content: str, file_path: Path, lines: List[str]):
        """Check for resources without tags"""
        resource_pattern = r'resource\s+"(aws_[a-z_]+)"\s+"([a-z_]+)"'

        # Resources that should have tags
        taggable_resources = [
            'aws_instance', 'aws_ebs_volume', 'aws_vpc', 'aws_subnet',
            'aws_security_group', 'aws_db_instance', 'aws_s3_bucket'
        ]

        resources = re.finditer(resource_pattern, content)
        for match in resources:
            resource_type = match.group(1)
            resource_name = match.group(2)

            if resource_type in taggable_resources:
                # Find the resource block
                start_pos = match.end()
                block_content = self._extract_block(content[start_pos:])

                if 'tags' not in block_content and 'default_tags' not in content:
                    self.results.add_issue(
                        severity=Severity.WARNING,
                        category="Tagging",
                        message=f"Resource {resource_type}.{resource_name} has no tags",
                        file_path=str(file_path),
                        suggestion="Add tags block with Name, Environment, Project, ManagedBy"
                    )

    def _check_variables(self, content: str, file_path: Path, lines: List[str]):
        """Check variable definitions"""
        variable_pattern = r'variable\s+"([a-z_]+)"\s+\{'

        variables = re.finditer(variable_pattern, content)
        for match in variables:
            var_name = match.group(1)
            start_pos = match.end()
            block_content = self._extract_block(content[start_pos:])

            # Check for description
            if 'description' not in block_content:
                self.results.add_issue(
                    severity=Severity.SUGGESTION,
                    category="Documentation",
                    message=f"Variable '{var_name}' has no description",
                    file_path=str(file_path),
                    suggestion="Add description field to variable"
                )

            # Check for validation on environment-like variables
            if 'environment' in var_name.lower() and 'validation' not in block_content:
                self.results.add_issue(
                    severity=Severity.WARNING,
                    category="Validation",
                    message=f"Variable '{var_name}' should have validation",
                    file_path=str(file_path),
                    suggestion="Add validation block to ensure valid environment values"
                )

    def _check_security_groups(self, content: str, file_path: Path, lines: List[str]):
        """Check security group configurations"""
        # Check for overly permissive ingress rules
        ingress_pattern = r'cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]'

        for i, line in enumerate(lines, 1):
            if re.search(ingress_pattern, line):
                # Check if it's for SSH (port 22)
                context_start = max(0, i - 10)
                context_lines = lines[context_start:i+5]
                context = '\n'.join(context_lines)

                if 'from_port   = 22' in context or 'from_port = 22' in context:
                    self.results.add_issue(
                        severity=Severity.CRITICAL,
                        category="Security",
                        message="SSH (port 22) open to 0.0.0.0/0",
                        file_path=str(file_path),
                        line_number=i,
                        suggestion="Restrict SSH to specific CIDR blocks or use AWS Systems Manager"
                    )

        # Check for missing security group descriptions
        if 'aws_security_group_rule' in content or 'ingress' in content:
            if 'description' not in content:
                self.results.add_issue(
                    severity=Severity.SUGGESTION,
                    category="Documentation",
                    message="Security group rules should have descriptions",
                    file_path=str(file_path),
                    suggestion="Add description field to all security group rules"
                )

    def _check_imdsv2(self, content: str, file_path: Path, lines: List[str]):
        """Check for IMDSv2 enforcement"""
        if 'aws_instance' in content or 'aws_launch_template' in content:
            if 'metadata_options' not in content:
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="EC2 instances should enforce IMDSv2",
                    file_path=str(file_path),
                    suggestion="Add metadata_options block with http_tokens = 'required'"
                )
            elif 'http_tokens' in content:
                if not re.search(r'http_tokens\s*=\s*"required"', content):
                    self.results.add_issue(
                        severity=Severity.CRITICAL,
                        category="Security",
                        message="IMDSv2 not enforced (http_tokens should be 'required')",
                        file_path=str(file_path),
                        suggestion="Set http_tokens = 'required' in metadata_options"
                    )

    def _check_sensitive_outputs(self, content: str, file_path: Path, lines: List[str]):
        """Check for potentially sensitive outputs"""
        output_pattern = r'output\s+"([a-z_]+)"\s+\{'
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']

        outputs = re.finditer(output_pattern, content)
        for match in outputs:
            output_name = match.group(1)
            start_pos = match.end()
            block_content = self._extract_block(content[start_pos:])

            # Check if output name suggests sensitive data
            if any(keyword in output_name.lower() for keyword in sensitive_keywords):
                if 'sensitive' not in block_content:
                    self.results.add_issue(
                        severity=Severity.CRITICAL,
                        category="Security",
                        message=f"Output '{output_name}' may contain sensitive data",
                        file_path=str(file_path),
                        suggestion="Add 'sensitive = true' to output"
                    )

    def _check_lifecycle_rules(self, content: str, file_path: Path, lines: List[str]):
        """Check for missing lifecycle rules on critical resources"""
        # Security groups should have create_before_destroy
        if 'aws_security_group"' in content:
            sg_blocks = re.finditer(r'resource\s+"aws_security_group"\s+"[a-z_]+"\s+\{', content)
            for match in sg_blocks:
                start_pos = match.end()
                block_content = self._extract_block(content[start_pos:])

                if 'create_before_destroy' not in block_content:
                    self.results.add_issue(
                        severity=Severity.WARNING,
                        category="Reliability",
                        message="Security group should have create_before_destroy lifecycle rule",
                        file_path=str(file_path),
                        suggestion="Add lifecycle { create_before_destroy = true }"
                    )

    def _check_state_configuration(self, content: str, file_path: Path, lines: List[str]):
        """Check Terraform state configuration"""
        if 'terraform' in content and 'backend' in content:
            # Check for encryption
            if 'backend "s3"' in content:
                if 'encrypt' not in content:
                    self.results.add_issue(
                        severity=Severity.CRITICAL,
                        category="Security",
                        message="S3 backend should have encryption enabled",
                        file_path=str(file_path),
                        suggestion="Add 'encrypt = true' to backend configuration"
                    )

                # Check for state locking
                if 'dynamodb_table' not in content:
                    self.results.add_issue(
                        severity=Severity.WARNING,
                        category="Reliability",
                        message="S3 backend should have DynamoDB table for state locking",
                        file_path=str(file_path),
                        suggestion="Add 'dynamodb_table' to backend configuration"
                    )

    def _extract_block(self, content: str) -> str:
        """Extract a HCL block (content between { and matching })"""
        depth = 0
        block = []

        for char in content:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    break

            if depth > 0:
                block.append(char)

        return ''.join(block)


def print_results(results: LintResults):
    """Print linting results in a human-readable format"""
    print("\n" + "=" * 80)
    print("TERRAFORM LINTING RESULTS")
    print("=" * 80)
    print(f"\nFiles scanned: {results.files_scanned}")
    print(f"Total issues: {len(results.issues)}")
    print(f"  CRITICAL: {results.count_by_severity(Severity.CRITICAL)}")
    print(f"  WARNING:  {results.count_by_severity(Severity.WARNING)}")
    print(f"  SUGGESTION: {results.count_by_severity(Severity.SUGGESTION)}")

    if not results.issues:
        print("\n✓ No issues found! Great job!")
        return

    # Group issues by severity
    for severity in [Severity.CRITICAL, Severity.WARNING, Severity.SUGGESTION]:
        severity_issues = [i for i in results.issues if i.severity == severity]
        if not severity_issues:
            continue

        print(f"\n{severity.value} ISSUES ({len(severity_issues)}):")
        print("-" * 80)

        for issue in severity_issues:
            print(f"\n[{issue.category}] {issue.message}")
            print(f"  File: {issue.file_path}")
            if issue.line_number:
                print(f"  Line: {issue.line_number}")
            if issue.suggestion:
                print(f"  Fix: {issue.suggestion}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    linter = TerraformLinter(directory)
    results = linter.lint()

    print_results(results)

    # Exit with appropriate code
    if results.has_critical():
        sys.exit(2)
    elif results.has_warnings():
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
