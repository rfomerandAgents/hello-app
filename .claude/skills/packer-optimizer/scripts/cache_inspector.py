#!/usr/bin/env python3
"""
Packer Cache Inspector

Analyzes Packer cache usage and effectiveness to identify optimization opportunities.

Usage:
    # Inspect local Packer cache
    python cache_inspector.py
    
    # Inspect specific cache directory
    python cache_inspector.py --cache-dir /custom/cache/path
    
    # Show detailed cache statistics
    python cache_inspector.py --detailed
    
    # Clean old cache entries
    python cache_inspector.py --clean --days 30
"""

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CacheEntry:
    """Represents a cache entry."""
    path: Path
    size: int
    last_accessed: datetime
    last_modified: datetime
    cache_type: str
    
    @property
    def age_days(self) -> int:
        """Age of cache entry in days."""
        return (datetime.now() - self.last_accessed).days
    
    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size / (1024 * 1024)


class CacheInspector:
    """Inspects and analyzes Packer cache."""
    
    CACHE_TYPES = {
        'plugins': ['.packer.d/plugins'],
        'downloads': ['packer_cache', 'downloads'],
        'packages': ['apt/archives', 'yum', 'apk'],
        'builds': ['go/pkg', 'cargo', 'gradle', 'maven'],
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self.entries = []
        self.stats = defaultdict(lambda: {'count': 0, 'size': 0})
    
    def _get_default_cache_dir(self) -> Path:
        """Get default Packer cache directory."""
        # Check environment variable
        if 'PACKER_CACHE_DIR' in os.environ:
            return Path(os.environ['PACKER_CACHE_DIR'])
        
        # Default locations
        home = Path.home()
        default_locations = [
            home / '.packer.d',
            home / '.cache' / 'packer',
            Path('/tmp/packer-cache'),
        ]
        
        for location in default_locations:
            if location.exists():
                return location
        
        return home / '.packer.d'
    
    def scan_cache(self):
        """Scan cache directory and collect statistics."""
        if not self.cache_dir.exists():
            print(f"Cache directory not found: {self.cache_dir}", file=sys.stderr)
            return
        
        print(f"Scanning cache directory: {self.cache_dir}")
        print("This may take a moment...\n")
        
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    
                    # Determine cache type
                    cache_type = self._determine_cache_type(file_path)
                    
                    entry = CacheEntry(
                        path=file_path,
                        size=stat.st_size,
                        last_accessed=datetime.fromtimestamp(stat.st_atime),
                        last_modified=datetime.fromtimestamp(stat.st_mtime),
                        cache_type=cache_type,
                    )
                    
                    self.entries.append(entry)
                    self.stats[cache_type]['count'] += 1
                    self.stats[cache_type]['size'] += entry.size
                    
                except (OSError, PermissionError) as e:
                    print(f"Warning: Could not access {file_path}: {e}", file=sys.stderr)
    
    def _determine_cache_type(self, path: Path) -> str:
        """Determine the type of cache based on path."""
        path_str = str(path).lower()
        
        for cache_type, patterns in self.CACHE_TYPES.items():
            if any(pattern in path_str for pattern in patterns):
                return cache_type
        
        return 'other'
    
    def print_summary(self):
        """Print cache summary statistics."""
        print("=" * 70)
        print("PACKER CACHE SUMMARY")
        print("=" * 70)
        print()
        
        # Overall statistics
        total_entries = len(self.entries)
        total_size = sum(e.size for e in self.entries)
        
        print(f"Total Entries: {total_entries:,}")
        print(f"Total Size: {self._format_size(total_size)}")
        print(f"Cache Directory: {self.cache_dir}")
        print()
        
        # Statistics by type
        print("CACHE BREAKDOWN BY TYPE")
        print("-" * 70)
        print(f"{'Type':<15} {'Entries':<12} {'Size':<15} {'Percentage':<12}")
        print("-" * 70)
        
        for cache_type in sorted(self.stats.keys()):
            stats = self.stats[cache_type]
            percentage = (stats['size'] / total_size * 100) if total_size > 0 else 0
            print(f"{cache_type:<15} {stats['count']:<12,} "
                  f"{self._format_size(stats['size']):<15} {percentage:.1f}%")
        print()
    
    def print_detailed_analysis(self):
        """Print detailed cache analysis."""
        print("DETAILED CACHE ANALYSIS")
        print("-" * 70)
        print()
        
        # Oldest entries
        print("Oldest Cache Entries (by last access):")
        oldest = sorted(self.entries, key=lambda e: e.last_accessed)[:10]
        for entry in oldest:
            print(f"  {entry.age_days:>4} days old - "
                  f"{self._format_size(entry.size):>10} - "
                  f"{entry.path.name}")
        print()
        
        # Largest entries
        print("Largest Cache Entries:")
        largest = sorted(self.entries, key=lambda e: e.size, reverse=True)[:10]
        for entry in largest:
            print(f"  {self._format_size(entry.size):>10} - "
                  f"{entry.cache_type:<10} - "
                  f"{entry.path.name}")
        print()
        
        # Age distribution
        print("Age Distribution:")
        age_buckets = {'<7 days': 0, '7-30 days': 0, '30-90 days': 0, '>90 days': 0}
        for entry in self.entries:
            age = entry.age_days
            if age < 7:
                age_buckets['<7 days'] += 1
            elif age < 30:
                age_buckets['7-30 days'] += 1
            elif age < 90:
                age_buckets['30-90 days'] += 1
            else:
                age_buckets['>90 days'] += 1
        
        for bucket, count in age_buckets.items():
            percentage = (count / len(self.entries) * 100) if self.entries else 0
            print(f"  {bucket:<15} {count:>6,} entries ({percentage:>5.1f}%)")
        print()
    
    def print_recommendations(self):
        """Print cache optimization recommendations."""
        print("RECOMMENDATIONS")
        print("-" * 70)
        
        total_size = sum(e.size for e in self.entries)
        old_entries = [e for e in self.entries if e.age_days > 30]
        old_size = sum(e.size for e in old_entries)
        
        if not self.entries:
            print("✅ Cache is empty or not found")
            return
        
        recommendations = []
        
        # Size recommendations
        if total_size > 10 * 1024 * 1024 * 1024:  # > 10GB
            recommendations.append(
                f"⚠️  Cache size is large ({self._format_size(total_size)}) - "
                f"consider implementing cleanup strategy"
            )
        
        # Age recommendations
        if old_entries:
            recommendations.append(
                f"💡 {len(old_entries):,} entries are older than 30 days "
                f"({self._format_size(old_size)}) - consider cleanup"
            )
        
        # Type-specific recommendations
        for cache_type, stats in self.stats.items():
            if stats['size'] > 5 * 1024 * 1024 * 1024:  # > 5GB
                recommendations.append(
                    f"💡 '{cache_type}' cache is large "
                    f"({self._format_size(stats['size'])}) - "
                    f"review if all entries are needed"
                )
        
        # Plugin recommendations
        if 'plugins' in self.stats:
            plugin_count = self.stats['plugins']['count']
            if plugin_count > 20:
                recommendations.append(
                    f"💡 Many Packer plugins cached ({plugin_count}) - "
                    f"consider removing unused plugins"
                )
        
        if recommendations:
            for rec in recommendations:
                print(rec)
        else:
            print("✅ Cache appears healthy - no specific recommendations")
        
        print()
        print("General best practices:")
        print("  • Implement automated cache cleanup (e.g., delete entries >30 days)")
        print("  • Monitor cache size and set limits")
        print("  • Use HCP Packer for team-wide image sharing")
        print("  • Consider separate caches for CI/CD vs. local development")
    
    def clean_old_entries(self, days: int, dry_run: bool = True):
        """Clean cache entries older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        to_delete = [e for e in self.entries if e.last_accessed < cutoff_date]
        
        if not to_delete:
            print(f"No cache entries older than {days} days found")
            return
        
        total_size = sum(e.size for e in to_delete)
        
        print(f"\n{'DRY RUN: ' if dry_run else ''}Found {len(to_delete):,} entries older than {days} days")
        print(f"Total size to clean: {self._format_size(total_size)}")
        print()
        
        if dry_run:
            print("Run with --no-dry-run to actually delete these entries")
            return
        
        deleted_count = 0
        deleted_size = 0
        
        for entry in to_delete:
            try:
                entry.path.unlink()
                deleted_count += 1
                deleted_size += entry.size
                print(f"Deleted: {entry.path}")
            except OSError as e:
                print(f"Error deleting {entry.path}: {e}", file=sys.stderr)
        
        print()
        print(f"Cleanup complete: Deleted {deleted_count:,} entries ({self._format_size(deleted_size)})")
    
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


def main():
    parser = argparse.ArgumentParser(
        description='Inspect and analyze Packer cache usage'
    )
    parser.add_argument('--cache-dir', type=Path,
                       help='Cache directory to inspect (default: auto-detect)')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed cache analysis')
    parser.add_argument('--clean', action='store_true',
                       help='Clean old cache entries')
    parser.add_argument('--days', type=int, default=30,
                       help='Age threshold for cleanup in days (default: 30)')
    parser.add_argument('--no-dry-run', action='store_true',
                       help='Actually delete files (default is dry run)')
    
    args = parser.parse_args()
    
    inspector = CacheInspector(args.cache_dir)
    inspector.scan_cache()
    
    if not inspector.entries:
        print("No cache entries found")
        sys.exit(0)
    
    inspector.print_summary()
    
    if args.detailed:
        print()
        inspector.print_detailed_analysis()
    
    print()
    inspector.print_recommendations()
    
    if args.clean:
        print()
        print("=" * 70)
        print("CACHE CLEANUP")
        print("=" * 70)
        inspector.clean_old_entries(args.days, dry_run=not args.no_dry_run)


if __name__ == '__main__':
    main()
