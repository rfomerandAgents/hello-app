#!/bin/bash
#
# Test Migration Assistant
# Quick test to verify the migration assistant is working
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

echo "Testing Migration Assistant"
echo "=========================="
echo ""

# Test 1: Dry run extraction of EC2 resources
echo "Test 1: Dry run extraction of EC2 resources"
echo "-------------------------------------------"
python3 "$SCRIPT_DIR/migrate_module.py" \
    --from-existing="$PROJECT_ROOT/terraform/main.tf" \
    --extract=ec2 \
    --name=test-ec2 \
    --dry-run

echo ""
echo "Test 1: PASSED"
echo ""

# Test 2: Dry run extraction of security resources
echo "Test 2: Dry run extraction of security resources"
echo "------------------------------------------------"
python3 "$SCRIPT_DIR/migrate_module.py" \
    --from-existing="$PROJECT_ROOT/terraform/main.tf" \
    --extract=security \
    --name=test-security \
    --dry-run

echo ""
echo "Test 2: PASSED"
echo ""

echo "=========================="
echo "All tests passed!"
echo ""
echo "To test full extraction (creates files), run:"
echo "  python3 scripts/migrate_module.py --from-existing=terraform/main.tf --extract=ec2 --name=test-module"
echo ""
