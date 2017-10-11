# Makefile for uwsgi, because uwsgi sux

# App-specific config

include Makefile.appconfig

APP_MODULE = "app:create()"
PIDFILE = app.pid
VENV_NAME = venv
UWSGI_LOG = uwsgi.log

# None of your business

BASEDIR = $(shell readlink -f .)
PIDPATH = $(BASEDIR)/$(PIDFILE)
VENV = $(BASEDIR)/$(VENV_NAME)
BIN = $(VENV)/bin/uwsgi

RM = rm -f

.PHONY: start stop ensure-stopped restart assets init-python init-npm

start: ensure-stopped
	$(BIN) \
		--daemonize $(UWSGI_LOG) \
		--pidfile $(PIDFILE) \
		--http-socket $(BIND) \
		--log-x-forwarded-for \
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

static/js/frontend.js: frontend.js
	mkdir -p static/js
	node node_modules/babel-cli/bin/babel.js --presets react -o static/js/frontend.js frontend.js

init-python:
	python3 -m venv $(VENV_NAME)
	$(VENV)/bin/pip install -r requirements.txt

init-npm:
	npm install
