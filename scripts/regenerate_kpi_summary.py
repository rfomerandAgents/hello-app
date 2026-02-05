#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///

"""
Regenerate agentic_kpis_summary.md from agentic_kpis.md entries.

This script parses the ADW KPIs table in agentic_kpis.md and calculates
aggregate metrics to generate agentic_kpis_summary.md.

Usage:
    uv run scripts/regenerate_kpi_summary.py

    # Or with explicit paths:
    uv run scripts/regenerate_kpi_summary.py --entries app_docs/agentic_kpis.md --summary app_docs/agentic_kpis_summary.md
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


class SimpleLogger:
    """Simple logger for console output."""

    def info(self, msg):
        print(f"INFO: {msg}", file=sys.stderr)

    def warning(self, msg):
        print(f"WARNING: {msg}", file=sys.stderr)

    def error(self, msg):
        print(f"ERROR: {msg}", file=sys.stderr)


class KPIEntry:
    """Represents a single KPI entry from the table."""

    def __init__(self, date: str, adw_id: str, issue_number: str,
                 issue_class: str, attempts: int, plan_size: int,
                 diff_added: int, diff_removed: int, diff_files: int,
                 created: str, updated: str):
        self.date = date
        self.adw_id = adw_id
        self.issue_number = issue_number
        self.issue_class = issue_class
        self.attempts = attempts
        self.plan_size = plan_size
        self.diff_added = diff_added
        self.diff_removed = diff_removed
        self.diff_files = diff_files
        self.created = created
        self.updated = updated

    @property
    def diff_total(self) -> int:
        """Total diff size (added + removed)."""
        return self.diff_added + self.diff_removed


def parse_diff_size(diff_str: str) -> Tuple[int, int, int]:
    """
    Parse diff size string like '166/13/13' into (added, removed, files).

    Args:
        diff_str: String in format "Added/Removed/Files"

    Returns:
        Tuple of (added, removed, files) as integers
    """
    try:
        parts = diff_str.split('/')
        if len(parts) != 3:
            return (0, 0, 0)
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return (0, 0, 0)


def parse_kpi_entries(entries_file: Path, logger: SimpleLogger) -> List[KPIEntry]:
    """
    Parse KPI entries from the markdown table.

    Args:
        entries_file: Path to agentic_kpis.md
        logger: Logger instance

    Returns:
        List of KPIEntry objects
    """
    if not entries_file.exists():
        logger.error(f"Entries file not found: {entries_file}")
        return []

    content = entries_file.read_text()
    entries = []

    # Find the ADW KPIs table section
    lines = content.split('\n')
    in_table = False
    header_seen = False

    for line in lines:
        # Look for table header
        if '| Date' in line and '| ADW ID' in line:
            in_table = True
            continue

        # Skip separator line (contains dashes between pipes)
        if in_table and not header_seen and '|' in line and '---' in line:
            header_seen = True
            continue

        # Parse data rows
        if in_table and header_seen:
            # Stop if we hit an empty line or another section
            if not line.strip() or (line.strip().startswith('#') and not '|' in line):
                break

            if line.strip().startswith('|'):
                # Split by pipe and clean up
                parts = [p.strip() for p in line.split('|')[1:-1]]  # Skip first/last empty

                if len(parts) < 9:
                    logger.warning(f"Skipping malformed row: {line}")
                    continue

                try:
                    date = parts[0]
                    adw_id = parts[1]
                    issue_number = parts[2]
                    issue_class = parts[3]
                    attempts = int(parts[4])
                    plan_size = int(parts[5])
                    diff_added, diff_removed, diff_files = parse_diff_size(parts[6])
                    created = parts[7]
                    updated = parts[8] if len(parts) > 8 else '-'

                    entry = KPIEntry(
                        date=date,
                        adw_id=adw_id,
                        issue_number=issue_number,
                        issue_class=issue_class,
                        attempts=attempts,
                        plan_size=plan_size,
                        diff_added=diff_added,
                        diff_removed=diff_removed,
                        diff_files=diff_files,
                        created=created,
                        updated=updated
                    )
                    entries.append(entry)

                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing row: {line} - {e}")
                    continue

    logger.info(f"Parsed {len(entries)} KPI entries")
    return entries


def calculate_current_streak(entries: List[KPIEntry]) -> int:
    """
    Calculate current streak (consecutive rows from bottom where Attempts <= 2).

    Args:
        entries: List of KPIEntry objects

    Returns:
        Current streak count
    """
    streak = 0
    for entry in reversed(entries):
        if entry.attempts <= 2:
            streak += 1
        else:
            break
    return streak


def calculate_longest_streak(entries: List[KPIEntry]) -> int:
    """
    Calculate longest streak (maximum consecutive sequence where Attempts <= 2).

    Args:
        entries: List of KPIEntry objects

    Returns:
        Longest streak count
    """
    max_streak = 0
    current_streak = 0

    for entry in entries:
        if entry.attempts <= 2:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def calculate_summary_metrics(entries: List[KPIEntry], logger: SimpleLogger) -> dict:
    """
    Calculate all summary metrics from entries.

    Args:
        entries: List of KPIEntry objects
        logger: Logger instance

    Returns:
        Dictionary of metric names to values
    """
    if not entries:
        logger.warning("No entries found, returning zero metrics")
        return {
            'current_streak': 0,
            'longest_streak': 0,
            'total_plan_size': 0,
            'largest_plan_size': 0,
            'total_diff_size': 0,
            'largest_diff_size': 0,
            'average_presence': 0.0
        }

    current_streak = calculate_current_streak(entries)
    longest_streak = calculate_longest_streak(entries)

    plan_sizes = [e.plan_size for e in entries]
    total_plan_size = sum(plan_sizes)
    largest_plan_size = max(plan_sizes)

    diff_totals = [e.diff_total for e in entries]
    total_diff_size = sum(diff_totals)
    largest_diff_size = max(diff_totals)

    attempts = [e.attempts for e in entries]
    average_presence = sum(attempts) / len(attempts) if attempts else 0.0

    logger.info(f"Current Streak: {current_streak}")
    logger.info(f"Longest Streak: {longest_streak}")
    logger.info(f"Total Plan Size: {total_plan_size}")
    logger.info(f"Largest Plan Size: {largest_plan_size}")
    logger.info(f"Total Diff Size: {total_diff_size}")
    logger.info(f"Largest Diff Size: {largest_diff_size}")
    logger.info(f"Average Presence: {average_presence:.2f}")

    return {
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_plan_size': total_plan_size,
        'largest_plan_size': largest_plan_size,
        'total_diff_size': total_diff_size,
        'largest_diff_size': largest_diff_size,
        'average_presence': average_presence
    }


def generate_summary_markdown(metrics: dict, logger: SimpleLogger) -> str:
    """
    Generate the summary markdown file content.

    Args:
        metrics: Dictionary of calculated metrics
        logger: Logger instance

    Returns:
        Markdown content as string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""# Agentic KPIs Summary

Performance metrics for the AI Developer Workflow (ADW) system.

> **Note:** This file is auto-generated from `agentic_kpis.md` entries.
> Run `python scripts/regenerate_kpi_summary.py` to update.

## Summary Metrics

| Metric            | Value       | Last Updated     |
| ----------------- | ----------- | ---------------- |
| Current Streak    | {metrics['current_streak']}          | {timestamp} |
| Longest Streak    | {metrics['longest_streak']}          | {timestamp} |
| Total Plan Size   | {metrics['total_plan_size']} lines  | {timestamp} |
| Largest Plan Size | {metrics['largest_plan_size']} lines   | {timestamp} |
| Total Diff Size   | {metrics['total_diff_size']} lines | {timestamp} |
| Largest Diff Size | {metrics['largest_diff_size']} lines   | {timestamp} |
| Average Presence  | {metrics['average_presence']:.2f}        | {timestamp} |
"""

    return content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Regenerate agentic_kpis_summary.md from entries'
    )
    parser.add_argument(
        '--entries',
        type=str,
        default='app_docs/agentic_kpis.md',
        help='Path to entries file (default: app_docs/agentic_kpis.md)'
    )
    parser.add_argument(
        '--summary',
        type=str,
        default='app_docs/agentic_kpis_summary.md',
        help='Path to summary output file (default: app_docs/agentic_kpis_summary.md)'
    )

    args = parser.parse_args()
    logger = SimpleLogger()

    try:
        # Resolve paths relative to repo root
        repo_root = Path(__file__).parent.parent
        entries_file = repo_root / args.entries
        summary_file = repo_root / args.summary

        logger.info(f"Reading entries from: {entries_file}")
        logger.info(f"Writing summary to: {summary_file}")

        # Parse entries
        entries = parse_kpi_entries(entries_file, logger)

        if not entries:
            logger.error("No entries found to process")
            return 1

        # Calculate metrics
        metrics = calculate_summary_metrics(entries, logger)

        # Generate summary
        summary_content = generate_summary_markdown(metrics, logger)

        # Write summary file
        summary_file.write_text(summary_content)
        logger.info(f"Successfully wrote summary to {summary_file}")

        return 0

    except Exception as e:
        logger.error(f"Failed to regenerate summary: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
