@echo off
REM Run all containers for development (API + DB)

setlocal enabledelayedexpansion

REM Go to project root to load .env
cd /d "%~dp0\..\..\..\"

REM Load environment variables from .env file
if exist .env (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" (
                set "%%a=%%b"
            )
        )
    )
)

REM Check required environment variables
if "%AWS_ACCOUNT_ID%"=="" (
    echo [ERROR] Missing AWS_ACCOUNT_ID in .env file
    exit /b 1
)
if "%AWS_REGION%"=="" (
    echo [ERROR] Missing AWS_REGION in .env file
    exit /b 1
)
if "%ECR_REPOSITORY%"=="" (
    echo [ERROR] Missing ECR_REPOSITORY in .env file
    exit /b 1
)

echo [INFO] Starting development environment with ECR base image

REM Run with environment variables
cd infra\docker
docker-compose -f docker-compose.yml up
