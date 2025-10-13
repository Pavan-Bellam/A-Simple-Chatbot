@echo off
REM Build and optionally push the base image with all dependencies to AWS ECR

setlocal enabledelayedexpansion

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

REM Construct ECR image name
set ECR_REGISTRY=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
set IMAGE_NAME=%ECR_REGISTRY%/%ECR_REPOSITORY%
if "%IMAGE_TAG%"=="" (
    set TAG=latest
) else (
    set TAG=%IMAGE_TAG%
)

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

REM Push to ECR if requested
if "%PUSH%"=="true" (
    echo [INFO] Logging into ECR...
    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%

    if errorlevel 1 (
        echo [ERROR] Failed to authenticate with ECR
        exit /b 1
    )

    echo [INFO] Pushing to ECR...
    docker push %IMAGE_NAME%:%TAG%

    if errorlevel 1 (
        echo [ERROR] Failed to push image
        exit /b 1
    )

    echo [INFO] Base image pushed to ECR: %IMAGE_NAME%:%TAG%
) else (
    echo [INFO] To push to ECR, run: %0 --push
    echo [INFO] Make sure AWS CLI is configured with proper credentials
)
