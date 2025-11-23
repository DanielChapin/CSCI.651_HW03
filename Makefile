PY=python3
VENV_DIR=venv
USE_VENV=source $(VENV_DIR)/bin/activate
SOURCE=$(wildcard src/*.py) $(wildcard src/demos/*.py)
SHELL := /bin/bash

.PHONY: all
all: out/daniel_chapin_hw3.zip

out/daniel_chapin_hw3.zip: Makefile README.md demo.sh out/report.pdf $(SOURCE) requirements.txt out/revisions.txt out/docs.pdf
	zip $@ $^

out/docs.pdf: $(SOURCE) Doxyfile
	doxygen && cd out/docs/latex ; make && cp refman.pdf ../../docs.pdf

.PHONY: setup
setup:
	mkdir out/
	$(PY) -m venv $(VENV_DIR)
	$(USE_VENV) && pip install -r requirements.txt

.PHONY: requirements.txt
requirements.txt:
	$(USE_VENV) && pip freeze > requirements.txt

.PHONY: out/revisions.txt
out/revisions.txt:
	git log > out/revisions.txt

out/report.pdf: report/report.typ
	typst compile report/report.typ out/report.pdf