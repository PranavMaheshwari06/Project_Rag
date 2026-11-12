# Local-first targets: none of these need Docker. `up` is for the later
# containerization phase.

.DEFAULT_GOAL := install
VENV := .venv
ifeq ($(OS),Windows_NT)
PY ?= $(VENV)/Scripts/python.exe
else
PY ?= $(VENV)/bin/python
endif

venv:
	uv venv $(VENV) --python 3.12

$(PY):
	$(MAKE) venv

install: $(PY)
	uv pip sync --python $(PY) --torch-backend cpu requirements.lock
	uv pip install --python $(PY) --no-deps -e .

crawl:
	$(PY) scripts/crawl.py $(ARGS)

ingest:
	$(PY) scripts/ingest.py

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

parse-profile:
	$(PY) scripts/parse_profile.py $(ARGS)

compare-agent:
	$(PY) scripts/compare_agent.py $(ARGS)

ablation:
	$(PY) scripts/run_ablation.py

eval-eligibility:
	$(PY) scripts/eval_eligibility.py $(ARGS)

validate-rule-inventory:
	$(PY) scripts/validate_rule_inventory.py $(ARGS)

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn api.main:app --port 8000

fmt:
	$(PY) -m ruff format .

up:
	docker compose up --build

.PHONY: venv install crawl ingest index extract review eval ablation compare-agent eval-eligibility eligibility parse-profile validate-rule-inventory test run fmt up
