#!/bin/bash
# Build script for A Simple Chatbot Docker images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="chatbot"
REGISTRY="${REGISTRY:-localhost:5000}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV          Environment (dev|prod) [default: dev]"
    echo "  -t, --tag TAG          Image tag [default: latest]"
    echo "  -p, --push             Push image to registry"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --env dev           Build development image"
    echo "  $0 --env prod --push   Build and push production image"
}

# Parse command line arguments
ENV="dev"
TAG="latest"
PUSH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    log_error "Invalid environment: $ENV. Must be 'dev' or 'prod'"
    exit 1
fi

# Set target based on environment
if [[ "$ENV" == "dev" ]]; then
    TARGET="development"
    FULL_TAG="${IMAGE_NAME}:${TAG}-dev"
else
    TARGET="production"
    FULL_TAG="${IMAGE_NAME}:${TAG}"
fi

log_info "Building $ENV image..."
log_info "Target: $TARGET"
log_info "Tag: $FULL_TAG"

# Change to project root directory
cd "$(dirname "$0")/../../.."

# Build the image
log_info "Building Docker image..."
docker build \
    --target "$TARGET" \
    --tag "$FULL_TAG" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg GIT_COMMIT="$GIT_COMMIT" \
    --file infra/docker/Dockerfile \
    . || {
    log_error "Docker build failed"
    exit 1
}

log_info "Build completed successfully!"
log_info "Image: $FULL_TAG"

# Push to registry if requested
if [[ "$PUSH" == true ]]; then
    REGISTRY_TAG="${REGISTRY}/${FULL_TAG}"
    log_info "Tagging image for registry: $REGISTRY_TAG"
    docker tag "$FULL_TAG" "$REGISTRY_TAG"

    log_info "Pushing to registry..."
    docker push "$REGISTRY_TAG" || {
        log_error "Failed to push image to registry"
        exit 1
    }

    log_info "Image pushed successfully: $REGISTRY_TAG"
fi

log_info "All operations completed successfully!"