# University Portal (Django demo)

## Run (macOS/Linux)

From the repo root:

### One command

```bash
# Option A: Make
make run

# Option B: Shell script
chmod +x run.sh
./run.sh
```

### Manual

```bash
# 1) Create/activate the virtualenv (if you already have .venv, just activate it)
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the app
cd app
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Open: http://127.0.0.1:8000/

Demo logins (after `seed_demo`): `student1`, `faculty1`, `registrar1`, `finance1`, `alumni1`, `admin1` with password `password123`.

Note: `/admin/` is Django Admin. A user needs `is_staff=True` and permissions (or be a superuser) to access it. In the demo seed, `admin1` is made a superuser for convenience.

## Create new users

### Option A: Django admin (recommended)

```bash
cd app
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Then open `http://127.0.0.1:8000/admin/` → Users → Add.

To assign portal roles, add the user to Groups like `Student`, `Faculty`, `Registrar Staff`, `Finance Staff`, `IT/Admin`, `Alumni`.

### Option B: Management command (fast)

From the repo root:

```bash
make migrate
cd app
python manage.py create_portal_user newstudent --roles STUDENT --password password123
python manage.py create_portal_user newfaculty --roles FACULTY --password password123
python manage.py create_portal_user newregistrar --roles REGISTRAR --staff --password password123
```

If you omit `--password`, it will prompt securely.

## Troubleshooting

- `ModuleNotFoundError: No module named 'django'`
  - You ran `python manage.py ...` without activating `.venv`.
  - Fix: `source .venv/bin/activate` and retry, or run with `.venv/bin/python`.

## Production settings (SDLC Step e: Improve)

This repo includes a production settings module at `app/university_portal/settings_prod.py`.

Run deploy checks with production settings:

```bash
cd app
DJANGO_SETTINGS_MODULE=university_portal.settings_prod python manage.py check --deploy
```

Typical production environment variables (see `.env.example`):

- `DJANGO_SETTINGS_MODULE=university_portal.settings_prod`
- `DJANGO_SECRET_KEY=...` (required)
- `DJANGO_ALLOWED_HOSTS=example.com,www.example.com` (required)
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com`
- `DJANGO_SITE_URL=https://example.com` (optional)

Notes:
- `settings_prod.py` enables HTTPS redirects, HSTS, and secure cookies by default.
- Static files in production should be served by a reverse proxy or CDN; `STATIC_ROOT` is set for `collectstatic`.

### One-command production verification

From the repo root:

```bash
make verify-prod
```

This runs `check --deploy`, `migrate`, `collectstatic`, and the test suite using production settings with safe local-default env vars (override any env var as needed, including `DATABASE_URL`).

### Database (Postgres) via `DATABASE_URL`

Production settings support `DATABASE_URL` (recommended: Postgres). Example:

```bash
export DATABASE_URL='postgres://portal_user:portal_pass@127.0.0.1:5432/portal_db'
```

### Static files

```bash
cd app
DJANGO_SETTINGS_MODULE=university_portal.settings_prod python manage.py collectstatic --noinput
```

`settings_prod.py` includes WhiteNoise for simple deployments.

### App server (gunicorn)

```bash
cd app
DJANGO_SETTINGS_MODULE=university_portal.settings_prod \
  gunicorn university_portal.wsgi:application --bind 0.0.0.0:8000
```

## Docker + Postgres smoke run

If you have Docker Desktop installed, you can run the portal against a real Postgres database (recommended verification for production settings).

```bash
docker compose up --build
```

This uses:
- `docker-compose.yml` (Postgres + web)
- `Dockerfile`

Open: http://127.0.0.1:8000/

Note: the compose file disables HTTPS-only settings (redirect/HSTS/secure cookies) for local HTTP smoke runs. For real deployments, remove those overrides.

## Deploy (SDLC Step f)

See docs/Deploy_University_Portal.md for production deployment steps.

If you want a managed-host deploy, this repo also includes a Render Blueprint: `render.yaml`.

