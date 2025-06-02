#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
# Sentinel Commander - Production Startup Script with Gunicorn + Uvicorn Workers + Logging
# This script runs the app in the background with separate log files.

APP_MODULE="app.main:app"
HOST="0.0.0.0"
PORT="80"
WORKERS=8
LOG_LEVEL="info"
LOG_DIR="logs/sentinel"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Timestamped logfile for startup
STARTUP_LOG="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"

echo "Launching Sentinel Commander via Gunicorn with $WORKERS Uvicorn workers..."
echo "Logs: $LOG_DIR/sentinel_gunicorn.log, $LOG_DIR/sentinel_access.log"

nohup gunicorn "$APP_MODULE" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "$HOST:$PORT" \
  --workers "$WORKERS" \
  --log-level "$LOG_LEVEL" \
  --access-logfile "$LOG_DIR/sentinel_access.log" \
  --error-logfile "$LOG_DIR/sentinel_gunicorn.log" \
  >> "$STARTUP_LOG" 2>&1 &