#!/bin/bash
# Start script for A Simple Chatbot services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV          Environment (dev|ci|prod) [default: dev]"
    echo "  -d, --detach           Run in detached mode"
    echo "  -b, --build            Build images before starting"
    echo "  --logs SERVICE         Show logs for specific service"
    echo "  --stop                 Stop all services"
    echo "  --restart SERVICE      Restart specific service"
    echo "  --test                 Run tests in CI environment"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Environments:"
    echo "  dev                    Local development with hot reload and volume mounting"
    echo "  ci                     CI/CD testing with temporary database"
    echo "  prod                   Production image build (for ECS deployment)"
    echo ""
    echo "Examples:"
    echo "  $0                     Start development environment"
    echo "  $0 --env ci --test     Run tests in CI environment"
    echo "  $0 --env prod --build  Build production image for ECS"
    echo "  $0 --logs api          Show API service logs"
    echo "  $0 --stop              Stop all services"
}

# Default values
ENV="dev"
DETACH=false
BUILD=false
LOGS=""
STOP=false
RESTART=""
TEST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        --logs)
            LOGS="$2"
            shift 2
            ;;
        --stop)
            STOP=true
            shift
            ;;
        --restart)
            RESTART="$2"
            shift 2
            ;;
        --test)
            TEST=true
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

# Change to infra/docker directory
cd "$(dirname "$0")/.."

# Set compose file based on environment
case "$ENV" in
    "prod")
        COMPOSE_FILE="docker-compose.prod.yml"
        log_info "Using production configuration (for image building)"
        ;;
    "ci")
        COMPOSE_FILE="docker-compose.ci.yml"
        log_info "Using CI/CD configuration"
        ;;
    "dev")
        COMPOSE_FILE="docker-compose.yml"
        log_info "Using development configuration"
        ;;
    *)
        log_error "Invalid environment: $ENV. Must be 'dev', 'ci', or 'prod'"
        exit 1
        ;;
esac

# Handle stop command
if [[ "$STOP" == true ]]; then
    log_info "Stopping all services..."
    docker-compose -f "$COMPOSE_FILE" down
    log_info "All services stopped"
    exit 0
fi

# Handle logs command
if [[ -n "$LOGS" ]]; then
    log_info "Showing logs for service: $LOGS"
    docker-compose -f "$COMPOSE_FILE" logs -f "$LOGS"
    exit 0
fi

# Handle restart command
if [[ -n "$RESTART" ]]; then
    log_info "Restarting service: $RESTART"
    docker-compose -f "$COMPOSE_FILE" restart "$RESTART"
    log_info "Service restarted: $RESTART"
    exit 0
fi

# Handle test command
if [[ "$TEST" == true ]]; then
    if [[ "$ENV" != "ci" ]]; then
        log_warn "Test mode enabled, switching to CI environment"
        ENV="ci"
        COMPOSE_FILE="docker-compose.ci.yml"
    fi
    log_info "Running tests in CI environment..."
    docker-compose -f "$COMPOSE_FILE" up --build --abort-on-container-exit
    exit_code=$?
    docker-compose -f "$COMPOSE_FILE" down -v
    log_info "Tests completed with exit code: $exit_code"
    exit $exit_code
fi

# Check if .env file exists for production
if [[ "$ENV" == "prod" && ! -f "../../.env.prod" ]]; then
    log_error "Production environment file (.env.prod) not found!"
    log_error "Please create .env.prod with production configurations"
    exit 1
fi

# Build images if requested
if [[ "$BUILD" == true ]]; then
    log_info "Building images..."
    ./scripts/build.sh --env "$ENV"
fi

# Start services
log_info "Starting services..."

COMPOSE_ARGS="-f $COMPOSE_FILE"

if [[ "$DETACH" == true ]]; then
    COMPOSE_ARGS="$COMPOSE_ARGS -d"
fi

docker-compose $COMPOSE_ARGS up

if [[ "$DETACH" == true ]]; then
    log_info "Services started in detached mode"
    log_info "To view logs: $0 --logs <service_name>"
    log_info "To stop: $0 --stop"

    # Show service status
    echo ""
    log_info "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
else
    log_info "Services stopped"
fi