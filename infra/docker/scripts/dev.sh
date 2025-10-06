#!/bin/bash
# Run all containers for development (API + DB)

cd "$(dirname "$0")/.."
docker-compose -f docker-compose.yml up
