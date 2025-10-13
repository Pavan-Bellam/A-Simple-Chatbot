#!/bin/bash
# Build the backend application Docker image

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

echo "[INFO] Building with ECR base image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG:-latest}"

# Build with environment variables
cd infra/docker
docker compose -f docker-compose.yml build api
