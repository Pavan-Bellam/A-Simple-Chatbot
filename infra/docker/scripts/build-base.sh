#!/bin/bash
# Build and optionally push the base image with all dependencies

set -e

IMAGE_NAME="hero7hero/simple-chatbot"
TAG="latest"
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

# Push to registry if requested
if [[ "$PUSH" == true ]]; then
    echo "[INFO] Pushing to registry..."
    docker push "$IMAGE_NAME:$TAG"

    echo "[INFO] Base image pushed: $IMAGE_NAME:$TAG"
else
    echo "[INFO] To push to Docker Hub, run: $0 --push"
    echo "[INFO] Make sure you're logged in: docker login"
fi
