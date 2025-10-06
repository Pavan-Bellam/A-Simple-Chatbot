@echo off
REM Run tests in CI environment

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

REM Run tests and capture exit code
docker-compose -f docker-compose.ci.yml up --build --abort-on-container-exit
set TEST_EXIT_CODE=%errorlevel%

REM Always cleanup
docker-compose -f docker-compose.ci.yml down -v

REM Exit with the test exit code
if %TEST_EXIT_CODE% equ 0 (
    echo [SUCCESS] All tests passed!
    exit /b 0
) else (
    echo [FAILURE] Tests failed with exit code %TEST_EXIT_CODE%
    exit /b %TEST_EXIT_CODE%
)
