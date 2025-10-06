# Makefile for A Simple Chatbot
# Convenience commands for Docker operations

.PHONY: help build build-base push-base dev test ci clean format lint lint-check fix

# Detect OS and set script extension
ifeq ($(OS),Windows_NT)
    SCRIPT_EXT := .bat
    SCRIPTS := infra\docker\scripts
else
    SCRIPT_EXT := .sh
    SCRIPTS := ./infra/docker/scripts
endif

# Default target
help: ## Show this help message
	@echo "A Simple Chatbot - Docker Management"
	@echo ""
	@echo "Available commands:"
	@echo "  build          Build the backend application"
	@echo "  build-base     Build base image with all dependencies"
	@echo "  push-base      Build and push base image to Docker Hub"
	@echo "  dev            Run development environment (API + DB)"
	@echo "  test           Run tests in CI environment"
	@echo "  ci             Run full CI pipeline (lint + format + tests)"
	@echo "  clean          Clean up Docker resources"
	@echo "  format         Format code with black and isort"
	@echo "  lint           Run flake8 linter"
	@echo "  lint-check     Check formatting and linting without changes"
	@echo "  fix            Auto-fix code formatting"

# Build commands
build: ## Build the backend application
	$(SCRIPTS)/build$(SCRIPT_EXT)

build-base: ## Build base image with all dependencies
	$(SCRIPTS)/build-base$(SCRIPT_EXT)

push-base: ## Build and push base image to Docker Hub
	$(SCRIPTS)/build-base$(SCRIPT_EXT) --push

# Development
dev: ## Run development environment (API + DB)
	$(SCRIPTS)/dev$(SCRIPT_EXT)

# Testing
test: ## Run tests in CI environment
	$(SCRIPTS)/test$(SCRIPT_EXT)

ci: ## Run full CI pipeline (lint + format check + tests)
	$(SCRIPTS)/ci$(SCRIPT_EXT)

# Cleanup
clean: ## Clean up Docker resources
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up all Docker resources (including images)
	docker system prune -af
	docker volume prune -f

# Code quality (runs inside Docker)
format: ## Format code with black and isort
	@echo "Formatting code in Docker..."
	cd infra/docker && docker compose -f docker-compose.yml run --rm api uv run black app tests
	cd infra/docker && docker compose -f docker-compose.yml run --rm api uv run isort app tests

lint: ## Run linters (flake8)
	@echo "Running linters in Docker..."
	cd infra/docker && docker compose -f docker-compose.yml run --rm api uv run flake8 app tests

lint-check: ## Check code formatting and linting without modifying
	@echo "Checking code formatting in Docker..."
	cd infra/docker && docker compose -f docker-compose.yml run --rm api uv run black --check app tests
	cd infra/docker && docker compose -f docker-compose.yml run --rm api uv run isort --check-only app tests
	cd infra/docker && docker compose -f docker-compose.yml run --rm api uv run flake8 app tests

fix: ## Auto-fix code formatting and imports
	@echo "Auto-fixing code in Docker..."
	$(MAKE) format
	@echo "Code formatted successfully!"
