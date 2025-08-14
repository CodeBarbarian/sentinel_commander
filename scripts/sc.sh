#!/usr/bin/env bash
set -euo pipefail

# --- Config (override via .env or env) ---
APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT_API="${APP_PORT_API:-80}"
APP_PORT_WEBHOOK="${APP_PORT_WEBHOOK:-8000}"
APP_WORKERS_API="${APP_WORKERS_API:-8}"
APP_WORKERS_WEBHOOK="${APP_WORKERS_WEBHOOK:-2}"
APP_LOG_LEVEL="${APP_LOG_LEVEL:-info}"

APP_MODULE_API="${APP_MODULE_API:-app.main:app}"
APP_MODULE_WEBHOOK="${APP_MODULE_WEBHOOK:-app.webhook_app:app}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR_API="${LOG_DIR_API:-$ROOT_DIR/logs/sentinel}"
LOG_DIR_WEBHOOK="${LOG_DIR_WEBHOOK:-$ROOT_DIR/logs/webhook}"
RUN_DIR="${RUN_DIR:-$ROOT_DIR/run}"   # pidfiles

# --- Load .env if present ---
if [ -f "$ROOT_DIR/.env" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "$ROOT_DIR/.env" | xargs)
fi

mkdir -p "$LOG_DIR_API" "$LOG_DIR_WEBHOOK" "$RUN_DIR"

PID_API="$RUN_DIR/sentinel.pid"
PID_WEBHOOK="$RUN_DIR/webhook.pid"

timestamp() { date +%Y%m%d_%H%M%S; }

start_service() {
  local name="$1" module="$2" host="$3" port="$4" workers="$5" logdir="$6" pidfile="$7"

  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] already running (PID $(cat "$pidfile"))."
    return 0
  fi

  local startlog="$logdir/startup_$(timestamp).log"
  echo "[$name] starting on ${host}:${port} with ${workers} workers …"
  echo "  logs: $logdir"
  nohup gunicorn "$module" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "${host}:${port}" \
    --workers "$workers" \
    --log-level "$APP_LOG_LEVEL" \
    --access-logfile "$logdir/access.log" \
    --error-logfile "$logdir/error.log" \
    --pid "$pidfile" \
    >> "$startlog" 2>&1 &
  sleep 0.5
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] started (PID $(cat "$pidfile"))."
  else
    echo "[$name] failed to start. See $startlog"
    exit 1
  fi
}

stop_service() {
  local name="$1" pidfile="$2"
  if [ ! -f "$pidfile" ]; then
    echo "[$name] not running (no pidfile)."
    return 0
  fi
  local pid
  pid="$(cat "$pidfile")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "[$name] stopping PID $pid …"
    kill "$pid" || true
    # Graceful wait, then SIGKILL fallback
    for i in {1..10}; do
      if kill -0 "$pid" 2>/dev/null; then sleep 0.5; else break; fi
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "[$name] force-killing PID $pid …"
      kill -9 "$pid" || true
    fi
  else
    echo "[$name] not running."
  fi
  rm -f "$pidfile"
  echo "[$name] stopped."
}

status_service() {
  local name="$1" pidfile="$2"
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] RUNNING (PID $(cat "$pidfile"))."
  else
    echo "[$name] STOPPED."
  fi
}

bootstrap_if_needed() {
  # Optional: ensure DB + migrations + admin before starting
  if command -v python >/dev/null 2>&1; then
    (cd "$ROOT_DIR" && python manage.py doctor || true)
    (cd "$ROOT_DIR" && python manage.py bootstrap || true)
  fi
}

usage() {
  cat <<EOF
Usage: $0 <start|stop|restart|status> [api|webhook|all] [--no-bootstrap]

Commands:
  start       Start one or both services
  stop        Stop one or both services
  restart     Restart one or both services
  status      Show status

Targets:
  api         $APP_MODULE_API (port $APP_PORT_API)
  webhook     $APP_MODULE_WEBHOOK (port $APP_PORT_WEBHOOK)
  all         both services

Examples:
  $0 start api
  $0 restart all
  $0 status
EOF
}

CMD="${1:-}"; TARGET="${2:-all}"; BOOTSTRAP=true
shift $(( $# > 0 ? 1 : 0 ))
shift $(( $# > 0 ? 1 : 0 )) || true
for arg in "$@"; do
  [ "$arg" = "--no-bootstrap" ] && BOOTSTRAP=false
done

case "$CMD" in
  start)
    $BOOTSTRAP && bootstrap_if_needed
    case "$TARGET" in
      api)
        start_service "API" "$APP_MODULE_API" "$APP_HOST" "$APP_PORT_API" "$APP_WORKERS_API" "$LOG_DIR_API" "$PID_API"
        ;;
      webhook)
        start_service "WEBHOOK" "$APP_MODULE_WEBHOOK" "$APP_HOST" "$APP_PORT_WEBHOOK" "$APP_WORKERS_WEBHOOK" "$LOG_DIR_WEBHOOK" "$PID_WEBHOOK"
        ;;
      all)
        $BOOTSTRAP && bootstrap_if_needed
        start_service "API" "$APP_MODULE_API" "$APP_HOST" "$APP_PORT_API" "$APP_WORKERS_API" "$LOG_DIR_API" "$PID_API"
        start_service "WEBHOOK" "$APP_MODULE_WEBHOOK" "$APP_HOST" "$APP_PORT_WEBHOOK" "$APP_WORKERS_WEBHOOK" "$LOG_DIR_WEBHOOK" "$PID_WEBHOOK"
        ;;
      *) usage; exit 1;;
    esac
    ;;
  stop)
    case "$TARGET" in
      api) stop_service "API" "$PID_API" ;;
      webhook) stop_service "WEBHOOK" "$PID_WEBHOOK" ;;
      all) stop_service "WEBHOOK" "$PID_WEBHOOK"; stop_service "API" "$PID_API" ;;
      *) usage; exit 1;;
    esac
    ;;
  restart)
    case "$TARGET" in
      api)
        stop_service "API" "$PID_API"
        $BOOTSTRAP && bootstrap_if_needed
        start_service "API" "$APP_MODULE_API" "$APP_HOST" "$APP_PORT_API" "$APP_WORKERS_API" "$LOG_DIR_API" "$PID_API"
        ;;
      webhook)
        stop_service "WEBHOOK" "$PID_WEBHOOK"
        $BOOTSTRAP && bootstrap_if_needed
        start_service "WEBHOOK" "$APP_MODULE_WEBHOOK" "$APP_HOST" "$APP_PORT_WEBHOOK" "$APP_WORKERS_WEBHOOK" "$LOG_DIR_WEBHOOK" "$PID_WEBHOOK"
        ;;
      all)
        stop_service "WEBHOOK" "$PID_WEBHOOK"
        stop_service "API" "$PID_API"
        $BOOTSTRAP && bootstrap_if_needed
        start_service "API" "$APP_MODULE_API" "$APP_HOST" "$APP_PORT_API" "$APP_WORKERS_API" "$LOG_DIR_API" "$PID_API"
        start_service "WEBHOOK" "$APP_MODULE_WEBHOOK" "$APP_HOST" "$APP_PORT_WEBHOOK" "$APP_WORKERS_WEBHOOK" "$LOG_DIR_WEBHOOK" "$PID_WEBHOOK"
        ;;
      *) usage; exit 1;;
    esac
    ;;
  status)
    status_service "API" "$PID_API"
    status_service "WEBHOOK" "$PID_WEBHOOK"
    ;;
  *) usage; exit 1;;
esac
