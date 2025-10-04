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
├── docker/                    # Docker configurations
│   ├── Dockerfile             # Multi-stage build
│   ├── docker-compose.yml     # Development setup
│   ├── docker-compose.ci.yml  # CI/CD testing
│   └── scripts/               # Management scripts
├── tests/                     # Comprehensive test suite
├── alembic/                   # Database migrations
├── scripts/                   # Utility scripts
├── docs/                      # Architecture documentation
└── Makefile                   # Convenience commands
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Git

### Development Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repo-url>
   cd A-Simple-Chatbot
   make setup
   ```

2. **Configure environment variables:**
   ```bash
   # Edit the generated .env file
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
```bash
make dev              # Start development environment
make test             # Run test suite
make logs-api         # View API logs
make stop             # Stop all services
make prod-build       # Build production image
```

### Manual Commands
```bash
# Development
./docker/scripts/start.sh

# Testing
./docker/scripts/start.sh --test

# Production build
./docker/scripts/build.sh --env prod
```

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
3. **Run tests:** `make test`
4. **Submit pull request** with tests and documentation

### Code Quality
- **Linting**: Configured for consistent code style
- **Type Hints**: Full typing coverage required
- **Testing**: Comprehensive test coverage expected
- **Documentation**: Update relevant docs with changes

## 📚 Additional Resources

- **API Documentation**: Available at `/docs` when running
- **Architecture Docs**: See `docs/` directory
- **Docker Guide**: See `docker/README.md`
- **Database Schema**: Generated diagrams in `docs/`


---

