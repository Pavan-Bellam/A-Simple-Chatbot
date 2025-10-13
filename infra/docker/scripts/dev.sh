#!/bin/bash
# Run all containers for development (API + DB)

set -e

# Go to project root to load .env
cd "$(dirname "$0")/../../.."

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Check required environment variables
if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$AWS_REGION" ] || [ -z "$ECR_REPOSITORY" ]; then
    echo "[ERROR] Missing required environment variables in .env file:"
    echo "  AWS_ACCOUNT_ID, AWS_REGION, ECR_REPOSITORY"
    exit 1
fi

echo "[INFO] Starting development environment with ECR base image"

# Run with environment variables
cd infra/docker
docker compose -f docker-compose.yml up
