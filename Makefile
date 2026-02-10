.PHONY: venv deps migrate seed run test verify-prod

VENV_DIR ?= .venv
PY := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
APP_DIR := app
HOST ?= 127.0.0.1
PORT ?= 8000

venv:
	@test -x "$(PY)" || python3 -m venv "$(VENV_DIR)"

deps: venv
	"$(PY)" -m pip install -r requirements.txt

migrate: deps
	cd "$(APP_DIR)" && "../$(PY)" manage.py migrate

seed: deps
	cd "$(APP_DIR)" && "../$(PY)" manage.py seed_demo

run: migrate seed
	cd "$(APP_DIR)" && "../$(PY)" manage.py runserver "$(HOST):$(PORT)"

test: deps
	cd "$(APP_DIR)" && "../$(PY)" manage.py test

verify-prod: deps
	PYTHON="$(PY)" ./scripts/verify_prod.sh
