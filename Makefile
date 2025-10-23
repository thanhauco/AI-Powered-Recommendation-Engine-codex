PYTHON=python3
POETRY=poetry
UVICORN=uvicorn

export PYTHONPATH=$(PWD)

.PHONY: dev seed train evaluate lint fmt test up down alembic-upgrade alembic-revision worker

dev:
	$(UVICORN) app.main:app --reload --factory --port 8000

seed:
	$(PYTHON) scripts/seed.py

train:
	$(PYTHON) ml/train.py

evaluate:
	$(PYTHON) ml/evaluate.py

lint:
	ruff check .

fmt:
	black .

mypy:
	mypy app ml scripts

test:
	pytest

up:
	docker compose up --build

down:
	docker compose down

alembic-upgrade:
	alembic upgrade head

alembic-revision:
	alembic revision --autogenerate -m "minor update"

worker:
	celery -A app.tasks.celery_app worker --loglevel=info
