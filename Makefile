# Local-first targets: none of these need Docker. `up` is for the later
# containerization phase.

.DEFAULT_GOAL := install
VENV := .venv
ifeq ($(OS),Windows_NT)
PY ?= $(VENV)/Scripts/python.exe
PYTHON ?= python
else
PY ?= $(VENV)/bin/python
PYTHON ?= python3
endif

venv:
	$(PYTHON) -m venv $(VENV)

$(PY):
	$(MAKE) venv

install: $(PY)
	$(PY) -m pip install -e '.[dev]'

crawl:
	$(PY) scripts/crawl.py $(ARGS)

ingest:
	$(PY) scripts/seed_ingest.py

index:
	$(PY) scripts/build_indexes.py

extract:
	$(PY) scripts/extract.py $(ARGS)

eval:
	$(PY) scripts/run_eval.py

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn api.main:app --port 8000

fmt:
	$(PY) -m ruff format .

up:
	docker compose up --build

.PHONY: venv install crawl ingest index extract eval test run fmt up
