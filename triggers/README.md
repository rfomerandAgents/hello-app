# Unified Webhook Router

A single webhook server that intelligently routes GitHub webhook events to either ADW (Application Development Workflow) or IPE (Infrastructure Platform Engineering) based on the workflow command detected in issue/comment content.

## Overview

The unified webhook router consolidates two separate webhook servers into a single entry point:
- Previously: `adws/adw_triggers/trigger_webhook.py` (port 8001) and `ipe/ipe_triggers/ipe_trigger_webhook.py` (port 8002)
- Now: `triggers/trigger_webhook.py` (port 8000)

## Features

- **Single Entry Point**: One webhook URL for all workflows
- **Intelligent Routing**: Automatically detects workflow type (ADW vs IPE)
- **Priority Routing**: IPE workflows checked first, then ADW
- **Bot Loop Prevention**: Ignores messages from ADW and IPE bots
- **Unified Health Check**: Single endpoint reports health of both subsystems
- **Stateless Router**: All state management delegated to ADW/IPE systems

## Quick Start

### Start the Unified Router

```bash
cd triggers/
uv run trigger_webhook.py
```

The server will start on `http://0.0.0.0:8000` by default.

### Custom Port

```bash
PORT=9000 uv run trigger_webhook.py
```

## Supported Workflows

### ADW Workflows (Application Code)

- `adw_plan_iso` - Create implementation plan
- `adw_build_iso` - Build the feature/fix
- `adw_test_iso` - Run tests (requires ADW ID)
- `adw_review_iso` - Review changes (requires ADW ID)
- `adw_document_iso` - Generate documentation (requires ADW ID)
- `adw_ship_iso` - Merge PR and deploy (requires ADW ID)
- `adw_sdlc_iso` - Full SDLC workflow
- `adw_patch_iso` - Quick patch workflow

### IPE Workflows (Infrastructure)

- `ipe_plan_iso` - Create infrastructure plan
- `ipe_build_iso` - Build Terraform changes
- `ipe_test_iso` - Validate Terraform (requires IPE ID)
- `ipe_review_iso` - Review infrastructure plan (requires IPE ID)
- `ipe_document_iso` - Generate infrastructure docs (requires IPE ID)
- `ipe_ship_iso` - Merge PR (manual apply by default, requires IPE ID)
- `ipe_sdlc_iso` - Full infrastructure SDLC

## Usage

### Trigger via GitHub Issue

Create a new issue with the workflow command in the body:

```markdown
## Feature Request: Add Dark Mode

Please run adw_plan_iso to implement this feature.
```

### Trigger via Issue Comment

Comment on an existing issue:

```markdown
adw_build_iso adw-12345678
```

Or for infrastructure:

```markdown
ipe_test_iso ipe-87654321
```

### Workflow with Model Selection

Specify the Claude model to use:

```markdown
adw_test_iso adw-12345678 sonnet
```

```markdown
ipe_test_iso ipe-87654321 haiku
```

## Routing Logic

1. **Check for Bot Messages**: Ignore if content contains `[ADW-AGENTS]` or `🤖 IPE`
2. **Detect Workflow Type**: Check for IPE workflows first, then ADW workflows
3. **Extract Details**: Parse workflow ID and model set from content
4. **Validate**: Ensure dependent workflows have required IDs
5. **Route**: Launch appropriate workflow script in background

## Endpoints

### POST /gh-webhook

Main webhook endpoint for GitHub events.

**GitHub Event Types Supported:**
- `issues` with action `opened`
- `issue_comment` with action `created`

**Response:**
```json
{
  "status": "accepted",
  "type": "adw",
  "workflow": "adw_plan_iso",
  "id": "adw-12345678"
}
```

Or if ignored:
```json
{
  "status": "ignored",
  "reason": "No ADW or IPE workflow detected"
}
```

### GET /health

Unified health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "unified-webhook-router",
  "port": 8000,
  "subsystems": {
    "adw": {
      "status": "healthy",
      "workflows": ["adw_plan_iso", "adw_build_iso", ...]
    },
    "ipe": {
      "status": "healthy",
      "workflows": ["ipe_plan_iso", "ipe_build_iso", ...]
    }
  },
  "workflows_available": {
    "adw": [...],
    "ipe": [...]
  }
}
```

## Testing

### Run Test Suite

```bash
cd triggers/
uv run test_unified_webhook.py
```

The test suite covers:
- ✅ ADW workflow detection
- ✅ IPE workflow detection
- ✅ Priority routing (IPE first)
- ✅ No workflow detection (ignore)
- ✅ Case-insensitive matching
- ✅ Bot message prevention
- ✅ All workflow types
- ✅ Dependent workflow validation
- ✅ ID and model parsing
- ✅ Multiline content
- ✅ Markdown formatted content

### Manual Testing

1. **Start the router:**
   ```bash
   uv run trigger_webhook.py
   ```

2. **Test health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Simulate webhook (ADW):**
   ```bash
   curl -X POST http://localhost:8000/gh-webhook \
     -H "X-GitHub-Event: issues" \
     -H "Content-Type: application/json" \
     -d '{
       "action": "opened",
       "issue": {
         "number": 123,
         "body": "adw_plan_iso"
       }
     }'
   ```

4. **Simulate webhook (IPE):**
   ```bash
   curl -X POST http://localhost:8000/gh-webhook \
     -H "X-GitHub-Event: issue_comment" \
     -H "Content-Type: application/json" \
     -d '{
       "action": "created",
       "issue": {"number": 456},
       "comment": {"body": "ipe_test_iso ipe-12345678"}
     }'
   ```

## Environment Variables

Required environment variables:

- `GITHUB_PAT` - GitHub Personal Access Token (for API access)
- `CLAUDE_CODE_OAUTH_TOKEN` - Claude API key (for agent execution)

Optional:

- `PORT` - Server port (default: 8000)
- `CLAUDE_CODE_PATH` - Path to Claude Code CLI (default: "claude")

## Configuration in GitHub

### Set Webhook URL

1. Go to your repository Settings → Webhooks
2. Click "Add webhook"
3. Set Payload URL to: `https://your-domain.com/gh-webhook`
4. Content type: `application/json`
5. Events: Select "Issues" and "Issue comments"
6. Active: ✅

### ngrok for Local Testing

```bash
# Install ngrok
brew install ngrok

# Start router
uv run trigger_webhook.py

# In another terminal, expose port
ngrok http 8000

# Use the ngrok URL as your webhook URL
# Example: https://abc123.ngrok.io/gh-webhook
```

## Migration from Legacy Webhooks

### Before (Two Separate Servers)

```bash
# Terminal 1: ADW webhook
cd adws/adw_triggers/
uv run trigger_webhook.py  # Port 8001

# Terminal 2: IPE webhook
cd ipe/ipe_triggers/
uv run ipe_trigger_webhook.py  # Port 8002
```

GitHub webhook configuration:
- ADW: `https://domain.com:8001/gh-webhook`
- IPE: `https://domain.com:8002/gh-webhook`

### After (Unified Router)

```bash
# Single terminal
cd triggers/
uv run trigger_webhook.py  # Port 8000
```

GitHub webhook configuration:
- Unified: `https://domain.com:8000/gh-webhook`

## Architecture

```
GitHub Webhook
      ↓
Unified Router (triggers/trigger_webhook.py)
      ↓
  [Detect Workflow Type]
      ↓
    ┌─────┴─────┐
    ↓           ↓
   ADW         IPE
    ↓           ↓
adws/*.py   ipe/*.py
```

## Error Handling

### Dependent Workflow Without ID

If a dependent workflow (like `adw_test_iso` or `ipe_ship_iso`) is triggered without an ID:

```markdown
❌ Error: `adw_test_iso` requires an existing ADW ID.

Example: `adw_test_iso adw-12345678`
```

### Bot Loop Prevention

Messages containing `[ADW-AGENTS]` or `🤖 IPE` are automatically ignored to prevent infinite loops.

### Workflow Not Found

If content doesn't contain any recognized workflow command:

```json
{
  "status": "ignored",
  "reason": "No ADW or IPE workflow detected"
}
```

## Troubleshooting

### Router won't start

**Issue**: Import errors or module not found

**Solution**: Ensure you're in the repository root and have installed dependencies:
```bash
cd triggers/
uv run trigger_webhook.py
```

### Webhooks not triggering

**Issue**: GitHub events not reaching the router

**Solution**:
1. Check webhook delivery in GitHub Settings → Webhooks
2. Verify ngrok tunnel is active (if using locally)
3. Check server logs for incoming requests

### Wrong workflow triggered

**Issue**: ADW triggered when expecting IPE (or vice versa)

**Solution**:
- Check workflow command spelling in issue/comment
- Remember: IPE workflows are checked first
- Ensure only one workflow command per message

### Health check shows degraded

**Issue**: One subsystem is unhealthy

**Solution**:
1. Check the health endpoint for details: `curl localhost:8000/health`
2. Verify ADW and IPE modules are importable
3. Check environment variables are set correctly

## Benefits

1. **Simplified Setup**: One webhook URL, one server process
2. **Easier Maintenance**: All routing logic in one place
3. **Better Resource Usage**: Single server instead of two
4. **Unified Monitoring**: Single health check endpoint
5. **Clear Separation**: Explicit routing makes subsystems clear
6. **Extensibility**: Easy to add new workflow types (e.g., DBW, MLW)

## Future Enhancements

- [ ] Add workflow metrics and monitoring
- [ ] Support for additional workflow types (Database, ML, etc.)
- [ ] Webhook signature verification
- [ ] Rate limiting and request throttling
- [ ] Workflow queue management
- [ ] Dead letter queue for failed workflows
- [ ] Distributed tracing support

## License

Copyright © {{YEAR}} {{PROJECT_NAME}}. All rights reserved.
