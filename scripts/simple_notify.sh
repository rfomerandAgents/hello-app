#!/bin/bash
# Simple macOS TTS notification using built-in 'say' command
# Usage: ./simple_notify.sh "Your message here"

if [ -z "$1" ]; then
    echo "Usage: ./simple_notify.sh <message>"
    exit 1
fi

MESSAGE="$*"
echo "🔊 Speaking: $MESSAGE"
say "$MESSAGE"
echo "✅ Notification spoken"
