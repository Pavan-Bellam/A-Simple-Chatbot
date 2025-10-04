# Docker Setup for A Simple Chatbot

This directory contains all Docker-related configurations for the A Simple Chatbot application, organized professionally for local development, CI/CD testing, and ECS production deployment.

## 🎯 Overview

- **Local Development**: Hot reload with volume mounting for real-time code changes
- **CI/CD Testing**: Temporary database containers for automated testing
- **Production**: Lightweight backend-only image for ECS deployment with external RDS

## 📁 Directory Structure

```
infra/docker/
├── Dockerfile                 # Multi-stage Dockerfile (dev/prod)
├── docker-compose.yml         # Development environment + hot reload
├── docker-compose.ci.yml      # CI/CD testing environment
├── docker-compose.prod.yml    # Production reference (ECS deployment)
├── .env.example              # Environment variables template
├── README.md                 # This file
├── init/                     # Database initialization scripts
│   └── 01-create-extensions.sql
└── scripts/                  # Management scripts
    ├── build.sh             # Build script (Linux/macOS)
    ├── build.bat            # Build script (Windows)
    ├── start.sh             # Start script (Linux/macOS)
    └── start.bat            # Start script (Windows)
```

## 🚀 Quick Start

### Using Root Makefile (Recommended)

```bash
# Setup environment file
make setup

# Start development with hot reload
make dev

# Run tests
make test

# Build production image
make prod-build

# View logs
make logs-api
```

### Manual Commands

#### Development Environment

1. **Copy environment file:**
   ```bash
   cp infra/docker/.env.example .env
   ```

2. **Edit the `.env` file** with your configuration values

3. **Start the development environment:**
   ```bash
   # Linux/macOS
   ./infra/docker/scripts/start.sh

   # Windows
   infra\docker\scripts\start.bat
   ```

#### CI/CD Testing

```bash
# Run tests
./infra/docker/scripts/start.sh --test

# Or start CI environment
./infra/docker/scripts/start.sh --env ci
```

#### Production Image Building

```bash
# Build production image for ECS
./infra/docker/scripts/build.sh --env prod

# Build and push to registry
./infra/docker/scripts/build.sh --env prod --push
```

## 🏗️ Build Options

### Multi-Stage Dockerfile

The Dockerfile uses multi-stage builds for optimal image sizes:

- **base**: Common system dependencies
- **development**: Development dependencies + hot reload
- **production**: Minimal production image

### Build Scripts

Use the build scripts for consistent image building:

```bash
# Development build
./infra/docker/scripts/build.sh --env dev

# Production build with push to registry
./infra/docker/scripts/build.sh --env prod --push --tag v1.0.0
```

## 🛠️ Available Services

### Development (docker-compose.yml)
- **api**: FastAPI application with hot reload and volume mounting
- **db**: PostgreSQL with pgvector extension (for local development)

### CI/CD (docker-compose.ci.yml)
- **api**: FastAPI application configured for testing
- **db**: Temporary PostgreSQL with pgvector (in-memory for speed)

### Production (docker-compose.prod.yml)
- **Reference only** - In actual ECS deployment:
  - **Backend**: Lightweight FastAPI container
  - **Database**: External RDS PostgreSQL with pgvector
  - **Load Balancer**: ALB handles SSL termination and routing

## 📋 Management Commands

### Start/Stop Services

```bash
# Start development environment
./infra/docker/scripts/start.sh

# Start production environment in background
./infra/docker/scripts/start.sh --env prod --detach

# Stop all services
./infra/docker/scripts/start.sh --stop
```

### View Logs

```bash
# View all logs
./infra/docker/scripts/start.sh --logs

# View specific service logs
./infra/docker/scripts/start.sh --logs api
./infra/docker/scripts/start.sh --logs db
```

### Restart Services

```bash
# Restart specific service
./infra/docker/scripts/start.sh --restart api
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `COGNITO_USER_POOL_ID` | AWS Cognito User Pool ID | Yes |

### Database Initialization

Database extensions and initial setup are handled automatically via scripts in `init/`:

- `01-create-extensions.sql`: Creates necessary PostgreSQL extensions

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 5432 are available
2. **Permission issues**: Ensure Docker daemon is running and user has permissions
3. **Environment file**: Verify `.env` file exists and is configured

### Logs and Debugging

```bash
# Check service status
docker-compose ps

# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f api
```

### Health Checks

All services include health checks. Check status:

```bash
# Check container health
docker ps

# Test API health endpoint
curl http://localhost:8000/health
```

## 🚀 Deployment

### Development Deployment
- Suitable for local development
- Includes hot reload and debugging tools
- Uses volume mounts for live code changes

### Production Deployment
- Optimized for performance and security
- Multi-worker setup
- Health checks and resource limits
- Lightweight backend-only for ECS

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

When making changes to Docker configuration:

1. Test in development environment first
2. Update both Linux and Windows scripts if needed
3. Update this README with any new features
4. Follow the existing naming conventions