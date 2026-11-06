# Makefile for Tech4Future-Global Management System V13
.PHONY: help install migrate bootstrap seed-users dev test check db-build db-up db-down db-logs docker-build docker-up docker-down docker-logs docker-test prod-build prod-up prod-down prod-logs prod-migrate prod-seed prod-collectstatic prod-restart prod-backup prod-check clean

PYTHON ?= .venv/bin/python
UVICORN ?= .venv/bin/uvicorn
PYTEST ?= .venv/bin/pytest
PORT ?= 8080
DB_ENGINE ?= postgresql

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Set up Python 3.13 venv and install dependencies using uv
	uv venv --python 3.13
	uv pip install -r backend/requirements-dev.txt

migrate: ## Run Django database migrations (PostgreSQL default)
	DB_ENGINE=$(DB_ENGINE) $(PYTHON) backend/manage.py migrate

bootstrap: ## Seed organizations, positions, and initial admin
	DB_ENGINE=$(DB_ENGINE) $(PYTHON) backend/manage.py bootstrap_platform

seed-users: ## Seed full suite of user roles and credentials
	DB_ENGINE=$(DB_ENGINE) $(PYTHON) backend/manage.py seed_all_users

dev: ## Run local development server with PostgreSQL on http://localhost:$(PORT)
	DB_ENGINE=$(DB_ENGINE) PYTHONPATH=backend $(UVICORN) t4f_backend.asgi:application --host 0.0.0.0 --port $(PORT) --reload

test: ## Run unit and integration tests with pytest
	$(PYTEST) backend/tests

check: ## Run Django system checks
	DB_ENGINE=$(DB_ENGINE) $(PYTHON) backend/manage.py check

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

# --- Production Deployment Targets (portal.t4f-global.org) ---
prod-build: ## Build production stack with Nginx and production settings
	docker compose -f docker-compose.prod.yml build

prod-up: ## Start production stack in background (Port 8080)
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production stack
	docker compose -f docker-compose.prod.yml down

prod-logs: ## View production stack logs
	docker compose -f docker-compose.prod.yml logs -f

prod-migrate: ## Run database migrations in production container
	docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

prod-seed: ## Seed all user roles in production container
	docker compose -f docker-compose.prod.yml exec -T web python manage.py seed_all_users

prod-superuser: ## Create an interactive superuser in production container
	docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

prod-collectstatic: ## Collect static files in production container
	docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

prod-restart: ## Restart production web and nginx services
	docker compose -f docker-compose.prod.yml restart web nginx

prod-backup: ## Trigger production database backup
	./scripts/backup_db.sh

prod-check: ## Run Django production deployment checklist check
	DJANGO_SECRET_KEY=prod-check-key-test DJANGO_DEBUG=false $(PYTHON) backend/manage.py check --deploy

clean: ## Remove temporary python cache and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
