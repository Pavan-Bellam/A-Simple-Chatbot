# Makefile for A Simple Chatbot
# Convenience commands for Docker operations

.PHONY: help dev prod ci test build clean logs stop restart

# Default target
help: ## Show this help message
	@echo "A Simple Chatbot - Docker Management"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
dev: ## Start development environment with hot reload
	@echo "Starting development environment..."
	./docker/scripts/start.sh --env dev

dev-build: ## Build and start development environment
	@echo "Building and starting development environment..."
	./docker/scripts/start.sh --env dev --build

dev-detach: ## Start development environment in background
	@echo "Starting development environment in detached mode..."
	./docker/scripts/start.sh --env dev --detach

# Testing commands
test: ## Run tests in CI environment
	@echo "Running tests..."
	./docker/scripts/start.sh --test

ci: ## Start CI environment
	@echo "Starting CI environment..."
	./docker/scripts/start.sh --env ci

# Production commands
prod-build: ## Build production image for ECS
	@echo "Building production image..."
	./docker/scripts/build.sh --env prod

prod-push: ## Build and push production image to registry
	@echo "Building and pushing production image..."
	./docker/scripts/build.sh --env prod --push

# Management commands
logs: ## Show logs for all services
	@echo "Showing logs..."
	./docker/scripts/start.sh --logs

logs-api: ## Show API service logs
	@echo "Showing API logs..."
	./docker/scripts/start.sh --logs api

logs-db: ## Show database logs
	@echo "Showing database logs..."
	./docker/scripts/start.sh --logs db

stop: ## Stop all services
	@echo "Stopping all services..."
	./docker/scripts/start.sh --stop

restart-api: ## Restart API service
	@echo "Restarting API service..."
	./docker/scripts/start.sh --restart api

restart-db: ## Restart database service
	@echo "Restarting database service..."
	./docker/scripts/start.sh --restart db

# Cleanup commands
clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up all Docker resources (including images)
	@echo "Cleaning up all Docker resources..."
	docker system prune -af
	docker volume prune -f

# Setup commands
setup: ## Initial setup - copy environment file
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		cp docker/.env.example .env; \
		echo "Created .env file from template. Please edit it with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi

# Health check
health: ## Check health of running services
	@echo "Checking service health..."
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Testing API health endpoint..."
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✅ API is healthy" || echo "❌ API is not responding"