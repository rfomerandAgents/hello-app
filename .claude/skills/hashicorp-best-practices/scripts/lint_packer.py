#!/usr/bin/env python3
"""
Packer Linter - Automated Packer Best Practices Checker

This script analyzes Packer HCL2 files and identifies common issues and anti-patterns.
It is read-only and never modifies files.

Usage:
    python lint_packer.py [path_to_packer_dir]

Exit codes:
    0 - No issues found
    1 - Warnings found
    2 - Critical issues found
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
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


class PackerLinter:
    """Packer best practices linter"""

    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.results = LintResults()

    def lint(self) -> LintResults:
        """Run all linting checks"""
        print(f"Scanning Packer files in: {self.directory}")

        packer_files = list(self.directory.rglob("*.pkr.hcl"))
        if not packer_files:
            print("No Packer files found")
            return self.results

        for packer_file in packer_files:
            self._lint_file(packer_file)
            self.results.files_scanned += 1

        return self.results

    def _lint_file(self, file_path: Path):
        """Lint a single Packer file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Run all checks
            self._check_hardcoded_ami(content, file_path, lines)
            self._check_imdsv2(content, file_path, lines)
            self._check_encryption(content, file_path, lines)
            self._check_security_group(content, file_path, lines)
            self._check_provisioners(content, file_path, lines)
            self._check_manifest_postprocessor(content, file_path, lines)
            self._check_variables(content, file_path, lines)
            self._check_cleanup(content, file_path, lines)
            self._check_secrets(content, file_path, lines)
            self._check_performance(content, file_path, lines)

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def _check_hardcoded_ami(self, content: str, file_path: Path, lines: List[str]):
        """Check for hardcoded AMI IDs"""
        pattern = r'source_ami\s*=\s*"ami-[a-f0-9]+"'

        for i, line in enumerate(lines, 1):
            if re.search(pattern, line) and not line.strip().startswith('#'):
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Maintainability",
                    message="Hardcoded source AMI ID detected",
                    file_path=str(file_path),
                    line_number=i,
                    suggestion="Use source_ami_filter with most_recent = true to dynamically select AMI"
                )

    def _check_imdsv2(self, content: str, file_path: Path, lines: List[str]):
        """Check for IMDSv2 enforcement"""
        if 'source "amazon-ebs"' in content or 'source "amazon-instance"' in content:
            if 'metadata_options' not in content:
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="IMDSv2 not configured in source block",
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

    def _check_encryption(self, content: str, file_path: Path, lines: List[str]):
        """Check for AMI encryption"""
        if 'source "amazon-ebs"' in content:
            if 'encrypt_boot' not in content:
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="AMI encryption not enabled",
                    file_path=str(file_path),
                    suggestion="Add 'encrypt_boot = true' to source block"
                )
            elif not re.search(r'encrypt_boot\s*=\s*true', content):
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="AMI encryption is disabled",
                    file_path=str(file_path),
                    suggestion="Set 'encrypt_boot = true'"
                )

            # Check for KMS key usage
            if 'encrypt_boot = true' in content and 'kms_key_id' not in content:
                self.results.add_issue(
                    severity=Severity.WARNING,
                    category="Security",
                    message="AMI encryption uses default key instead of custom KMS key",
                    file_path=str(file_path),
                    suggestion="Specify kms_key_id for better key management"
                )

    def _check_security_group(self, content: str, file_path: Path, lines: List[str]):
        """Check temporary security group configuration"""
        pattern = r'temporary_security_group_source_cidrs\s*=\s*\["0\.0\.0\.0/0"\]'

        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                self.results.add_issue(
                    severity=Severity.CRITICAL,
                    category="Security",
                    message="Temporary security group allows access from 0.0.0.0/0",
                    file_path=str(file_path),
                    line_number=i,
                    suggestion="Restrict to specific CIDR blocks or use security_group_ids"
                )

    def _check_provisioners(self, content: str, file_path: Path, lines: List[str]):
        """Check provisioner patterns"""
        # Count provisioner blocks
        provisioner_count = len(re.findall(r'provisioner\s+"shell"', content))

        if provisioner_count > 10:
            self.results.add_issue(
                severity=Severity.WARNING,
                category="Performance",
                message=f"Too many shell provisioners ({provisioner_count})",
                file_path=str(file_path),
                suggestion="Consolidate shell provisioners to reduce SSH sessions"
            )

        # Check for very long inline scripts
        inline_pattern = r'inline\s*=\s*\['
        matches = re.finditer(inline_pattern, content)

        for match in matches:
            start_pos = match.end()
            # Count lines in inline array
            bracket_depth = 1
            lines_count = 0

            for char in content[start_pos:]:
                if char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1
                    if bracket_depth == 0:
                        break
                elif char == '\n':
                    lines_count += 1

            if lines_count > 20:
                self.results.add_issue(
                    severity=Severity.SUGGESTION,
                    category="Maintainability",
                    message=f"Long inline script ({lines_count} lines) detected",
                    file_path=str(file_path),
                    suggestion="Move inline script to a separate file and use 'script' instead"
                )

        # Check for provisioners without timeout
        if 'provisioner' in content and 'timeout' not in content:
            self.results.add_issue(
                severity=Severity.SUGGESTION,
                category="Reliability",
                message="Provisioners should have explicit timeouts",
                file_path=str(file_path),
                suggestion="Add timeout field to provisioners (e.g., timeout = '10m')"
            )

    def _check_manifest_postprocessor(self, content: str, file_path: Path, lines: List[str]):
        """Check for manifest post-processor"""
        if 'build' in content and 'post-processor "manifest"' not in content:
            self.results.add_issue(
                severity=Severity.WARNING,
                category="Best Practices",
                message="Missing manifest post-processor",
                file_path=str(file_path),
                suggestion="Add post-processor 'manifest' to track AMI metadata"
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

    def _check_cleanup(self, content: str, file_path: Path, lines: List[str]):
        """Check for cleanup provisioners"""
        if 'provisioner' in content:
            # Look for cleanup-related keywords in provisioners
            cleanup_keywords = ['cleanup', 'rm -rf', 'truncate', 'apt-get clean']

            has_cleanup = any(keyword in content for keyword in cleanup_keywords)

            if not has_cleanup:
                self.results.add_issue(
                    severity=Severity.WARNING,
                    category="Best Practices",
                    message="No cleanup provisioner detected",
                    file_path=str(file_path),
                    suggestion="Add cleanup provisioner to remove logs, caches, and temporary files"
                )

    def _check_secrets(self, content: str, file_path: Path, lines: List[str]):
        """Check for secrets in provisioners"""
        patterns = [
            (r'password\s*=', 'Potential password in provisioner'),
            (r'API_KEY\s*=', 'Potential API key in provisioner'),
            (r'SECRET\s*=', 'Potential secret in provisioner'),
        ]

        for pattern, message in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's in a provisioner block
                    context_start = max(0, i - 20)
                    context = '\n'.join(lines[context_start:i])

                    if 'provisioner' in context:
                        self.results.add_issue(
                            severity=Severity.CRITICAL,
                            category="Security",
                            message=message,
                            file_path=str(file_path),
                            line_number=i,
                            suggestion="Don't bake secrets into AMI. Use AWS Secrets Manager."
                        )

    def _check_performance(self, content: str, file_path: Path, lines: List[str]):
        """Check for performance optimizations"""
        # Check for EBS optimization
        if 'source "amazon-ebs"' in content:
            if 'ebs_optimized' not in content:
                self.results.add_issue(
                    severity=Severity.SUGGESTION,
                    category="Performance",
                    message="EBS optimization not enabled",
                    file_path=str(file_path),
                    suggestion="Add 'ebs_optimized = true' for better I/O performance"
                )

            # Check for enhanced networking
            if 'ena_support' not in content:
                self.results.add_issue(
                    severity=Severity.SUGGESTION,
                    category="Performance",
                    message="Enhanced networking (ENA) not enabled",
                    file_path=str(file_path),
                    suggestion="Add 'ena_support = true' for better network performance"
                )

        # Check instance type for builds
        if 'instance_type' in content:
            # Look for t2/t3 instances used for builds
            if re.search(r'instance_type\s*=\s*"t[23]\.', content):
                self.results.add_issue(
                    severity=Severity.SUGGESTION,
                    category="Performance",
                    message="Consider using compute-optimized instance for faster builds",
                    file_path=str(file_path),
                    suggestion="Use c5/c6i instances for build performance (e.g., c6i.large)"
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
    print("PACKER LINTING RESULTS")
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

    linter = PackerLinter(directory)
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
