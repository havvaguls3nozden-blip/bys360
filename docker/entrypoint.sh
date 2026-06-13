#!/usr/bin/env sh
set -eu

export FLASK_APP="${FLASK_APP:-wsgi.py}"
export PORT="${PORT:-8000}"
export BYS360_DEPLOYMENT_MODE="${BYS360_DEPLOYMENT_MODE:-docker}"

if [ "${BYS360_COMPILE_ON_STARTUP:-false}" = "true" ]; then
  python -m compileall -q app config.py wsgi.py
fi

if [ "${BYS360_RUN_MIGRATIONS_ON_STARTUP:-false}" = "true" ]; then
  echo "BYS360: running database migrations..."
  flask db upgrade
fi

exec "$@"
