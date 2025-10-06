#!/bin/bash
# Run all CI checks: linting, formatting, and tests

set -e

cd "$(dirname "$0")/.."

echo "[CI] Starting CI pipeline..."
echo ""

# Build the image once
echo "[CI] Building Docker image..."
docker-compose -f docker-compose.ci.yml build
echo ""

# Run lint check
echo "[CI] Running lint check..."
if ! docker-compose -f docker-compose.ci.yml run --rm api uv run flake8 app tests; then
    echo "[CI] Linting failed!"
    docker-compose -f docker-compose.ci.yml down -v
    exit 1
fi
echo "[CI] Linting passed!"
echo ""

# Run format check
echo "[CI] Checking code formatting..."
if ! docker-compose -f docker-compose.ci.yml run --rm api uv run black --check app tests; then
    echo "[CI] Black formatting check failed!"
    docker-compose -f docker-compose.ci.yml down -v
    exit 1
fi
if ! docker-compose -f docker-compose.ci.yml run --rm api uv run isort --check-only app tests; then
    echo "[CI] isort formatting check failed!"
    docker-compose -f docker-compose.ci.yml down -v
    exit 1
fi
echo "[CI] Formatting check passed!"
echo ""

# Run tests (disable set -e to capture exit code)
echo "[CI] Running tests..."
set +e
docker-compose -f docker-compose.ci.yml up --abort-on-container-exit
TEST_EXIT_CODE=$?
set -e
echo ""

# Always cleanup
docker-compose -f docker-compose.ci.yml down -v

# Report results
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "[CI] SUCCESS: All checks passed!"
    echo "========================================"
    exit 0
else
    echo "[CI] FAILURE: Tests failed!"
    echo "========================================"
    exit $TEST_EXIT_CODE
fi
