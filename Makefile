# Makefile for Tech4Future-Global Management System V13
.PHONY: help install migrate bootstrap dev test check db-build db-up db-down db-logs docker-build docker-up docker-down docker-logs docker-test prod-build prod-up prod-down prod-logs prod-backup prod-check clean

PYTHON ?= .venv/bin/python
UVICORN ?= .venv/bin/uvicorn
PYTEST ?= .venv/bin/pytest

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Set up Python 3.13 venv and install dependencies using uv
	uv venv --python 3.13
	uv pip install -r backend/requirements-dev.txt

migrate: ## Run Django migrations locally (SQLite mode)
	DB_ENGINE=sqlite $(PYTHON) backend/manage.py migrate

bootstrap: ## Seed organizations, positions, and initial admin (SQLite mode)
	DB_ENGINE=sqlite $(PYTHON) backend/manage.py bootstrap_platform

seed-users: ## Seed full suite of user roles and credentials (SQLite mode)
	DB_ENGINE=sqlite $(PYTHON) backend/manage.py seed_all_users

dev: ## Run local development server on http://localhost:8000
	DB_ENGINE=sqlite PYTHONPATH=backend $(UVICORN) t4f_backend.asgi:application --host 0.0.0.0 --port 8000 --reload

test: ## Run unit and integration tests with pytest
	$(PYTEST) backend/tests

check: ## Run Django system checks
	DB_ENGINE=sqlite $(PYTHON) backend/manage.py check

# --- Database in Docker ---
db-build: ## Build the custom PostgreSQL 17 production Docker image
	docker compose build db

db-up: ## Start the PostgreSQL 17 and Redis Docker containers
	docker compose up -d db redis

db-down: ## Stop database container
	docker compose stop db redis

db-logs: ## View database container logs
	docker compose logs -f db

# --- Full Docker Compose Stack ---
docker-build: ## Build all Docker images
	docker compose build

docker-up: ## Start PostgreSQL, Redis, and Web platform with Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker Compose services
	docker compose down

docker-logs: ## Follow Docker Compose logs
	docker compose logs -f

docker-test: ## Run test suite inside Docker web container
	docker compose exec web pytest tests

# --- Production Deployment Targets ---
prod-build: ## Build production stack with Nginx and production settings
	docker compose -f docker-compose.prod.yml build

prod-up: ## Start production stack in background
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production stack
	docker compose -f docker-compose.prod.yml down

prod-logs: ## View production stack logs
	docker compose -f docker-compose.prod.yml logs -f

prod-backup: ## Trigger production database backup
	./scripts/backup_db.sh

prod-check: ## Run Django production deployment checklist check
	DJANGO_SECRET_KEY=prod-check-key-test DJANGO_DEBUG=false $(PYTHON) backend/manage.py check --deploy

clean: ## Remove temporary python cache and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
