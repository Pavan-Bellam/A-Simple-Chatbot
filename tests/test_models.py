import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.models.message_embeddings import MessageEmbedding


class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user with valid data."""
        user = User(
            cognito_sub="test-sub-123",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.cognito_sub == "test-sub-123"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.created_at is not None
    
    def test_user_cognito_sub_unique(self, db_session):
        """Test that cognito_sub must be unique."""
        user1 = User(cognito_sub="duplicate-sub")
        user2 = User(cognito_sub="duplicate-sub")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_email_unique(self, db_session):
        """Test that email must be unique."""
        user1 = User(cognito_sub="sub1", email="duplicate@example.com")
        user2 = User(cognito_sub="sub2", email="duplicate@example.com")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_relationships(self, db_session):
        """Test user relationships with conversations."""
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
        
        assert len(user.conversations) == 1
        assert user.conversations[0].title == "Test Conversation"


class TestConversationModel:
    """Test cases for Conversation model."""
    
    def test_create_conversation(self, db_session):
        """Test creating a conversation with valid data."""
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
        
        assert conversation.id is not None
        assert conversation.user_id == user.id
        assert conversation.title == "Test Conversation"
        assert conversation.status == ConversationStatus.Active
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
    
    def test_conversation_status_enum(self, db_session):
        """Test conversation status enum values."""
        user = User(cognito_sub="test-sub")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Test Active status
        active_conv = Conversation(
            user_id=user.id,
            title="Active Conversation",
            status=ConversationStatus.Active
        )
        db_session.add(active_conv)
        db_session.commit()
        
        assert active_conv.status == ConversationStatus.Active
        
        # Test Archived status
        archived_conv = Conversation(
            user_id=user.id,
            title="Archived Conversation",
            status=ConversationStatus.Archived
        )
        db_session.add(archived_conv)
        db_session.commit()
        
        assert archived_conv.status == ConversationStatus.Archived
    
    def test_conversation_relationships(self, db_session):
        """Test conversation relationships with user and messages."""
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
        
        # Test user relationship
        assert conversation.owner.id == user.id
        
        # Test messages relationship
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Test message",
            token_count=10,
            message_count=1
        )
        db_session.add(message)
        db_session.commit()
        
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == "Test message"


class TestMessageModel:
    """Test cases for Message model."""
    
    def test_create_message(self, db_session):
        """Test creating a message with valid data."""
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
            content="Test message content",
            token_count=15,
            message_count=1,
            provider="openai",
            model="gpt-4"
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == MessageRole.User
        assert message.content == "Test message content"
        assert message.token_count == 15
        assert message.message_count == 1
        assert message.provider == "openai"
        assert message.model == "gpt-4"
        assert message.created_at is not None
    
    def test_message_role_enum(self, db_session):
        """Test message role enum values."""
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
        
        # Test all role types
        roles = [MessageRole.System, MessageRole.AI, MessageRole.User]
        for i, role in enumerate(roles):
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=f"Test {role.value} message",
                token_count=10,
                message_count=i + 1
            )
            db_session.add(message)
        
        db_session.commit()
        
        messages = db_session.query(Message).all()
        assert len(messages) == 3
        assert {msg.role for msg in messages} == {MessageRole.System, MessageRole.AI, MessageRole.User}
    
    def test_message_relationships(self, db_session):
        """Test message relationships with conversation and embeddings."""
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
        
        # Test conversation relationship
        assert message.conversation.id == conversation.id
        
        # Test embeddings relationship
        embedding = MessageEmbedding(
            message_id=message.id,
            chunk_index=0,
            text_chunk="Test chunk",
            embedding=[0.1] * 1024  # Mock 1024-dimensional embedding vector
        )
        db_session.add(embedding)
        db_session.commit()
        
        assert len(message.embeddings) == 1
        assert message.embeddings[0].text_chunk == "Test chunk"


class TestMessageEmbeddingModel:
    """Test cases for MessageEmbedding model."""
    
    def test_create_message_embedding(self, db_session):
        """Test creating a message embedding with valid data."""
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
            text_chunk="This is a test chunk",
            embedding=[0.1] * 1024  # Mock 1024-dimensional embedding
        )
        db_session.add(embedding)
        db_session.commit()
        db_session.refresh(embedding)
        
        assert embedding.id is not None
        assert embedding.message_id == message.id
        assert embedding.chunk_index == 0
        assert embedding.text_chunk == "This is a test chunk"
        assert len(embedding.embedding) == 1024
        assert embedding.embedding[0] == pytest.approx(0.1)
    
    def test_embedding_relationship(self, db_session):
        """Test embedding relationship with message."""
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
            embedding=[0.1] * 1024  # Mock 1024-dimensional embedding
        )
        db_session.add(embedding)
        db_session.commit()
        
        assert embedding.message.id == message.id
