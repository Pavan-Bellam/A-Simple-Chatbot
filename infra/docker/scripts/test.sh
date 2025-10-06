#!/bin/bash
# Run tests in CI environment

set -e

cd "$(dirname "$0")/.."

# Run tests and capture exit code (disable set -e temporarily)
set +e
docker-compose -f docker-compose.ci.yml up --build --abort-on-container-exit
TEST_EXIT_CODE=$?
set -e

# Always cleanup
docker-compose -f docker-compose.ci.yml down -v

# Exit with the test exit code
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
    exit 0
else
    echo "[FAILURE] Tests failed with exit code $TEST_EXIT_CODE"
    exit $TEST_EXIT_CODE
fi
