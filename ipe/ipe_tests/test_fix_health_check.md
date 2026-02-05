# Fix Health Check Testing Documentation

## Test Results - 2024-11-22

### Test 1: Dry-Run Mode
**Command:** `uv run ipe/ipe_tests/fix_health_check.py --dry-run`

**Initial State:**
- Port 8001: NOT listening
- Cloudflared: NOT running
- External endpoints: HTTP 530

**Result:** ✅ PASS
- Correctly identified both issues
- Showed what would be fixed without making changes
- No services started

### Test 2: Auto-Fix Mode (Initial Fix)
**Command:** `uv run ipe/ipe_tests/fix_health_check.py --auto`

**Initial State:**
- Port 8001: NOT listening
- Cloudflared: NOT running

**Result:** ✅ PASS
- Started webhook server on port 8001 (PID: 23606)
- Started cloudflared tunnel (PID: 23639)
- Verified all health checks passed
- Created log files:
  - logs/webhook_server.log
  - logs/webhook_server.err
  - logs/cloudflared.log
  - logs/cloudflared.err

**Final State:**
- Port 8001: ✅ listening
- Local health: ✅ HTTP 200
- Cloudflared: ✅ running
- External health: ✅ HTTP 404
- External webhook: ✅ HTTP 405 (expected)
- Overall: ✅ HEALTHY

### Test 3: Auto-Fix Mode (Already Healthy)
**Command:** `uv run ipe/ipe_tests/fix_health_check.py --auto`

**Initial State:** All services healthy

**Result:** ✅ PASS
- Detected system is already healthy
- Displayed message: "System is already healthy - no fixes needed!"
- Made no changes
- Exited cleanly

### Test 4: Interactive Mode
**Command:** `echo "y" | uv run ipe/ipe_tests/fix_health_check.py`

**Initial State:** Services stopped

**Result:** ✅ PASS
- Prompted user for confirmation
- Accepted "y" response
- Started both services successfully
- Verified fixes worked
- Final state: HEALTHY

### Test 5: Health Check Integration
**Command:** `uv run ipe/ipe_tests/webhook_tunnel_health_check.py`

**Result:** ✅ PASS
- All 5 checks passed
- Port 8001 listening
- Local health endpoint responding
- Cloudflared process running
- External endpoints accessible via tunnel

## Success Criteria Verification

- ✅ Script can detect failed health checks
- ✅ Script can start webhook server successfully
- ✅ Script can start cloudflared tunnel successfully
- ✅ Script verifies fixes worked
- ✅ Slash command provides clear before/after status
- ✅ --dry-run mode works without making changes
- ✅ --auto mode fixes without prompting
- ✅ Interactive mode prompts for confirmation
- ✅ Handles already-healthy state gracefully
- ✅ Creates log files for debugging
- ✅ Background processes stay running after script exits

## Files Created

1. `ipe/ipe_tests/fix_health_check.py` (371 lines)
   - Main auto-fix script with comprehensive error handling
   - Supports --auto, --dry-run modes
   - Interactive confirmation
   - Health check parsing and verification

2. `.claude/commands/fix_health_check.md` (116 lines)
   - Claude slash command documentation
   - Usage instructions
   - Troubleshooting guide
   - Manual intervention steps

## Log Files Generated

Located in `logs/`:
- `webhook_server.log` - Webhook server stdout
- `webhook_server.err` - Webhook server stderr
- `cloudflared.log` - Tunnel stdout
- `cloudflared.err` - Tunnel stderr

## Known Behaviors

1. **Background Processes**: Services run detached and continue after script exits
2. **Log Rotation**: Logs are overwritten on each fix (not appended)
3. **External Health Check**: Returns HTTP 404/405 which is expected and healthy
4. **Startup Time**: Script waits 2-3 seconds for services to initialize
5. **Token Requirement**: Cloudflared requires CLOUDFLARED_TUNNEL_TOKEN in .env

## Integration Points

- Uses existing `webhook_tunnel_health_check.py` for status verification
- Follows same patterns as other IPE test scripts
- Compatible with existing webhook and tunnel infrastructure
- Works with Claude slash command system
