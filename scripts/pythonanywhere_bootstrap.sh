#!/usr/bin/env bash
set -euo pipefail

# PythonAnywhere bootstrap for this repo.
# Assumes repo is cloned at: /home/mahmadkhan/uniportal
#
# Usage (on PythonAnywhere Bash console):
#   bash scripts/pythonanywhere_bootstrap.sh

REPO_DIR="/home/mahmadkhan/uniportal"
VENV_DIR="/home/mahmadkhan/.virtualenvs/portal"
APP_DIR="$REPO_DIR/app"

if [[ ! -d "$REPO_DIR" ]]; then
  echo "ERROR: Repo directory not found: $REPO_DIR" >&2
  exit 1
fi

cd "$REPO_DIR"

# Create virtualenv if missing
if [[ ! -d "$VENV_DIR" ]]; then
  python -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
pip install -r requirements.txt

cd "$APP_DIR"

# Migrate and collect static assets
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo ""
echo "Bootstrap complete. Next:" 
echo "1) Set env vars in PythonAnywhere Web tab (or use pythonanywhere_wsgi.py to load them)."
echo "2) Update the PythonAnywhere WSGI configuration file (see pythonanywhere_wsgi.py)."
echo "3) Reload your web app from the Web tab."
