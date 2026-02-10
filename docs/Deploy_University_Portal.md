# Deployment (SDLC Step f: Deploy)

This project is a Django app with server-rendered templates (frontend) and a Django backend.
In production it should run behind HTTPS with a Postgres database.

## Prerequisites

- A hosting provider for the web app (Render/Fly.io/Railway/VPS)
- A Postgres database (managed or self-hosted)
- A real domain (optional but recommended)

## Required environment variables

- `DJANGO_SETTINGS_MODULE=university_portal.settings_prod`
- `DJANGO_SECRET_KEY` (long random value)
- `DJANGO_ALLOWED_HOSTS` (comma-separated hosts)

Recommended:
- `DATABASE_URL` (Postgres)
- `DJANGO_SITE_URL=https://your-domain`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain`

## Quick deploy option A: Render (Blueprint)

This repo includes a Render Blueprint at `render.yaml`.

1) Push the repo to GitHub.
2) In Render: **New + → Blueprint** → select your repo.
3) After it provisions, verify:
   - Web service health check passes at `/healthz/`
   - App loads at your Render URL

Important: replace the default `university-portal.onrender.com` hostname in `render.yaml` with the actual service URL Render assigns (or your custom domain), otherwise `ALLOWED_HOSTS` / CSRF may block requests.

## Quick deploy option B: Docker + Postgres (any VPS)

1) Install Docker on the server.
2) Copy `.env.example` to a real `.env` on the server and fill in real values.
3) Run:

```bash
docker compose up -d --build
```

For real production, terminate TLS at a reverse proxy (Nginx/Caddy/Traefik) and remove the docker-compose overrides that disable HTTPS-only settings.

## Post-deploy checklist

- Visit `/healthz/` (should return `ok`)
- Create an admin user:

```bash
# If you can run a one-off command in the same environment
python manage.py createsuperuser
```

- Confirm `SECURE_SSL_REDIRECT`, secure cookies, and HSTS are enabled when serving over HTTPS
- Confirm `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` match your production URL(s)
