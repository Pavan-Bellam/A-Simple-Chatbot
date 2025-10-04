import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR

from app.services.auth import JWTService, jwt_service
from app.services.user import create_user, get_user_by_sub
from app.services.message import create_message, get_messages, get_k_messages
from app.services.chat import (
    get_history, 
    chunk_text, 
    get_embeddings, 
    store_message, 
    retrieve_relevant_context, 
    chat
)
from app.models.user import User
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.models.message_embeddings import MessageEmbedding
from app.schemas.messages import MessageCreate


class TestJWTService:
    """Test cases for JWT authentication service."""
    
    def test_jwt_service_initialization(self):
        """Test JWT service initializes correctly."""
        service = JWTService()
        assert service.jwk_client is not None
    
    @patch('app.services.auth.jwt.decode')
    @patch('app.services.auth.PyJWKClient')
    def test_verify_token_success(self, mock_jwk_client_class, mock_jwt_decode):
        """Test successful token verification."""
        # Setup mocks
        mock_jwk_client = Mock()
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwk_client_class.return_value = mock_jwk_client
        
        mock_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": 9999999999,
            "iss": "test-issuer",
            "token_use": "access"
        }
        mock_jwt_decode.return_value = mock_payload
        
        service = JWTService()
        result = service.verify_token("test-token")
        
        assert result == mock_payload
        mock_jwt_decode.assert_called_once()
    
    @patch('app.services.auth.jwt.decode')
    @patch('app.services.auth.PyJWKClient')
    def test_verify_token_expired(self, mock_jwk_client_class, mock_jwt_decode):
        """Test token verification with expired token."""
        from jwt import ExpiredSignatureError
        
        mock_jwk_client = Mock()
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwk_client_class.return_value = mock_jwk_client
        
        mock_jwt_decode.side_effect = ExpiredSignatureError("Token expired")
        
        service = JWTService()
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_token("expired-token")
        
        assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
        assert "Token Expired" in exc_info.value.detail
    
    @patch('app.services.auth.jwt.decode')
    @patch('app.services.auth.PyJWKClient')
    def test_verify_token_invalid_key(self, mock_jwk_client_class, mock_jwt_decode):
        """Test token verification with invalid key."""
        from jwt import InvalidKeyError
        
        mock_jwk_client = Mock()
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwk_client_class.return_value = mock_jwk_client
        
        mock_jwt_decode.side_effect = InvalidKeyError("Invalid key")
        
        service = JWTService()
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_token("invalid-token")
        
        assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
        assert "Invalid token" in exc_info.value.detail


class TestUserService:
    """Test cases for user service functions."""
    
    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        user_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }

        # The create_user function uses its own database session, but we can still test it
        # Note: In production this creates its own session, but the data should be visible
        create_user(user_data)

        # Refresh the session and verify user was created
        db_session.commit()
        user = db_session.query(User).filter(User.cognito_sub == "test-user-123").first()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
    
    def test_create_user_duplicate_sub(self, db_session):
        """Test user creation with duplicate cognito_sub."""
        user_data = {
            "sub": "duplicate-sub",
            "email": "test@example.com"
        }
        
        # Create first user
        create_user(user_data)

        # Try to create second user with same sub
        with pytest.raises(Exception):  # Should raise IntegrityError
            create_user(user_data)
    
    def test_get_user_by_sub_success(self, db_session):
        """Test successful user retrieval by sub."""
        # Create a user first
        user = User(
            cognito_sub="test-sub-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Test retrieval
        result = get_user_by_sub("test-sub-123")
        assert result.id == user.id
        assert result.cognito_sub == "test-sub-123"
    
    def test_get_user_by_sub_not_found(self, db_session):
        """Test user retrieval when user doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_sub("non-existent-sub")
        
        assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
        assert "User not found" in exc_info.value.detail


class TestMessageService:
    """Test cases for message service functions."""
    
    def test_create_message_success(self, db_session):
        """Test successful message creation."""
        # Create user and conversation first
        user = User(cognito_sub="test-sub")
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
        
        # Create message
        message_data = MessageCreate(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Test message",
            token_count=10,
            message_count=1,
            provider="openai",
            model="gpt-4"
        )
        
        result = create_message(db_session, message_data)
        
        assert result.id is not None
        assert result.conversation_id == conversation.id
        assert result.role == MessageRole.User
        assert result.content == "Test message"
        assert result.token_count == 10
        assert result.provider == "openai"
        assert result.model == "gpt-4"
    
    def test_get_messages_success(self, db_session):
        """Test successful message retrieval."""
        # Create user, conversation, and messages
        user = User(cognito_sub="test-sub")
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
        
        # Test retrieval
        result = get_messages(db_session, conversation.id, skip=0, limit=3)
        assert len(result) == 3
    
    def test_get_messages_not_found(self, db_session):
        """Test message retrieval when no messages exist."""
        conversation_id = uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            get_messages(db_session, conversation_id, skip=0, limit=10)
        
        assert exc_info.value.status_code == 404
        assert "No messages for given conversation id" in exc_info.value.detail
    
    def test_get_k_messages(self, db_session):
        """Test getting k latest messages."""
        # Create user, conversation, and messages
        user = User(cognito_sub="test-sub")
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
        
        # Test getting k messages
        result = get_k_messages(3, conversation.id, db_session)
        assert len(result) == 3


class TestChatService:
    """Test cases for chat service functions."""
    
    def test_get_history_empty(self, db_session):
        """Test getting history when no messages exist."""
        conversation_id = uuid4()
        history, token_count = get_history(10, db_session, conversation_id)
        
        assert history == []
        assert token_count == 0
    
    def test_get_history_with_messages(self, db_session):
        """Test getting history with existing messages."""
        # Create user, conversation, and messages
        user = User(cognito_sub="test-sub")
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
        
        # Create messages
        message1 = Message(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Hello",
            token_count=5,
            message_count=1
        )
        message2 = Message(
            conversation_id=conversation.id,
            role=MessageRole.AI,
            content="Hi there!",
            token_count=10,
            message_count=2
        )
        db_session.add_all([message1, message2])
        db_session.commit()
        
        history, token_count = get_history(10, db_session, conversation.id)
        
        assert len(history) == 2
        assert token_count == 10  # Should be the token_count from the last message
    
    def test_chunk_text(self):
        """Test text chunking functionality."""
        text = "This is a test message that should be chunked properly."
        chunks = chunk_text(text, max_len=10)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        # All chunks should be strings
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    @patch('app.services.chat._embedder.encode')
    def test_get_embeddings(self, mock_encode):
        """Test embedding generation."""
        import numpy as np
        mock_encode.return_value = np.array([[0.1] * 1024, [0.2] * 1024])
        
        text = "Test text for embedding"
        result = get_embeddings(text)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Each result should be a tuple of (text_chunk, embedding_vector)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)
        assert all(isinstance(item[0], str) for item in result)
        assert all(isinstance(item[1], list) for item in result)
    
    @patch('app.services.chat.get_embeddings')
    def test_store_message(self, mock_get_embeddings, db_session):
        """Test storing message with embeddings."""
        # Create user and conversation
        user = User(cognito_sub="test-sub")
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
        
        # Mock embeddings with 1024 dimensions
        mock_get_embeddings.return_value = [
            ("chunk1", [0.1] * 1024),
            ("chunk2", [0.2] * 1024)
        ]
        
        message_data = MessageCreate(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Test message",
            token_count=10,
            message_count=1
        )
        
        result = store_message(db_session, message_data)
        
        assert result.id is not None
        assert result.content == "Test message"
        assert len(result.embeddings) == 2
        assert result.embeddings[0].text_chunk == "chunk1"
        assert result.embeddings[1].text_chunk == "chunk2"
    
    @patch('app.services.chat._embedder.encode')
    def test_retrieve_relevant_context(self, mock_encode, db_session):
        """Test retrieving relevant context using embeddings."""
        import numpy as np
        # Mock query embedding with 1024 dimensions
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        # Create user, conversation, and message with embedding
        user = User(cognito_sub="test-sub")
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
            content="Test message",
            token_count=10,
            message_count=1
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        embedding = MessageEmbedding(
            message_id=message.id,
            chunk_index=0,
            text_chunk="Test chunk",
            embedding=[0.1] * 1024  # 1024-dimensional embedding
        )
        db_session.add(embedding)
        db_session.commit()
        
        result = retrieve_relevant_context(db_session, "test query", top_k=5)
        
        assert result is not None
        assert "Retrieved context from memory" in result.content
    
    @patch('app.services.chat.ChatOpenAI')
    @patch('app.services.chat.store_message')
    def test_chat_function(self, mock_store_message, mock_chat_openai, db_session):
        """Test the main chat function."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.content = "AI response"
        mock_response.response_metadata = {
            "token_usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm
        
        # Mock store_message to return a mock message
        mock_message = Mock()
        mock_message.id = uuid4()
        mock_store_message.return_value = mock_message
        
        # Create user and conversation
        user = User(cognito_sub="test-sub")
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
        
        result = chat(
            db_session, 
            conversation.id, 
            "Hello", 
            "gpt-4", 
            "openai"
        )
        
        assert result == "AI response"
        # Should call store_message twice (user message + AI response)
        assert mock_store_message.call_count == 2
