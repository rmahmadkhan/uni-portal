# SDLC Step (e) — Improve
University Portal (LUMS-like)

Date: 2026-02-10

## Goal
Harden the application for production deployment by introducing production-grade Django settings driven by environment variables, addressing `manage.py check --deploy` security warnings.

## Changes
### 1) Production settings module
Added a dedicated production settings module:
- `app/university_portal/settings_prod.py`

Key behaviors:
- Enforces `DEBUG=False`
- Requires `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` to be set
- Enables secure defaults (HTTPS redirect, HSTS, secure cookies)
- Sets `STATIC_ROOT` for `collectstatic`

Additional deployment support:
- Supports `DATABASE_URL` for production databases (recommended: Postgres)
- Enables WhiteNoise for static file serving in small deployments

### 2) Environment-driven development settings
Updated the default settings file:
- `app/university_portal/settings.py`

Key behaviors:
- Supports `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`
- Adds safe baseline hardening (`SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`, `SECURE_REFERRER_POLICY`)

### 3) Documentation and configuration template
- Updated `README.md` with production settings usage
- Added `.env.example` with recommended environment variables

Additional docs updates:
- Documented `collectstatic` and `gunicorn` usage

## How to use
Deploy checks (production settings):

```bash
cd app
DJANGO_SETTINGS_MODULE=university_portal.settings_prod python manage.py check --deploy
```

Example Postgres configuration:

```bash
export DATABASE_URL='postgres://portal_user:portal_pass@127.0.0.1:5432/portal_db'
```

Collect static:

```bash
cd app
DJANGO_SETTINGS_MODULE=university_portal.settings_prod python manage.py collectstatic --noinput
```

Serve via gunicorn:

```bash
cd app
DJANGO_SETTINGS_MODULE=university_portal.settings_prod \
	gunicorn university_portal.wsgi:application --bind 0.0.0.0:8000
```

## Notes / Next improvements
- Add a `DATABASE_URL` parser for easy Postgres configuration (would require adding a dependency like `dj-database-url`).
- Add structured logging and error reporting (Sentry) for production.
- Consider adding WhiteNoise if you want the app to serve static files directly (not recommended for large deployments).

Status:
- `DATABASE_URL` support: implemented via `dj-database-url`.
- Static serving via WhiteNoise: implemented in `settings_prod.py`.

## Docker smoke run (Postgres)

Artifacts:
- `Dockerfile`
- `docker-compose.yml`

Run:

```bash
docker compose up --build
```

Purpose:
- Validates migrations and runtime connectivity against a real Postgres instance.
