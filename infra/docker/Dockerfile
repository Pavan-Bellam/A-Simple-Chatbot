# Lightweight Dockerfile for A Simple Chatbot Backend

# Base image with Python 3.12
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Stage for development (with dev dependencies)
FROM base AS development

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies including dev dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Development command with hot reload (source code mounted as volume)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage for production (lightweight)
FROM base AS production

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install only production dependencies
RUN uv sync --frozen --no-dev

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