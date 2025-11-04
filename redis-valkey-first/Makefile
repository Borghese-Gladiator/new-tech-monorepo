# ---- Config ----
UV ?= uv
APP ?= cache_service:app
PORT ?= 8000
HOST ?= 0.0.0.0

# Default to fake Valkey for local runs unless overridden in the shell
export VALKEY_FAKE ?= 1

# ---- Phonies ----
.PHONY: help init sync clean serve client test cov lock update format lint check

help:
	@echo "Targets:"
	@echo "  init     - Initialize uv project (idempotent) and add deps"
	@echo "  sync     - Sync deps from pyproject.lock (create venv if needed)"
	@echo "  serve    - Run FastAPI dev server with reload"
	@echo "  client   - Run the example client"
	@echo "  test     - Run pytest"
	@echo "  cov      - Run pytest with coverage"
	@echo "  lock     - Re-resolve & lock dependencies (pin versions)"
	@echo "  update   - Update all dependencies to latest compatible"
	@echo "  format   - (Optional) Format code with ruff/black if installed"
	@echo "  lint     - (Optional) Lint with ruff if installed"
	@echo "  clean    - Remove virtual env cache and build artifacts"

init:
	# Safe to run multiple times; adds deps if missing
	$(UV) init --no-readme --package || true
	# Runtime deps
	$(UV) add fastapi uvicorn pydantic valkey httpx
	# Dev/test deps
	$(UV) add --dev pytest fakeredis coverage
	@echo "Project initialized."

sync:
	$(UV) sync

serve:
	$(UV) run uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

client:
	$(UV) run python client_example.py

test:
	$(UV) run pytest -q

cov:
	$(UV) run coverage run -m pytest -q
	$(UV) run coverage report -m
	@echo "Tip: generate HTML with: uv run coverage html && open htmlcov/index.html"

lock:
	# Re-solve and create/update lockfile
	$(UV) lock

update:
	# Update to latest compatible versions (re-lock)
	$(UV) pip compile --upgrade || true
	$(UV) lock --upgrade

format:
	-$(UV) run ruff format .
	-$(UV) run black . 2>/dev/null || true

lint:
	-$(UV) run ruff check .

clean:
	rm -rf .venv .pytest_cache .mypy_cache htmlcov dist build
	find . -name "__pycache__" -type d -exec rm -rf {} +
