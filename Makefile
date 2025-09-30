PYTHON ?= python3
PORT ?= 8000

.PHONY: test lint format build run-mock gateway

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p pytest_cov

lint:
	$(PYTHON) -m pip install ruff black isort || true
	ruff check src tests
	black --check src tests
	isort --check-only src tests

format:
	$(PYTHON) -m pip install black isort || true
	black src tests
	isort src tests

build:
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build

run-mock:
	LITCOACH_MOCK=true uvicorn litcoach.services.gateway.app:app --port $(PORT)

gateway:
	uvicorn litcoach.services.gateway.app:app --port $(PORT)

