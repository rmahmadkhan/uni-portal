#!/usr/bin/env sh
set -eu

cd /workspace/app

# Run DB migrations and prepare static assets on startup.
# These are idempotent and safe to run on each release.
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn university_portal.wsgi:application --bind 0.0.0.0:${PORT:-8000}
