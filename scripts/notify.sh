#!/bin/bash
# Simple wrapper to send TTS notifications
# Usage: ./notify.sh "Your message here"

cd "$(dirname "$0")"
./tts_notify.py "$@"
