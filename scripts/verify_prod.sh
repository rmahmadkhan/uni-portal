#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${APP_DIR:-"$ROOT_DIR/app"}"
PYTHON_BIN="${PYTHON:-"$ROOT_DIR/.venv/bin/python"}"

# If PYTHON_BIN is relative (e.g. from Makefile), resolve it from repo root.
if [[ "$PYTHON_BIN" != /* ]]; then
	PYTHON_BIN="$ROOT_DIR/$PYTHON_BIN"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
	PYTHON_BIN="${PYTHON:-python3}"
fi

# Required by settings_prod.py
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-university_portal.settings_prod}"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-dev-verify-not-for-production-change-me-$(printf 'x%.0s' {1..48})}"
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1}"

# Helpful for deploy checks and CSRF; safe defaults for local verification.
export DJANGO_SITE_URL="${DJANGO_SITE_URL:-https://localhost}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${DJANGO_CSRF_TRUSTED_ORIGINS:-https://localhost}"

# Default to a local SQLite DATABASE_URL for verification unless provided.
DEFAULT_DB_URL="sqlite:///${APP_DIR}/db_prod_verify.sqlite3"
export DATABASE_URL="${DATABASE_URL:-$DEFAULT_DB_URL}"

cd "$APP_DIR"

DJANGO_SECURE_SSL_REDIRECT=1 \
DJANGO_SESSION_COOKIE_SECURE=1 \
DJANGO_CSRF_COOKIE_SECURE=1 \
"$PYTHON_BIN" manage.py check --deploy

# The Django test client uses HTTP by default; if SECURE_SSL_REDIRECT is enabled,
# most views will return 301 redirects to HTTPS and tests will fail.
export DJANGO_SECURE_SSL_REDIRECT=0
export DJANGO_SESSION_COOKIE_SECURE=0
export DJANGO_CSRF_COOKIE_SECURE=0

"$PYTHON_BIN" manage.py migrate --noinput
"$PYTHON_BIN" manage.py collectstatic --noinput
"$PYTHON_BIN" manage.py test

echo "verify-prod: OK"