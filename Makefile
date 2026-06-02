VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
ALEMBIC = $(VENV)/bin/alembic
SANIC = $(VENV)/bin/sanic
RUFF = $(VENV)/bin/ruff
PYTEST = $(VENV)/bin/pytest

.PHONY: install run test lint format docker-up docker-down docker-logs clean

$(VENV)/bin/python:
	python3 -m venv $(VENV)

install: $(VENV)/bin/python
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"

run: install
	cp -n .env.example .env 2>/dev/null || true
	$(ALEMBIC) upgrade head
	$(SANIC) src.main:create_app --factory --host=0.0.0.0 --port=8000 --dev

test: install
	$(PYTEST) -v --cov=src --cov-report=term-missing

lint: install
	$(RUFF) check src/ tests/
	$(RUFF) format --check src/ tests/

format: install
	$(RUFF) format src/ tests/

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
