#!/bin/bash

# Start webhook server with logging
LOGFILE="logs/webhook-$(date +%Y%m%d-%H%M%S).log"

echo "Starting Unified Webhook Router"
echo "Logging to: $LOGFILE"
echo "Port: 8001"
echo ""

cd {{REPO_PATH}}/triggers
PORT=8001 uv run trigger_webhook.py 2>&1 | tee "../$LOGFILE"
