#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  . ".env"
  set +a
fi

mkdir -p logs
chmod 700 logs

VENV_DIR="${VENV_PATH:-}"
if [ -z "$VENV_DIR" ] && [ -n "${VENV_NAME:-}" ]; then
  VENV_DIR="$ROOT_DIR/${VENV_NAME}"
fi
if [ -z "$VENV_DIR" ]; then
  VENV_DIR="$ROOT_DIR/.venv"
fi

REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
CELERY_BROKER_URL="${CELERY_BROKER_URL:-$REDIS_URL}"
CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-$REDIS_URL}"
FLOWER_BASIC_AUTH="${FLOWER_BASIC_AUTH:-admin:change-me}"
FLOWER_ADDRESS="${FLOWER_ADDRESS:-127.0.0.1}"
FLOWER_PORT="${FLOWER_PORT:-5555}"
DJANGO_LOG_LEVEL="${DJANGO_LOG_LEVEL:-INFO}"

PYTHON="$VENV_DIR/bin/python"
CELERY="$VENV_DIR/bin/celery"

export REDIS_URL CELERY_BROKER_URL CELERY_RESULT_BACKEND FLOWER_BASIC_AUTH FLOWER_ADDRESS FLOWER_PORT DJANGO_LOG_LEVEL VENV_DIR

if ! command -v redis-server >/dev/null 2>&1; then
  echo "redis-server not found in PATH, make sure Redis is installed and available"
  exit 1
fi

redis-server --daemonize yes || true

port_in_use() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$1" | grep -q LISTEN
  else
    lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  fi
}

.venv/bin/celery -A config worker --loglevel=info --logfile=logs/celery-worker.log --pidfile=logs/celery-worker.pid &
.venv/bin/celery -A config beat --loglevel=info --logfile=logs/celery-beat.log --pidfile=logs/celery-beat.pid &

if port_in_use "$FLOWER_PORT"; then
  echo "Flower port $FLOWER_PORT is already in use, skipping Flower startup."
else
  .venv/bin/celery -A config flower --address="$FLOWER_ADDRESS" --port="$FLOWER_PORT" --basic_auth="$FLOWER_BASIC_AUTH" --logfile=logs/flower.log --pidfile=logs/flower.pid &
fi

echo "Started Redis, Celery worker, Celery beat, and Flower (auth: $FLOWER_BASIC_AUTH if not already running)."

echo "Run Django with logs to logs/django-console.log"
.venv/bin/python manage.py runserver 0.0.0.0:8000 2>&1 | tee logs/django-console.log
