#!/bin/bash
# Build the backend application Docker image

cd "$(dirname "$0")/.."
docker-compose -f docker-compose.yml build api
