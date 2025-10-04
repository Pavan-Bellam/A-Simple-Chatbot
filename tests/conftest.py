import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import create_app
from app.db.base import Base
from app.db.engine import SessionLocal
from app.api.deps import get_db_session
from app.core.settings import settings


# Test database URL - using environment variable (set in docker-compose or .env)
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev_user:dev_password@localhost:5432/chatbot_db")

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

# Create test session
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after each test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "sub": "test-user-123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "status": "active"
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "role": "user",
        "content": "Hello, this is a test message",
        "token_count": 10,
        "message_count": 1,
        "provider": "openai",
        "model": "gpt-4"
    }


@pytest.fixture
def mock_jwt_payload():
    """Mock JWT payload for testing."""
    return {
        "sub": "test-user-123",
        "email": "test@example.com",
        "token_use": "access",
        "exp": 9999999999,
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/test-pool"
    }


@pytest.fixture
def mock_authorization_header():
    """Mock authorization header for testing."""
    return "Bearer mock-jwt-token"
