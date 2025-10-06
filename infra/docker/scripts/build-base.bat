@echo off
REM Build and optionally push the base image with all dependencies

setlocal enabledelayedexpansion

set IMAGE_NAME=hero7hero/simple-chatbot
set TAG=latest

REM Parse arguments
if "%1"=="--push" (
    set PUSH=true
) else (
    set PUSH=false
)

echo [INFO] Building base image: %IMAGE_NAME%:%TAG%

REM Go to project root
cd /d "%~dp0\..\..\..\"

REM Build base image
docker build -f infra/docker/Dockerfile.base -t %IMAGE_NAME%:%TAG% .

if errorlevel 1 (
    echo [ERROR] Failed to build base image
    exit /b 1
)

echo [INFO] Base image built successfully: %IMAGE_NAME%:%TAG%

REM Push to registry if requested
if "%PUSH%"=="true" (
    echo [INFO] Pushing to registry...
    docker push %IMAGE_NAME%:%TAG%

    if errorlevel 1 (
        echo [ERROR] Failed to push image
        exit /b 1
    )

    echo [INFO] Base image pushed: %IMAGE_NAME%:%TAG%
) else (
    echo [INFO] To push to Docker Hub, run: %0 --push
    echo [INFO] Make sure you're logged in: docker login
)
