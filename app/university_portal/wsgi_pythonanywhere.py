"""WSGI entrypoint tuned for PythonAnywhere.

- Loads optional env file for secrets (default: /home/<user>/.env.uniportal)
- Defaults DJANGO_SETTINGS_MODULE to production settings

This module exists to keep the PythonAnywhere WSGI config file tiny.
"""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application


def _load_env_file(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        return


# Allow overriding the env file path without editing code
env_file = os.environ.get("UNI_PORTAL_ENV_FILE")
if not env_file:
    username = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if username:
        env_file = f"/home/{username}/.env.uniportal"
    else:
        env_file = "/home/.env.uniportal"

_load_env_file(env_file)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "university_portal.settings_prod")

application = get_wsgi_application()
