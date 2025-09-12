# README: Scalable Chatbot Project

This repository contains a scalable chatbot designed to handle millions of users, leveraging FastAPI, PostgreSQL, AWS Cognito, and vector databases for efficient context management. Below are instructions for setup, development, and database management.

## Project Overview

- **Purpose**: Build a chatbot with scalable architecture for millions of concurrent users.
- **Key Features**:
  - **Context Management**: Hybrid approach with recent message retention and vector DB retrieval.
  - **Backend**: FastAPI with Uvicorn.
  - **Database**: PostgreSQL with Alembic migrations.
  - **Authentication**: AWS Cognito for JWT-based auth.
  - **Package Management**: UV for fast dependency resolution.
- **Status**: Production deployment TBD.

## Context Management Strategy

To ensure scalability and low-latency conversations:

- **Hot Path (Last K Messages)**: Stores the most recent `k` messages (e.g., `k=10`) in memory for quick access.
- **Summary**: Maintains a rolling summary of all prior messages (from first to `total - k`). Updated incrementally using a language model (e.g., OpenAI or local LLM).
- **Relevant Info Retrieval**: Uses a postgress vectorDB for semantic search of historical or external data.
  - **Setup**: Embed messages with Sentence Transformers, store with metadata (e.g., `user_id`, `timestamp`), query with cosine similarity (>0.7).
  - **Fallback**: Defaults to hot path summary if no relevant vectors are found.


## Development Setup

### Prerequisites
- Git
- Docker and Docker Compose
- Python 3.10+

### Step 1: Clone and Install Dependencies
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <project-root>
   ```
2. Install UV:
   - **macOS/Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - **Windows (PowerShell)**:
     ```bash
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - Verify: `uv --version`
3. Set up project:
   ```bash
   uv sync
   ```

### Step 2: Environment Configuration
1. Copy template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env`:


## Database Setup

Uses PostgreSQL with Docker Compose and Alembic for migrations.

### Step 1: Build and Start Database
1. Navigate:
   ```bash
   cd infra/compose
   ```
2. Build:
   ```bash
   docker compose -f db.compose.yaml build
   ```
3. Start:
   ```bash
   docker compose -f db.compose.yaml up -d
   ```
   - Verify: `docker compose -f db.compose.yaml logs` or connect via `psql`.
   - Stop: `docker compose -f db.compose.yaml down`.

### Step 2: Run Migrations
Alembic is configured in the root `alembic` folder (`alembic.ini`, `env.py` use `DB_URL`).
   ```
     Apply migrations:
   ```bash
   uv run alembic upgrade head
   ```

### Step 3: Insert Initial Data
Alembic is primarily for schema changes; use sparingly for seeding.
1. Create migration:
   ```bash
   uv run alembic revision --autogenerate -m "seed_initial_data"
   
2. Apply:
   ```bash
   uv run alembic upgrade head
   ```

## Running the Application

From root:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Access: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Logs: Tail or use Sentry.

## Authentication (Getting Tokens)

Uses AWS Cognito for JWT-based auth.

### Step 1: Cognito Config
1. Copy template:
   ```bash
   cp scripts/cognito/config_template.py scripts/cognito/config.py
   ```
2. Edit `config.py`

### Step 2: Signup
Use a **real email** (Cognito sends confirmation):
```bash
uv run python -m scripts.cognito.signup
```
- Confirm via email link.

### Step 3: Login
```bash
uv run python -m scripts.cognito.login 
```
- Output: Access token for `Authorization: Bearer <token>`.
- Refresh: Re-run login

## Info for Developers

### Updating OpenAPI Schema
Regenerate `openapi.yaml`:
```bash
uv run python -m scripts.export_openapi
```
- Run after changes in `app/routers` or `app/models`.
- Commit updated YAML.

### Updating Database Tables
1. Edit `app/models/` (e.g., add columns).
2. Generate migration:
   ```bash
   uv run alembic revision --autogenerate -m "add_new_column_to_users"
   ```
3. Review `alembic/versions/<generated_file>.py`.
4. Apply:
   ```bash
   uv run alembic upgrade head
   ```
5. Downgrade (if needed):
   ```bash
   uv run alembic downgrade -1
   ```

**Best Practices**:
- Test migrations in dev DB.
- Use `--autogenerate` for most changes; edit manually for complex cases.
- Version control `alembic/versions/`.

## Production Deployment

TBD. Planned:
- Dockerized app + DB + vector DB.
- AWS ECS/EKS or Kubernetes.
- Scaling: Horizontal pods, Redis caching, auto-scaling.
- Monitoring: Prometheus, Grafana, CloudWatch.
- CI/CD: GitHub Actions.

For questions, contact the team!