VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

.PHONY: setup run test type-check lint eval eval-adversarial mcp-server clean

setup:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]" -q

test:
	$(VENV)/bin/pytest tests/ -v

type-check:
	$(VENV)/bin/mypy src/ --ignore-missing-imports

lint:
	$(VENV)/bin/ruff check src/ tests/

run:
	$(PYTHON) -m src.coordinator.agent --demo --dry-run

eval:
	python evals/harness.py

eval-adversarial:
	python evals/harness.py --dataset evals/datasets/adversarial.json

mcp-server:
	python -m src.mcp_server.server

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache dist build *.egg-info
