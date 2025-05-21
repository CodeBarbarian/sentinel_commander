#!/bin/bash

# Sentinel Commander - Production Startup Script with Gunicorn + Uvicorn Workers
# This is a simple script to launch the Sentinel Commander application using Gunicorn with Uvicorn workers.
# For ease of use, this script is designed to be run from the root directory of the project.

APP_MODULE="app.main:app"
HOST="0.0.0.0"
PORT="8000"
WORKERS=4
LOG_LEVEL="info"

echo "Launching Sentinel Commander via Gunicorn with $WORKERS Uvicorn workers"

exec gunicorn "$APP_MODULE" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "$HOST:$PORT" \
  --workers "$WORKERS" \
  --log-level "$LOG_LEVEL"