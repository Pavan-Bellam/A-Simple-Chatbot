@echo off
REM Run all containers for development (API + DB)

cd /d "%~dp0\.."
docker-compose -f docker-compose.yml up
