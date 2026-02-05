#!/usr/bin/env python3
"""
Packer Build Analyzer

Parses Packer build logs to identify slow provisioners and bottlenecks.
Provides actionable insights for optimizing build times.

Usage:
    python analyze_build.py packer-build.log
    python analyze_build.py packer-build.log --json
    python analyze_build.py packer-build.log --top 10
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


class ProvisionerStats:
    """Statistics for a single provisioner."""
    
    def __init__(self, name: str):
        self.name = name
        self.executions = []
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0
        
    def add_execution(self, duration: float):
        """Add an execution time for this provisioner."""
        self.executions.append(duration)
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
    
    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / len(self.executions) if self.executions else 0.0
    
    @property
    def count(self) -> int:
        """Number of executions."""
        return len(self.executions)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            'name': self.name,
            'count': self.count,
            'total_time': round(self.total_time, 2),
            'avg_time': round(self.avg_time, 2),
            'min_time': round(self.min_time, 2),
            'max_time': round(self.max_time, 2),
        }


class PackerBuildAnalyzer:
    """Analyzes Packer build logs for optimization opportunities."""
    
    # Regex patterns for log parsing
    TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})')
    PROVISIONER_START = re.compile(r'Provisioning with ([\w-]+)')
    PROVISIONER_END = re.compile(r'Provisioning (with [\w-]+ )?step had errors')
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.provisioners = {}
        self.build_start = None
        self.build_end = None
        self.warnings = []
        
    def parse_log(self):
        """Parse the Packer log file."""
        current_provisioner = None
        provisioner_start_time = None
        
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                timestamp = self._extract_timestamp(line)
                
                # Track overall build time
                if 'Starting build' in line or 'Build \'amazon-ebs\' finished' in line:
                    if self.build_start is None:
                        self.build_start = timestamp
                    else:
                        self.build_end = timestamp
                
                # Provisioner start
                provisioner_match = self.PROVISIONER_START.search(line)
                if provisioner_match and timestamp:
                    current_provisioner = provisioner_match.group(1)
                    provisioner_start_time = timestamp
                    
                    if current_provisioner not in self.provisioners:
                        self.provisioners[current_provisioner] = ProvisionerStats(current_provisioner)
                
                # Provisioner end (look for next provisioner start or build end)
                if current_provisioner and provisioner_start_time:
                    if ('Provisioning with' in line and timestamp != provisioner_start_time) or \
                       'Build finished' in line or \
                       'Build \'amazon-ebs\' finished' in line:
                        if timestamp:
                            duration = (timestamp - provisioner_start_time).total_seconds()
                            self.provisioners[current_provisioner].add_execution(duration)
                            current_provisioner = None
                            provisioner_start_time = None
                
                # Collect warnings
                if 'Warning:' in line or 'WARN' in line:
                    self.warnings.append(line.strip())
    
    def _extract_timestamp(self, line: str) -> datetime:
        """Extract timestamp from log line."""
        match = self.TIMESTAMP_PATTERN.search(line)
        if match:
            try:
                # Parse ISO 8601 timestamp
                ts = match.group(1)
                return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                pass
        return None
    
    def get_sorted_provisioners(self) -> List[ProvisionerStats]:
        """Get provisioners sorted by total time (descending)."""
        return sorted(self.provisioners.values(), 
                     key=lambda p: p.total_time, 
                     reverse=True)
    
    def get_total_build_time(self) -> float:
        """Calculate total build time in seconds."""
        if self.build_start and self.build_end:
            return (self.build_end - self.build_start).total_seconds()
        return 0.0
    
    def get_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        sorted_provisioners = self.get_sorted_provisioners()
        if not sorted_provisioners:
            return ['No provisioner data found in log file']
        
        # Check for slow provisioners
        if sorted_provisioners[0].total_time > 300:  # 5 minutes
            recommendations.append(
                f"⚠️  '{sorted_provisioners[0].name}' takes {sorted_provisioners[0].total_time:.1f}s - "
                f"consider optimizing or splitting into parallel steps"
            )
        
        # Check for repeated provisioners
        for prov in sorted_provisioners:
            if prov.count > 1:
                recommendations.append(
                    f"⚠️  '{prov.name}' runs {prov.count} times - "
                    f"consider consolidating into single provisioner"
                )
        
        # Check for package manager operations
        pkg_managers = ['shell', 'ansible', 'chef']
        for prov in sorted_provisioners:
            if any(pm in prov.name.lower() for pm in pkg_managers):
                recommendations.append(
                    f"💡 '{prov.name}' may benefit from package caching or local mirrors"
                )
        
        # Check total provisioning time
        total_prov_time = sum(p.total_time for p in sorted_provisioners)
        total_build_time = self.get_total_build_time()
        
        if total_build_time > 0:
            prov_percentage = (total_prov_time / total_build_time) * 100
            if prov_percentage < 50:
                recommendations.append(
                    f"💡 Provisioning is only {prov_percentage:.1f}% of build time - "
                    f"consider optimizing builder startup/shutdown"
                )
        
        return recommendations or ['No specific optimization recommendations']
    
    def print_report(self, top_n: int = None):
        """Print analysis report to console."""
        print("=" * 70)
        print("PACKER BUILD ANALYSIS REPORT")
        print("=" * 70)
        print()
        
        # Build time summary
        build_time = self.get_total_build_time()
        if build_time > 0:
            print(f"Total Build Time: {timedelta(seconds=int(build_time))}")
            print()
        
        # Provisioner statistics
        print("PROVISIONER PERFORMANCE")
        print("-" * 70)
        
        sorted_provisioners = self.get_sorted_provisioners()
        display_provisioners = sorted_provisioners[:top_n] if top_n else sorted_provisioners
        
        if not display_provisioners:
            print("No provisioner data found in log file")
            print()
        else:
            print(f"{'Provisioner':<30} {'Count':<8} {'Total':<12} {'Avg':<12}")
            print("-" * 70)
            
            for prov in display_provisioners:
                print(f"{prov.name:<30} {prov.count:<8} "
                      f"{timedelta(seconds=int(prov.total_time))!s:<12} "
                      f"{timedelta(seconds=int(prov.avg_time))!s:<12}")
            print()
        
        # Warnings
        if self.warnings:
            print("WARNINGS DETECTED")
            print("-" * 70)
            for warning in self.warnings[:5]:  # Show first 5 warnings
                print(f"⚠️  {warning}")
            if len(self.warnings) > 5:
                print(f"... and {len(self.warnings) - 5} more warnings")
            print()
        
        # Recommendations
        print("OPTIMIZATION RECOMMENDATIONS")
        print("-" * 70)
        for rec in self.get_recommendations():
            print(rec)
        print()
        print("=" * 70)
    
    def to_json(self) -> str:
        """Export analysis as JSON."""
        data = {
            'build_time_seconds': self.get_total_build_time(),
            'provisioners': [p.to_dict() for p in self.get_sorted_provisioners()],
            'warnings_count': len(self.warnings),
            'recommendations': self.get_recommendations(),
        }
        return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Packer build logs for optimization opportunities'
    )
    parser.add_argument('log_file', type=Path, help='Path to Packer log file')
    parser.add_argument('--json', action='store_true', 
                       help='Output results as JSON')
    parser.add_argument('--top', type=int, metavar='N',
                       help='Show only top N slowest provisioners')
    
    args = parser.parse_args()
    
    if not args.log_file.exists():
        print(f"Error: Log file not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)
    
    analyzer = PackerBuildAnalyzer(args.log_file)
    
    print(f"Analyzing log file: {args.log_file}", file=sys.stderr)
    print("This may take a moment...", file=sys.stderr)
    print()
    
    analyzer.parse_log()
    
    if args.json:
        print(analyzer.to_json())
    else:
        analyzer.print_report(top_n=args.top)


if __name__ == '__main__':
    main()
