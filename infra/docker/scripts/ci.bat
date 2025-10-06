@echo off
REM Run all CI checks: linting, formatting, and tests

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo [CI] Starting CI pipeline...
echo.

REM Build the image once
echo [CI] Building Docker image...
docker-compose -f docker-compose.ci.yml build
if errorlevel 1 (
    echo [CI] Build failed!
    exit /b 1
)
echo.

REM Run lint check
echo [CI] Running lint check...
docker-compose -f docker-compose.ci.yml run --rm api uv run flake8 app tests
set LINT_EXIT_CODE=%errorlevel%
if %LINT_EXIT_CODE% neq 0 (
    echo [CI] Linting failed!
    docker-compose -f docker-compose.ci.yml down -v
    exit /b %LINT_EXIT_CODE%
)
echo [CI] Linting passed!
echo.

REM Run format check
echo [CI] Checking code formatting...
docker-compose -f docker-compose.ci.yml run --rm api uv run black --check app tests
set BLACK_EXIT_CODE=%errorlevel%
docker-compose -f docker-compose.ci.yml run --rm api uv run isort --check-only app tests
set ISORT_EXIT_CODE=%errorlevel%
if %BLACK_EXIT_CODE% neq 0 (
    echo [CI] Black formatting check failed!
    docker-compose -f docker-compose.ci.yml down -v
    exit /b %BLACK_EXIT_CODE%
)
if %ISORT_EXIT_CODE% neq 0 (
    echo [CI] isort formatting check failed!
    docker-compose -f docker-compose.ci.yml down -v
    exit /b %ISORT_EXIT_CODE%
)
echo [CI] Formatting check passed!
echo.

REM Run tests
echo [CI] Running tests...
docker-compose -f docker-compose.ci.yml up --abort-on-container-exit
set TEST_EXIT_CODE=%errorlevel%
echo.

REM Always cleanup
docker-compose -f docker-compose.ci.yml down -v

REM Report results
echo ========================================
if %TEST_EXIT_CODE% equ 0 (
    echo [CI] SUCCESS: All checks passed!
    echo ========================================
    exit /b 0
) else (
    echo [CI] FAILURE: Tests failed!
    echo ========================================
    exit /b %TEST_EXIT_CODE%
)
