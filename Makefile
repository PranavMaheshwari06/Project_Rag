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

review:
	$(PY) -m uvicorn extraction.review:app --port 8001

eval:
	$(PY) scripts/validate_gold.py
	$(PY) scripts/run_eval.py --apply-threshold

eligibility:
	$(PY) scripts/check_eligibility.py $(ARGS)

eval-eligibility:
	$(PY) scripts/eval_eligibility.py $(ARGS)

validate-phase6-inventory:
	$(PY) scripts/validate_phase6_inventory.py $(ARGS)

check-publish:
	bash scripts/check_publish.sh

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn api.main:app --port 8000

fmt:
	$(PY) -m ruff format .

up:
	docker compose up --build

.PHONY: check-publish venv install crawl ingest index extract review eval eval-eligibility eligibility validate-phase6-inventory test run fmt up
