# A Simple Chatbot

A scalable FastAPI-based chatbot designed for production deployment on AWS ECS with intelligent context management using vector databases.

## 🎯 Overview

- **Backend**: FastAPI with JWT authentication via AWS Cognito
- **Database**: PostgreSQL with pgvector extension for semantic search
- **Context Management**: Hybrid approach with recent messages + vector similarity search
- **Deployment**: Containerized for AWS ECS with external RDS
- **Development**: Docker with hot reload for rapid iteration

## 🏗️ Architecture

### Context Management Strategy
- **Recent Messages**: Last 20 messages for immediate context
- **Semantic Search**: Vector embeddings for relevant historical context
- **Intelligent Retrieval**: Combines recent + relevant messages for LLM prompts

### Production Stack
- **API**: FastAPI containers on ECS behind ALB
- **Database**: RDS PostgreSQL with pgvector
- **Authentication**: AWS Cognito User Pools
- **LLM**: OpenAI API integration

## 📁 Project Structure

```
A-Simple-Chatbot/
├── app/                       # FastAPI application
│   ├── api/                   # API routes and dependencies
│   ├── core/                  # Core configurations
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   └── services/              # Business logic
├── infra/                     # Infrastructure
│   └── docker/                # Docker configurations
│       ├── Dockerfile         # Multi-stage build
│       ├── docker-compose.yml # Development setup
│       ├── docker-compose.ci.yml  # CI/CD testing
│       └── scripts/           # Management scripts
├── tests/                     # Comprehensive test suite
├── alembic/                   # Database migrations
├── scripts/                   # Utility scripts
├── docs/                      # Architecture documentation
├── pyproject.toml             # Project dependencies & tool configs
├── .flake8                    # Flake8 configuration
└── Makefile                   # Convenience commands
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- **Note**: Python is NOT required locally - everything runs in Docker!

### Development Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repo-url>
   cd A-Simple-Chatbot
   ```

2. **Configure environment variables:**
   ```bash
   # Copy example env file
   cp infra/docker/.env.example .env

   # Edit the .env file
   nano .env
   ```
   Required variables:
   - `DATABASE_URL` (auto-configured for development)
   - `COGNITO_*` (your AWS Cognito configuration)
   - `OPENAI_API_KEY` (your OpenAI API key)

3. **Start development environment:**
   ```bash
   make dev
   ```
   This starts:
   - FastAPI with hot reload on http://localhost:8000
   - PostgreSQL with pgvector on localhost:5432
   - Real-time code changes via volume mounting

   **First-time setup**: The first run will automatically pull the pre-built base image (`hero7hero/simple-chatbot:latest`) from Docker Hub, which contains all Python dependencies. This is a one-time download.

4. **Run database migrations:**
   ```bash
   uv run alembic upgrade head
   ```

5. **Access the application:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## 🛠️ Development Commands

### Using Makefile (Recommended)

#### Docker & Services
```bash
make dev              # Start development environment (API + DB)
make test             # Run test suite in CI environment
make build            # Build the backend application
make clean            # Clean up Docker resources
```

#### Code Quality (runs inside Docker)
```bash
make format           # Format code with black and isort
make lint             # Run flake8 linter
make lint-check       # Check formatting without modifying
make fix              # Auto-fix code formatting and imports
```
**Note**: All code quality commands run inside Docker containers, so you don't need Python installed locally!

#### Base Image Management
```bash
make build-base       # Build base image with all dependencies
make push-base        # Build and push base image to Docker Hub
```

### Manual Scripts
```bash
# Development
./infra/docker/scripts/dev.sh          # Linux/Mac
.\infra\docker\scripts\dev.bat         # Windows

# Testing
./infra/docker/scripts/test.sh
.\infra\docker\scripts\test.bat

# Build application
./infra/docker/scripts/build.sh
.\infra\docker\scripts\build.bat

# Base image (maintainers only)
./infra/docker/scripts/build-base.sh
.\infra\docker\scripts\build-base.bat
```

## 🐳 Docker Base Image

This project uses a **pre-built base image** (`hero7hero/simple-chatbot:latest`) that contains all heavy Python dependencies (langchain, sentence-transformers, etc.). This significantly speeds up builds for both development and CI/CD.

### For Developers (Normal Usage)
- **You don't need to build the base image!** It's automatically pulled from Docker Hub when you run `make dev` or `make test`.
- All builds are fast because they use the cached base image.

### For Maintainers (Dependency Updates)
**⚠️ IMPORTANT**: Only rebuild the base image when adding/updating major dependencies in `pyproject.toml`.

```bash
# 1. Update dependencies in pyproject.toml
# 2. Rebuild the base image locally
make build-base

# 3. Test that everything works
make test

# 4. Push to Docker Hub (requires authentication)
docker login
make push-base
```

**Guidelines**:
- **DO rebuild** when: Adding new packages, upgrading major dependencies (langchain, transformers, etc.)
- **DON'T rebuild** for: Minor version bumps, code changes, or configuration updates
- Always test locally before pushing to Docker Hub
- Coordinate with team before pushing new base images to avoid breaking CI/CD

### Base Image Contents
The base image includes:
- Python 3.12-slim
- System dependencies (build-essential, libpq-dev, curl)
- uv package manager
- All Python packages from `pyproject.toml` (production + dev)

## 🗄️ Database Management

### Migrations with Alembic
```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### Database Schema
- **Users**: Cognito integration with user profiles
- **Conversations**: Chat sessions with metadata
- **Messages**: Individual messages with embeddings
- **Message Embeddings**: Vector representations for semantic search

## 🔐 Authentication

Uses AWS Cognito for JWT-based authentication:

1. **Configure Cognito settings** in `.env`
2. **Use signup/login scripts:**
   ```bash
   # Signup (requires real email for confirmation)
   uv run python -m scripts.cognito.signup

   # Login (returns JWT token)
   uv run python -m scripts.cognito.login
   ```
3. **Use token in API calls:**
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/secure
   ```

## 🧪 Testing

Comprehensive test suite with different environments:

```bash
# Run all tests
make test

# Run specific test files
uv run pytest tests/test_api.py -v

# Run tests with coverage
uv run pytest --cov=app tests/
```

Test environments:
- **Development**: Full integration tests with real database
- **CI/CD**: Automated testing with temporary containers
- **Unit Tests**: Fast isolated tests for business logic


## 📊 Monitoring & Observability

- **Health Checks**: Built-in health endpoint for ECS
- **Logging**: Structured JSON logs for CloudWatch
- **Metrics**: Application performance monitoring ready
- **Error Tracking**: Sentry integration available

## 🤝 Contributing

1. **Setup development environment** (see Quick Start)
2. **Create feature branch:** `git checkout -b feature/new-feature`
3. **Format and lint your code:** `make format && make lint`
4. **Run tests:** `make test`
5. **Submit pull request** with tests and documentation

### Code Quality Standards

This project uses automated code quality tools to maintain consistency:

#### Formatting & Linting Tools
- **Black** (v25.9.0+): Code formatter with 100 char line length
- **isort** (v6.1.0+): Import statement organizer (black-compatible profile)
- **flake8** (v7.3.0+): Style guide enforcer with max complexity of 10

#### Configuration
All tools are configured in `pyproject.toml` and `.flake8`:
- Line length: 100 characters
- Target: Python 3.12+
- Excludes: alembic migrations, cache directories, vendor code

#### Usage
```bash
# Before committing
make format           # Auto-format code with black and isort
make lint             # Check for linting issues with flake8

# In CI/CD pipelines
make lint-check       # Verify formatting without changes

# Quick fix
make fix              # Format and fix all issues
```

#### Requirements
- **Type Hints**: Full typing coverage required for new code
- **Testing**: Comprehensive test coverage expected
- **Documentation**: Update relevant docs with changes
- **Linting**: All code must pass `make lint-check` before merging

## 📚 Additional Resources

- **API Documentation**: Available at `/docs` when running
- **Architecture Docs**: See `docs/` directory
- **Docker Guide**: See `infra/docker/README.md`
- **Database Schema**: Generated diagrams in `docs/`


---

