# Makefile for uwsgi, because uwsgi sux

# App-specific config

include Makefile.appconfig

APP_MODULE = "app:create()"
PIDFILE = app.pid
VENV_NAME = .venv
UWSGI_LOG = uwsgi.log

# None of your business

BASEDIR = $(shell readlink -f .)
PIDPATH = $(BASEDIR)/$(PIDFILE)
VENV = $(BASEDIR)/$(VENV_NAME)
BIN = $(VENV)/bin/uwsgi

RM = rm -f

.PHONY: start stop ensure-stopped restart assets init-python init-npm test

start: ensure-stopped
	$(BIN) \
		--daemonize $(UWSGI_LOG) \
		--pidfile $(PIDFILE) \
		--http-socket $(BIND) \
		--log-x-forwarded-for \
		-H $(VENV) \
		-w $(APP_MODULE)

dev: ensure-stopped
	$(BIN) \
		--http-socket $(BIND) \
		--log-x-forwarded-for \
		--need-app \
		-H $(VENV) \
		-w $(APP_MODULE)

stop:
	$(BIN) --stop $(PIDFILE)
	while [ ! -z "`pgrep -F $(PIDFILE)`" ]; do sleep .1; done

ensure-stopped:
	@if [ -z "`pgrep -F $(PIDFILE)`" ]; then \
		exit 0; \
	else \
		echo "Cowardly refusing to run when another instance is already running."; \
		exit 1; \
	fi

restart: stop start

assets: static/js/frontend.js

static/js/frontend.js: frontend/src/frontend.jsx frontend/package.json frontend/vite.config.js
	mkdir -p static/js
	cd frontend && npm run build

init-python:
	uv sync

init-npm:
	cd frontend && npm install

test:
	uv sync --group dev
	uv run pytest
