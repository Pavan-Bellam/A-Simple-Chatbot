@echo off
REM Start script for A Simple Chatbot services (Windows)

setlocal enabledelayedexpansion

REM Default values
set ENV=dev
set DETACH=false
set BUILD=false
set LOGS=
set STOP=false
set RESTART=
set TEST=false

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
if "%1"=="-d" (
    set DETACH=true
    shift
    goto :parse_args
)
if "%1"=="--detach" (
    set DETACH=true
    shift
    goto :parse_args
)
if "%1"=="-b" (
    set BUILD=true
    shift
    goto :parse_args
)
if "%1"=="--build" (
    set BUILD=true
    shift
    goto :parse_args
)
if "%1"=="--logs" (
    set LOGS=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--stop" (
    set STOP=true
    shift
    goto :parse_args
)
if "%1"=="--restart" (
    set RESTART=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--test" (
    set TEST=true
    shift
    goto :parse_args
)
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help
echo Unknown option: %1
goto :show_help

:args_done

REM Change to infra/docker directory
cd /d "%~dp0\.."

REM Set compose file based on environment
if "%ENV%"=="prod" (
    set COMPOSE_FILE=docker-compose.prod.yml
    echo [INFO] Using production configuration (for image building)
) else if "%ENV%"=="ci" (
    set COMPOSE_FILE=docker-compose.ci.yml
    echo [INFO] Using CI/CD configuration
) else if "%ENV%"=="dev" (
    set COMPOSE_FILE=docker-compose.yml
    echo [INFO] Using development configuration
) else (
    echo [ERROR] Invalid environment: %ENV%. Must be 'dev', 'ci', or 'prod'
    exit /b 1
)

REM Handle stop command
if "%STOP%"=="true" (
    echo [INFO] Stopping all services...
    docker-compose -f %COMPOSE_FILE% down
    echo [INFO] All services stopped
    goto :eof
)

REM Handle logs command
if not "%LOGS%"=="" (
    echo [INFO] Showing logs for service: %LOGS%
    docker-compose -f %COMPOSE_FILE% logs -f %LOGS%
    goto :eof
)

REM Handle restart command
if not "%RESTART%"=="" (
    echo [INFO] Restarting service: %RESTART%
    docker-compose -f %COMPOSE_FILE% restart %RESTART%
    echo [INFO] Service restarted: %RESTART%
    goto :eof
)

REM Handle test command
if "%TEST%"=="true" (
    if not "%ENV%"=="ci" (
        echo [WARN] Test mode enabled, switching to CI environment
        set ENV=ci
        set COMPOSE_FILE=docker-compose.ci.yml
    )
    echo [INFO] Running tests in CI environment...
    docker-compose -f %COMPOSE_FILE% up --build --abort-on-container-exit
    set exit_code=!errorlevel!
    docker-compose -f %COMPOSE_FILE% down -v
    echo [INFO] Tests completed with exit code: !exit_code!
    exit /b !exit_code!
)

REM Check if .env file exists for production
if "%ENV%"=="prod" (
    if not exist "../../.env.prod" (
        echo [ERROR] Production environment file ^(.env.prod^) not found!
        echo [ERROR] Please create .env.prod with production configurations
        exit /b 1
    )
)

REM Build images if requested
if "%BUILD%"=="true" (
    echo [INFO] Building images...
    call scripts\build.bat --env %ENV%
    if errorlevel 1 exit /b 1
)

REM Start services
echo [INFO] Starting services...

set COMPOSE_ARGS=-f %COMPOSE_FILE%

if "%DETACH%"=="true" (
    set COMPOSE_ARGS=!COMPOSE_ARGS! -d
)

docker-compose !COMPOSE_ARGS! up

if "%DETACH%"=="true" (
    echo [INFO] Services started in detached mode
    echo [INFO] To view logs: %0 --logs ^<service_name^>
    echo [INFO] To stop: %0 --stop
    echo.
    echo [INFO] Service status:
    docker-compose -f %COMPOSE_FILE% ps
) else (
    echo [INFO] Services stopped
)
goto :eof

:show_help
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   -e, --env ENV          Environment (dev^|ci^|prod) [default: dev]
echo   -d, --detach           Run in detached mode
echo   -b, --build            Build images before starting
echo   --logs SERVICE         Show logs for specific service
echo   --stop                 Stop all services
echo   --restart SERVICE      Restart specific service
echo   --test                 Run tests in CI environment
echo   -h, --help             Show this help message
echo.
echo Environments:
echo   dev                    Local development with hot reload and volume mounting
echo   ci                     CI/CD testing with temporary database
echo   prod                   Production image build (for ECS deployment)
echo.
echo Examples:
echo   %0                     Start development environment
echo   %0 --env ci --test     Run tests in CI environment
echo   %0 --env prod --build  Build production image for ECS
echo   %0 --logs api          Show API service logs
echo   %0 --stop              Stop all services
goto :eof