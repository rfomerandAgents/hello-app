# Tunnel Test - Verify GitHub Webhook Delivery

Test the complete webhook pipeline by creating a test GitHub issue and monitoring for webhook delivery.

## Command Usage

```bash
/tunnel_test
```

## What This Command Does

1. Creates a test GitHub issue with a unique timestamp
2. Monitors the webhook logs for incoming events
3. Reports success/failure of webhook delivery
4. Cleans up the test issue after verification

## Instructions

You are executing the `/tunnel_test` command to verify the GitHub → Cloudflare → Webhook pipeline.

### Step 1: Get Baseline

Check the current webhook log state before creating the test issue:

```bash
wc -l /tmp/webhook.log
```

Store this line count for comparison.

### Step 2: Create Test Issue

Create a test GitHub issue with a unique timestamp:

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
gh issue create \
  --title "[TUNNEL-TEST] Webhook test $TIMESTAMP" \
  --body "/patch - adw_patch_iso - Tunnel test created at $TIMESTAMP to verify webhook delivery" \
  --label "test"
```

Capture the issue number from the output.

### Step 3: Monitor Webhook Logs

Wait 10 seconds for GitHub to deliver the webhook, then check if it was received:

```bash
sleep 10
tail -50 /tmp/webhook.log | grep -i "tunnel-test\|issue_number"
```

### Step 4: Analyze Results

Check if the webhook was received by looking for:
- The issue number in the logs
- "Received webhook" message with the issue number
- "Detected ADW workflow" message
- HTTP 200 response from the webhook endpoint

### Step 5: Report Results

**If webhook was received:**
```
✅ TUNNEL TEST PASSED

Webhook pipeline is working correctly:
- GitHub sent webhook event
- Cloudflare tunnel delivered the event
- Webhook server received and processed it
- Issue #[NUMBER] was processed
- ADW workflow was triggered

Tunnel Status: HEALTHY
```

**If webhook was NOT received:**
```
❌ TUNNEL TEST FAILED

Webhook was not received within 10 seconds.

Possible issues:
1. GitHub webhook not configured or inactive
2. Cloudflare tunnel connectivity problem
3. Webhook server not listening on correct port
4. GitHub webhook delivery delayed

Diagnostics:
- Check webhook health: curl http://localhost:8001/health
- Check tunnel status: cloudflared tunnel info tac-webhook
- Check GitHub webhook settings: https://github.com/OWNER/REPO/settings/hooks

Tunnel Status: DEGRADED
```

### Step 6: Cleanup

Close the test issue after verification:

```bash
gh issue close [ISSUE_NUMBER] --comment "Tunnel test complete. Webhook delivery $([ webhook_received ] && echo 'successful' || echo 'failed')."
```

### Step 7: Additional Diagnostics

If the test fails, run these diagnostic commands:

```bash
# Check local webhook health
curl -s http://localhost:8001/health | jq .

# Check external tunnel access
curl -s https://somenetwork.org/health | jq .

# Check cloudflared tunnel status
cloudflared tunnel info tac-webhook

# Check webhook process
ps aux | grep trigger_webhook | grep -v grep

# Check recent webhook logs
tail -100 /tmp/webhook.log
```

## Success Criteria

The test passes if:
1. ✅ Test issue is created successfully
2. ✅ Webhook event appears in logs within 10 seconds
3. ✅ Webhook server processes the event (returns 200)
4. ✅ ADW workflow is detected and triggered
5. ✅ Bot posts a comment to the test issue

## Failure Scenarios

**Scenario 1: Issue created but no webhook**
- GitHub webhook not configured
- Webhook URL incorrect
- Event types not enabled

**Scenario 2: Webhook received locally but not externally**
- Cloudflare tunnel issue
- Port forwarding problem

**Scenario 3: Delayed webhook delivery**
- GitHub webhook queue backed up
- Network latency
- Wait longer (30-60 seconds)

## Notes

- Creates a real GitHub issue (will count against issue numbers)
- Issue is automatically closed after test
- Can be run multiple times safely
- Each test issue has a unique timestamp
- Test issues are labeled "test" for easy filtering
