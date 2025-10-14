#!/bin/bash
# Build and optionally push the base image with all dependencies to AWS ECR

set -e

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

# Construct ECR image name
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPOSITORY}"
TAG="${IMAGE_TAG:-latest}"
PUSH=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--push]"
            exit 1
            ;;
    esac
done

echo "[INFO] Building base image: $IMAGE_NAME:$TAG"

# Go to project root
cd "$(dirname "$0")/../../.."

# Build base image
docker build -f infra/docker/Dockerfile.base -t "$IMAGE_NAME:$TAG" .

echo "[INFO] Base image built successfully: $IMAGE_NAME:$TAG"

# Push to ECR if requested
if [[ "$PUSH" == true ]]; then
    echo "[INFO] Logging into ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to authenticate with ECR"
        exit 1
    fi

    echo "[INFO] Pushing to ECR..."
    docker push "$IMAGE_NAME:$TAG"

    echo "[INFO] Base image pushed to ECR: $IMAGE_NAME:$TAG"
else
    echo "[INFO] To push to ECR, run: $0 --push"
    echo "[INFO] Make sure AWS CLI is configured with proper credentials"
fi
