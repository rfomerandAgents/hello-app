#!/bin/bash
# Manual testing script for Unified Webhook Router

set -e

echo "=== Unified Webhook Router - Manual Testing ==="
echo ""

# Check if router is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Error: Router is not running on port 8000"
    echo "Start it first with: uv run trigger_webhook.py"
    exit 1
fi

echo "✅ Router is running"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo ""

# Test 2: ADW Plan Workflow
echo "Test 2: ADW Plan Workflow (New Issue)"
echo "--------------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issues" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 999,
      "body": "Please run adw_plan_iso for this feature request"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 3: IPE Plan Workflow
echo "Test 3: IPE Plan Workflow (New Issue)"
echo "--------------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issues" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 998,
      "body": "Please run ipe_plan_iso for this infrastructure change"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 4: ADW with ID and Model
echo "Test 4: ADW Test with ID and Model (Comment)"
echo "---------------------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issue_comment" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "created",
    "issue": {"number": 997},
    "comment": {
      "body": "adw_test_iso adw-12345678 sonnet"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 5: IPE with ID
echo "Test 5: IPE Test with ID (Comment)"
echo "-----------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issue_comment" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "created",
    "issue": {"number": 996},
    "comment": {
      "body": "ipe_test_iso ipe-87654321"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 6: Bot Message (Should be Ignored)
echo "Test 6: Bot Message - Should be Ignored"
echo "----------------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issue_comment" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "created",
    "issue": {"number": 995},
    "comment": {
      "body": "[ADW-AGENTS] adw_plan_iso completed successfully"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 7: No Workflow (Should be Ignored)
echo "Test 7: No Workflow Command - Should be Ignored"
echo "------------------------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issues" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 994,
      "body": "This is just a regular bug report without any workflow command"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 8: Dependent Workflow Without ID (Should Error)
echo "Test 8: Dependent Workflow Without ID - Should Error"
echo "----------------------------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issue_comment" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "created",
    "issue": {"number": 993},
    "comment": {
      "body": "adw_ship_iso"
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 9: Priority Test (IPE should win)
echo "Test 9: Priority Test - IPE First"
echo "----------------------------------"
curl -X POST http://localhost:8000/gh-webhook \
  -H "X-GitHub-Event: issues" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 992,
      "body": "Run ipe_plan_iso and then adw_build_iso"
    }
  }' | python3 -m json.tool
echo ""
echo ""

echo "=== All Manual Tests Complete ==="
echo ""
echo "Note: These are simulated webhooks. In production, these would come from GitHub."
echo "Check the router logs for detailed processing information."
