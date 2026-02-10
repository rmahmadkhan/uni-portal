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

## Quick deploy option C: PythonAnywhere (public link, easiest)

PythonAnywhere is a hosted WSGI platform that can run Django apps with a public URL like:
`https://<your-username>.pythonanywhere.com/`

This project is already set up to run with SQLite for development; on PythonAnywhere (especially on free tiers), SQLite is the simplest approach.

### 1) Create the web app

In PythonAnywhere:

1) **Web** → **Add a new web app**
2) Choose **Manual configuration**
3) Pick a Python version that’s compatible with your account (3.10+ recommended)

### 2) Get the code onto PythonAnywhere

Open a PythonAnywhere **Bash console** and run:

```bash
cd ~
git clone <YOUR_GITHUB_REPO_URL> uniportal
cd /home/mahmadkhan/uniportal
```

If your repo name differs, adjust the folder name accordingly.

### 3) Create a virtualenv + install dependencies

```bash
cd ~
python -m venv ~/.virtualenvs/portal
source ~/.virtualenvs/portal/bin/activate
cd /home/mahmadkhan/uniportal
pip install -r requirements.txt
```

Alternative (one command):

```bash
cd /home/mahmadkhan/uniportal
bash scripts/pythonanywhere_bootstrap.sh
```

### 4) Configure environment variables (important)

In PythonAnywhere: **Web** → your app → **Environment variables**, set:

- `DJANGO_SETTINGS_MODULE` = `university_portal.settings_prod`
- `DJANGO_SECRET_KEY` = (a long random string)
- `DJANGO_ALLOWED_HOSTS` = `<your-username>.pythonanywhere.com`
- `DJANGO_SITE_URL` = `https://<your-username>.pythonanywhere.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://<your-username>.pythonanywhere.com`

Optional (recommended on PythonAnywhere):
- `DJANGO_SECURE_PROXY_SSL_HEADER` = `1`

Do **not** set `DATABASE_URL` unless you have a paid database option; if omitted, the app uses SQLite by default.

Optional shortcut (fewer dashboard clicks):

- Copy `.env.uniportal.example` to `/home/mahmadkhan/.env.uniportal` and fill the real `DJANGO_SECRET_KEY`.
- Then use the provided WSGI snippet file `pythonanywhere_wsgi.py` (it auto-loads `/home/mahmadkhan/.env.uniportal`).

### 5) Configure the WSGI file

In PythonAnywhere: **Web** → your app → **WSGI configuration file**.

Set it up so it:

1) Adds your repo’s `app/` directory to `sys.path`
2) Sets `DJANGO_SETTINGS_MODULE` to production settings
3) Imports Django’s WSGI application

Minimal option (recommended): import the repo-provided WSGI entrypoint.

Copy/paste this (filled in for your details):

```python
import sys

path = '/home/mahmadkhan/uniportal/app'
if path not in sys.path:
   sys.path.append(path)

from university_portal.wsgi_pythonanywhere import application
```

Full option (also OK): paste the longer WSGI snippet from `pythonanywhere_wsgi.py`.

```python
import os
import sys

path = '/home/mahmadkhan/uniportal/app'
if path not in sys.path:
   sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_portal.settings_prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 6) Run migrations + collectstatic

In a Bash console:

```bash
source ~/.virtualenvs/portal/bin/activate
cd /home/mahmadkhan/uniportal/app
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

### 7) Configure static files mapping (PythonAnywhere UI)

In PythonAnywhere: **Web** → your app → **Static files**:

- URL: `/static/`
- Directory: `/home/mahmadkhan/uniportal/app/staticfiles`

### 8) Create an admin user (and optional demo data)

```bash
source ~/.virtualenvs/portal/bin/activate
cd /home/mahmadkhan/uniportal/app
python manage.py createsuperuser

# Optional demo users/data
python manage.py seed_demo
```

### 9) Reload the web app

In PythonAnywhere: **Web** → click **Reload**.

If you see a 400 error:
- Re-check `DJANGO_ALLOWED_HOSTS`

If you see a CSRF failure:
- Re-check `DJANGO_CSRF_TRUSTED_ORIGINS` includes your exact https URL

If you see a 500:
- Check the PythonAnywhere error log from the **Web** tab.

## Post-deploy checklist

- Visit `/healthz/` (should return `ok`)
- Create an admin user:

```bash
# If you can run a one-off command in the same environment
python manage.py createsuperuser
```

- Confirm `SECURE_SSL_REDIRECT`, secure cookies, and HSTS are enabled when serving over HTTPS
- Confirm `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` match your production URL(s)
