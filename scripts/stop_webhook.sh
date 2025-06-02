#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
# Sentinel Commander - Stop Webhook Script
# This script finds and terminates the Gunicorn process running the webhook handler.

APP_MODULE="webhook_app:app"

echo "Stopping Sentinel Webhook Service..."

# Find the Gunicorn process running this specific app
PID=$(ps aux | grep "$APP_MODULE" | grep gunicorn | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "No running Gunicorn process found for $APP_MODULE."
else
  echo "Killing process ID(s): $PID"
  kill $PID
  echo "Sentinel Webhook Service stopped."
fi
