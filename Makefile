.PHONY: install run test lint docker-up docker-down clean

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev]"

run:
	cp -n .env.example .env 2>/dev/null || true
	alembic upgrade head
	sanic src.main:create_app --host=0.0.0.0 --port=8000 --dev

test:
	pytest -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/

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
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
