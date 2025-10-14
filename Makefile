# Makefile for A Simple Chatbot
# Convenience commands for Docker operations

.PHONY: help build build-base push-base dev test ci clean format lint lint-check fix

# Cross-platform configuration
# Make always uses forward slashes for paths, even on Windows
SCRIPTS := infra/docker/scripts

# Detect Windows and configure appropriately
ifeq ($(OS),Windows_NT)
    SCRIPT_EXT := .bat
    # Use cmd.exe for .bat files and convert forward slashes to backslashes
    SHELL := cmd.exe
    .SHELLFLAGS := /c
    # Convert forward slashes to backslashes for Windows
    SCRIPTS_WIN := $(subst /,\,$(SCRIPTS))
    RUN_SCRIPT = $(SCRIPTS_WIN)\$(1)$(SCRIPT_EXT)
else
    SCRIPT_EXT := .sh
    SHELL := /bin/bash
    .SHELLFLAGS := -c
    RUN_SCRIPT = ./$(SCRIPTS)/$(1)$(SCRIPT_EXT)
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
	$(call RUN_SCRIPT,build)

build-base: ## Build base image with all dependencies (run this when pyproject.toml or uv.lock changes)
	$(call RUN_SCRIPT,build-base)

push-base: ## Build and push base image to Docker Hub
	$(call RUN_SCRIPT,build-base) --push

# Development
dev: ## Run development environment (API + DB)
	$(call RUN_SCRIPT,dev)

# Testing
test: ## Run tests in CI environment
	$(call RUN_SCRIPT,test)

ci: ## Run full CI pipeline (lint + format check + tests)
	$(call RUN_SCRIPT,ci)

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
