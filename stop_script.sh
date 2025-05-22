#!/bin/bash

# Sentinel Commander - Stop Script
# This script finds and terminates the Gunicorn process running Sentinel Commander.

APP_MODULE="app.main:app"

echo "Stopping Sentinel Commander..."

# Find the Gunicorn process running this specific app
PID=$(ps aux | grep "$APP_MODULE" | grep gunicorn | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "No running Gunicorn process found for $APP_MODULE."
else
  echo "Killing process ID(s): $PID"
  kill $PID
  echo "Sentinel Commander stopped."
fi