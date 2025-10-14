# Lightweight Dockerfile for A Simple Chatbot Backend
# Uses pre-built base image with all dependencies

# Use custom base image with all dependencies pre-installed from ECR
# Build base: make build-base
# Push to ECR: make push-base
ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS base

# Stage for development
FROM base AS development

# Copy source code and tests
COPY ./app ./app
COPY ./tests ./tests
COPY ./.flake8 ./.flake8

# Expose port
EXPOSE 8000

# Development command with hot reload (can be overridden by docker-compose volumes)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage for production
FROM base AS production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && chown -R app:app /app

# Copy source code
COPY --chown=app:app ./app ./app

# Switch to non-root user
USER app

# Health check for ECS/container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command optimized for ECS
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]