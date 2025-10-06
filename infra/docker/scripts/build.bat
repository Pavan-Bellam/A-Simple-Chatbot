@echo off
REM Build the backend application Docker image

cd /d "%~dp0\.."
docker-compose -f docker-compose.yml build api
