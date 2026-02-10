"""PythonAnywhere WSGI config for this repo.

Copy/paste this into the PythonAnywhere Web tab → WSGI configuration file.

Repo location (user-provided):
  /home/mahmadkhan/uniportal

This file also supports loading environment variables from:
  /home/mahmadkhan/.env.uniportal

That keeps secrets out of git while avoiding clicking lots of dashboard env vars.
"""

import os
import sys

APP_PATH = "/home/mahmadkhan/uniportal/app"
ENV_FILE = "/home/mahmadkhan/.env.uniportal"


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
        # It's fine if the env file doesn't exist; you can also set env vars in the Web tab.
        return


if APP_PATH not in sys.path:
    sys.path.append(APP_PATH)

_load_env_file(ENV_FILE)

# Ensure production settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "university_portal.settings_prod")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
