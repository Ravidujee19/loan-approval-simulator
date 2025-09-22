PY=python
PIP=pip

.PHONY: dev start migrate seed lint typecheck test coverage docker:up docker:down docker:test sbom scan fmt

dev:
	uvicorn agents.applicant_evaluator.app.main:app --reload --port 8000

start:
	$(PY) -m uvicorn agents.applicant_evaluator.app.main:app --host 0.0.0.0 --port 8000

migrate:
	alembic -c agents/applicant_evaluator/app/db/alembic.ini upgrade head

seed:
	$(PY) agents/applicant_evaluator/app/seed_data.py

lint:
	flake8 agents/applicant_evaluator/app
	black --check agents/applicant_evaluator/app
	isort --check-only agents/applicant_evaluator/app

fmt:
	black agents/applicant_evaluator/app
	isort agents/applicant_evaluator/app

typecheck:
	mypy agents/applicant_evaluator/app

test:
	pytest -q --maxfail=1

coverage:
	pytest --cov=agents.applicant_evaluator.app --cov-report=term-missing

docker:up:
	docker compose up --build

docker:down:
	docker compose down -v

docker:test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api

sbom:
	syft packages dir:.

scan:
	trivy fs --exit-code 0 --severity HIGH,CRITICAL .
