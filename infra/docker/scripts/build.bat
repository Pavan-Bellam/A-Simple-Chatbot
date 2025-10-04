@echo off
REM Build script for A Simple Chatbot Docker images (Windows)

setlocal enabledelayedexpansion

REM Configuration
set IMAGE_NAME=chatbot
set REGISTRY=%REGISTRY%
if "%REGISTRY%"=="" set REGISTRY=localhost:5000
set BUILD_DATE=%date% %time%
for /f "tokens=*" %%i in ('git rev-parse --short HEAD 2^>nul') do set GIT_COMMIT=%%i
if "%GIT_COMMIT%"=="" set GIT_COMMIT=unknown

REM Default values
set ENV=dev
set TAG=latest
set PUSH=false

REM Parse command line arguments
:parse_args
if "%1"=="" goto :args_done
if "%1"=="-e" (
    set ENV=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--env" (
    set ENV=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="-t" (
    set TAG=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--tag" (
    set TAG=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="-p" (
    set PUSH=true
    shift
    goto :parse_args
)
if "%1"=="--push" (
    set PUSH=true
    shift
    goto :parse_args
)
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help
echo Unknown option: %1
goto :show_help

:args_done

REM Validate environment
if not "%ENV%"=="dev" if not "%ENV%"=="prod" (
    echo Invalid environment: %ENV%. Must be 'dev' or 'prod'
    exit /b 1
)

REM Set target based on environment
if "%ENV%"=="dev" (
    set TARGET=development
    set FULL_TAG=%IMAGE_NAME%:%TAG%-dev
) else (
    set TARGET=production
    set FULL_TAG=%IMAGE_NAME%:%TAG%
)

echo [INFO] Building %ENV% image...
echo [INFO] Target: %TARGET%
echo [INFO] Tag: %FULL_TAG%

REM Change to project root directory
cd /d "%~dp0\..\..\..\"

REM Build the image
echo [INFO] Building Docker image...
docker build ^
    --target %TARGET% ^
    --tag %FULL_TAG% ^
    --build-arg BUILD_DATE="%BUILD_DATE%" ^
    --build-arg GIT_COMMIT=%GIT_COMMIT% ^
    --file infra/docker/Dockerfile ^
    .

if errorlevel 1 (
    echo [ERROR] Docker build failed
    exit /b 1
)

echo [INFO] Build completed successfully!
echo [INFO] Image: %FULL_TAG%

REM Push to registry if requested
if "%PUSH%"=="true" (
    set REGISTRY_TAG=%REGISTRY%/%FULL_TAG%
    echo [INFO] Tagging image for registry: !REGISTRY_TAG!
    docker tag %FULL_TAG% !REGISTRY_TAG!

    echo [INFO] Pushing to registry...
    docker push !REGISTRY_TAG!
    if errorlevel 1 (
        echo [ERROR] Failed to push image to registry
        exit /b 1
    )

    echo [INFO] Image pushed successfully: !REGISTRY_TAG!
)

echo [INFO] All operations completed successfully!
goto :eof

:show_help
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   -e, --env ENV          Environment (dev^|prod) [default: dev]
echo   -t, --tag TAG          Image tag [default: latest]
echo   -p, --push             Push image to registry
echo   -h, --help             Show this help message
echo.
echo Examples:
echo   %0 --env dev           Build development image
echo   %0 --env prod --push   Build and push production image
goto :eof