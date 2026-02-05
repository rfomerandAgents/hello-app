#!/bin/bash
# Workflow Health Monitoring Script
# Run via cron: */15 * * * * /path/to/monitor_workflow_health.sh
#
# Usage:
#   ./scripts/monitor_workflow_health.sh
#
# Options:
#   --auto-fix    Automatically fix auto-fixable issues
#   --json        Output results in JSON format
#
# Example cron setup:
#   crontab -e
#   # Add line: */15 * * * * {{REPO_PATH}}/scripts/monitor_workflow_health.sh

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run health check
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running workflow health check..."
if uv run adws/adw_tests/workflow_health_check.py "$@"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Health check passed" >> logs/health_check.log
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Health check failed" >> logs/health_check.log

    # Optional: Send notification (uncomment and configure as needed)
    # curl -X POST "$SLACK_WEBHOOK" -H "Content-Type: application/json" \
    #     -d '{"text":"ADW Workflow health check failed. Check logs/health_check.log for details."}'

    exit 1
fi
