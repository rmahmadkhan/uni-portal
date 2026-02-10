"""Production settings for the University Portal.

Usage:
  DJANGO_SETTINGS_MODULE=university_portal.settings_prod

This module intentionally enforces environment-provided secrets and secure defaults.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import dj_database_url

from .settings import *  # noqa: F403


def _env_bool(name: str, default: bool = False) -> bool:
	val = os.environ.get(name)
	if val is None:
		return default
	return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str) -> list[str]:
	val = (os.environ.get(name) or "").strip()
	if not val:
		return []
	return [item.strip() for item in val.split(",") if item.strip()]


# --- Required secrets / core toggles ---
DEBUG = False  # noqa: F405

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()  # noqa: F405
if not SECRET_KEY:
	raise RuntimeError("DJANGO_SECRET_KEY is required in production")


# --- Hosts / origins ---
ALLOWED_HOSTS = _env_csv("DJANGO_ALLOWED_HOSTS")  # noqa: F405
if not ALLOWED_HOSTS:
	raise RuntimeError("DJANGO_ALLOWED_HOSTS is required in production")

CSRF_TRUSTED_ORIGINS = _env_csv("DJANGO_CSRF_TRUSTED_ORIGINS")  # noqa: F405

# If you provide SITE_URL, we can infer a trusted origin.
site_url = (os.environ.get("DJANGO_SITE_URL") or "").strip()
if site_url:
	parsed = urlparse(site_url)
	origin = f"{parsed.scheme}://{parsed.netloc}"
	if origin and origin not in CSRF_TRUSTED_ORIGINS:
		CSRF_TRUSTED_ORIGINS.append(origin)


# --- HTTPS / cookies ---
SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", True)  # noqa: F405
SESSION_COOKIE_SECURE = _env_bool("DJANGO_SESSION_COOKIE_SECURE", True)  # noqa: F405
CSRF_COOKIE_SECURE = _env_bool("DJANGO_CSRF_COOKIE_SECURE", True)  # noqa: F405

# If behind a reverse proxy (common), set:
#   DJANGO_SECURE_PROXY_SSL_HEADER=1
# and ensure it forwards X-Forwarded-Proto: https
if _env_bool("DJANGO_SECURE_PROXY_SSL_HEADER", True):
	SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # noqa: F405


# --- HSTS ---
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True)  # noqa: F405
SECURE_HSTS_PRELOAD = _env_bool("DJANGO_SECURE_HSTS_PRELOAD", True)  # noqa: F405


# --- Misc hardening ---
SECURE_CONTENT_TYPE_NOSNIFF = True  # noqa: F405
X_FRAME_OPTIONS = os.environ.get("DJANGO_X_FRAME_OPTIONS", "DENY")  # noqa: F405
SECURE_REFERRER_POLICY = os.environ.get("DJANGO_SECURE_REFERRER_POLICY", "same-origin")  # noqa: F405


# --- Static files ---
# For real production, serve static files via CDN/reverse-proxy.
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

# Simple static serving for small deployments (reverse proxy still recommended).
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {  # noqa: F405
	"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
	"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}


# --- Admin security (optional but recommended) ---
# If you want to force admin login over HTTPS even when other pages don't:
# SECURE_SSL_REDIRECT = True


# --- Database (optional override) ---
# This demo uses SQLite by default.
# Provide DATABASE_URL for production deployments.
database_url = (os.environ.get("DATABASE_URL") or "").strip()
if database_url:
	db_ssl_require = _env_bool("DJANGO_DB_SSL_REQUIRE", True)
	scheme = urlparse(database_url).scheme.lower()
	ssl_require = db_ssl_require if scheme in {"postgres", "postgresql", "postgis"} else False
	db_config = dj_database_url.parse(database_url, conn_max_age=60, ssl_require=ssl_require)
	# Postgres-specific tuning (avoid passing unsupported params to other engines like SQLite).
	if scheme in {"postgres", "postgresql", "postgis"}:
		db_config.setdefault("OPTIONS", {})
		db_config["OPTIONS"].setdefault("connect_timeout", 5)
		db_config["ATOMIC_REQUESTS"] = True
	DATABASES = {"default": db_config}  # noqa: F405
