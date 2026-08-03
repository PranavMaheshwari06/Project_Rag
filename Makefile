# Local-first targets: none of these need Docker. `up` is for the later
# containerization phase.

PY ?= python

install:
	$(PY) -m pip install -e .[dev]

ingest:
	$(PY) scripts/seed_ingest.py

index:
	$(PY) scripts/build_indexes.py

eval:
	$(PY) scripts/run_eval.py

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn api.main:app --port 8000

fmt:
	$(PY) -m ruff format . 2>/dev/null || echo "ruff not installed; skipping"

up:
	docker compose up --build

.PHONY: install ingest index eval test run fmt up
