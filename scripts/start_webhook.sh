#!/bin/bash
cd "$(dirname "$0")/.." || exit 1

# Load environment
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Sentinel Commander - Webhook Service Startup Script
APP_MODULE="app.webhook_app:app"
HOST="0.0.0.0"
PORT="8000"
WORKERS=2
LOG_LEVEL="info"
LOG_DIR="logs/webhook"

mkdir -p "$LOG_DIR"
STARTUP_LOG="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"

echo "Launching Sentinel Webhook Listener via Gunicorn with $WORKERS Uvicorn workers..."
echo "Logs: $LOG_DIR/webhook_gunicorn.log, $LOG_DIR/webhook_access.log"

nohup gunicorn "$APP_MODULE" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "$HOST:$PORT" \
  --workers "$WORKERS" \
  --log-level "$LOG_LEVEL" \
  --access-logfile "$LOG_DIR/webhook_access.log" \
  --error-logfile "$LOG_DIR/webhook_gunicorn.log" \
  >> "$STARTUP_LOG" 2>&1 &
