import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.user import User
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.schemas.messages import MessageCreate


class TestHealthAPI:
    """Test cases for health endpoint."""
    
    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "app"
        assert "time" in data


class TestSecureAPI:
    """Test cases for secure endpoint."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_secure_endpoint_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful access to secure endpoint."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user in database
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Access Granted"
        assert "user" in data
    
    def test_secure_endpoint_no_auth_header(self, client: TestClient):
        """Test secure endpoint without authorization header."""
        response = client.get("/api/v1/secure")
        assert response.status_code == 401
        assert "Missing or Invalid Authorization Header" in response.json()["detail"]
    
    def test_secure_endpoint_invalid_auth_header(self, client: TestClient):
        """Test secure endpoint with invalid authorization header."""
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Invalid token"}
        )
        assert response.status_code == 401
        assert "Missing or Invalid Authorization Header" in response.json()["detail"]


class TestConversationsAPI:
    """Test cases for conversations endpoints."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_create_conversation_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful conversation creation."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user in database
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        conversation_data = {
            "title": "Test Conversation"
        }
        
        response = client.post(
            "/api/v1/conversation",
            json=conversation_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["title"] == "Test Conversation"
        assert "conversation_id" in data
        assert "created_at" in data
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_get_conversations_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful conversation retrieval."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversations
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create multiple conversations
        for i in range(3):
            conversation = Conversation(
                user_id=user.id,
                title=f"Conversation {i}"
            )
            db_session.add(conversation)
        db_session.commit()
        
        response = client.get(
            "/api/v1/conversations",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in conv for conv in data)
        assert all("title" in conv for conv in data)
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_get_conversations_with_pagination(self, mock_verify_token, client: TestClient, db_session):
        """Test conversation retrieval with pagination."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversations
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create multiple conversations
        for i in range(5):
            conversation = Conversation(
                user_id=user.id,
                title=f"Conversation {i}"
            )
            db_session.add(conversation)
        db_session.commit()
        
        # Test pagination
        response = client.get(
            "/api/v1/conversations?skip=2&limit=2",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_update_conversation_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful conversation update."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Original Title"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        update_data = {
            "title": "Updated Title",
            "status": "archived"
        }
        
        response = client.patch(
            f"/api/v1/conversation/{conversation.id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "archived"
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_update_conversation_not_found(self, mock_verify_token, client: TestClient, db_session):
        """Test conversation update when conversation doesn't exist."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        non_existent_id = uuid4()
        update_data = {
            "title": "Updated Title"
        }
        
        response = client.patch(
            f"/api/v1/conversation/{non_existent_id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_delete_conversation_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful conversation deletion."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="To Be Deleted"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        response = client.delete(
            f"/api/v1/conversation/{conversation.id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 204
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_delete_conversation_not_found(self, mock_verify_token, client: TestClient, db_session):
        """Test conversation deletion when conversation doesn't exist."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        non_existent_id = uuid4()
        
        response = client.delete(
            f"/api/v1/conversation/{non_existent_id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]
    
    @patch('app.services.chat.chat')
    @patch('app.api.deps.jwt_service.verify_token')
    def test_chat_endpoint_success(self, mock_verify_token, mock_chat, client: TestClient, db_session):
        """Test successful chat endpoint."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Mock chat service
        mock_chat.return_value = "AI response message"
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Chat Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        chat_data = {
            "user_input": "Hello, how are you?",
            "provider": "openai",
            "model": "gpt-4"
        }
        
        response = client.post(
            f"/api/v1/conversation/{conversation.id}/chat",
            json=chat_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Verify the mocked chat service was called and returned correctly
        assert "content" in data
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0


class TestMessagesAPI:
    """Test cases for messages endpoints."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_create_message_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful message creation."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message_data = {
            "conversation_id": str(conversation.id),
            "role": "user",
            "content": "Test message",
            "token_count": 10,
            "message_count": 1,
            "provider": "openai",
            "model": "gpt-4"
        }
        
        response = client.post(
            "/api/v1/message",
            json=message_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test message"
        assert data["role"] == "user"
        assert data["conversation_id"] == str(conversation.id)
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_get_messages_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful message retrieval."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Create multiple messages
        for i in range(3):
            message = Message(
                conversation_id=conversation.id,
                role=MessageRole.User,
                content=f"Message {i}",
                token_count=10,
                message_count=i + 1
            )
            db_session.add(message)
        db_session.commit()
        
        # GET with query parameters instead of JSON body
        response = client.get(
            f"/api/v1/message?conversation_id={conversation.id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in msg for msg in data)
        assert all("content" in msg for msg in data)
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_get_messages_with_pagination(self, mock_verify_token, client: TestClient, db_session):
        """Test message retrieval with pagination."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Create multiple messages
        for i in range(5):
            message = Message(
                conversation_id=conversation.id,
                role=MessageRole.User,
                content=f"Message {i}",
                token_count=10,
                message_count=i + 1
            )
            db_session.add(message)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/message?conversation_id={conversation.id}&skip=2&limit=2",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_delete_message_success(self, mock_verify_token, client: TestClient, db_session):
        """Test successful message deletion."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="To Be Deleted",
            token_count=10,
            message_count=1
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        response = client.delete(
            f"/api/v1/message/{conversation.id}/{message.id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 204
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_delete_message_not_found(self, mock_verify_token, client: TestClient, db_session):
        """Test message deletion when message doesn't exist."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user and conversation
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        non_existent_message_id = uuid4()
        
        response = client.delete(
            f"/api/v1/message/{conversation.id}/{non_existent_message_id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 404
        assert "No message with given id in given conversation id" in response.json()["detail"]


class TestAPIErrorHandling:
    """Test cases for API error handling."""
    
    def test_invalid_json_request(self, client: TestClient):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/api/v1/conversation",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_missing_required_fields(self, mock_verify_token, client: TestClient, db_session):
        """Test handling of missing required fields."""
        mock_verify_token.return_value = {"sub": "test-user", "email": "test@test.com"}

        # Create user in database
        user = User(
            cognito_sub="test-user",
            email="test@test.com"
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/conversation",
            json={},  # Missing required 'title' field
            headers={"Authorization": "Bearer mock-token"}
        )
        assert response.status_code == 422
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_invalid_uuid_format(self, mock_verify_token, client: TestClient, db_session):
        """Test handling of invalid UUID format."""
        mock_verify_token.return_value = {"sub": "test-user", "email": "test@test.com"}

        # Create user in database
        user = User(
            cognito_sub="test-user",
            email="test@test.com"
        )
        db_session.add(user)
        db_session.commit()

        response = client.patch(
            "/api/v1/conversation/invalid-uuid",
            json={"title": "New Title"},
            headers={"Authorization": "Bearer mock-token"}
        )
        assert response.status_code == 422
