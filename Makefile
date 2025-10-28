PY=python3
VENV_DIR=venv
USE_VENV=source $(VENV_DIR)/bin/activate
SHELL := /bin/bash

.phony: setup
setup:
	mkdir out/
	$(PY) -m venv $(VENV_DIR)
	$(USE_VENV) && pip install -r requirements.txt

.phony: requirements.txt
requirements.txt:
	$(USE_VENV) && pip freeze > requirements.txt