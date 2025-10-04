import pytest
from unittest.mock import patch, Mock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.models.message_embeddings import MessageEmbedding


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_complete_chat_workflow(self, mock_verify_token, client: TestClient, db_session):
        """Test complete chat workflow from user creation to message exchange."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # 1. Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # 2. Create conversation
        conversation_data = {
            "title": "My First Chat"
        }
        
        response = client.post(
            "/api/v1/conversation",
            json=conversation_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 201
        conversation_response = response.json()
        conversation_id = conversation_response["conversation_id"]
        
        # 3. Send a message
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Hello, how are you?",
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
        message_response = response.json()
        assert message_response["content"] == "Hello, how are you?"
        
        # 4. Retrieve messages
        response = client.get(
            f"/api/v1/message?conversation_id={conversation_id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello, how are you?"
        
        # 5. Update conversation
        update_data = {
            "title": "Updated Chat Title",
            "status": "archived"
        }
        
        response = client.patch(
            f"/api/v1/conversation/{conversation_id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        updated_conversation = response.json()
        assert updated_conversation["title"] == "Updated Chat Title"
        assert updated_conversation["status"] == "archived"
        
        # 6. Get all conversations
        response = client.get(
            "/api/v1/conversations",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 1
        assert conversations[0]["title"] == "Updated Chat Title"
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_multi_user_isolation(self, mock_verify_token, client: TestClient, db_session):
        """Test that users can only access their own data."""
        # Create two users
        user1 = User(
            cognito_sub="user-1",
            email="user1@example.com"
        )
        user2 = User(
            cognito_sub="user-2",
            email="user2@example.com"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Create conversations for both users
        conv1 = Conversation(
            user_id=user1.id,
            title="User 1 Conversation"
        )
        conv2 = Conversation(
            user_id=user2.id,
            title="User 2 Conversation"
        )
        db_session.add_all([conv1, conv2])
        db_session.commit()
        db_session.refresh(conv1)
        db_session.refresh(conv2)
        
        # Mock JWT for user 1
        mock_verify_token.return_value = {
            "sub": "user-1",
            "email": "user1@example.com"
        }
        
        # User 1 should only see their own conversations
        response = client.get(
            "/api/v1/conversations",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 1
        assert conversations[0]["title"] == "User 1 Conversation"
        
        # User 1 should not be able to access user 2's conversation
        response = client.patch(
            f"/api/v1/conversation/{conv2.id}",
            json={"title": "Hacked Title"},
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 404  # Not found because user doesn't own it
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_conversation_cascade_delete(self, mock_verify_token, client: TestClient, db_session):
        """Test that deleting a conversation also deletes its messages."""
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
        
        # Verify messages exist
        messages_before = db_session.query(Message).filter(
            Message.conversation_id == conversation.id
        ).all()
        assert len(messages_before) == 3
        
        # Delete conversation
        response = client.delete(
            f"/api/v1/conversation/{conversation.id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 204
        
        # Verify messages are also deleted (cascade)
        messages_after = db_session.query(Message).filter(
            Message.conversation_id == conversation.id
        ).all()
        assert len(messages_after) == 0


class TestDataConsistency:
    """Test data consistency and integrity."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_message_count_consistency(self, mock_verify_token, client: TestClient, db_session):
        """Test that message counts are consistent."""
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
        
        # Create messages with sequential message counts
        for i in range(5):
            message_data = {
                "conversation_id": str(conversation.id),
                "role": "user",
                "content": f"Message {i}",
                "token_count": 10,
                "message_count": i + 1,
                "provider": "openai",
                "model": "gpt-4"
            }
            
            response = client.post(
                "/api/v1/message",
                json=message_data,
                headers={"Authorization": "Bearer mock-token"}
            )
            assert response.status_code == 201
        
        # Verify all messages were created with correct counts
        response = client.get(
            f"/api/v1/message?conversation_id={conversation.id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 5
        
        # Verify message counts are sequential
        message_counts = [msg["message_count"] for msg in messages]
        assert message_counts == [1, 2, 3, 4, 5]
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_token_count_accumulation(self, mock_verify_token, client: TestClient, db_session):
        """Test that token counts accumulate correctly."""
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
        
        # Create messages with increasing token counts
        token_counts = [5, 10, 15, 20]
        for i, token_count in enumerate(token_counts):
            message_data = {
                "conversation_id": str(conversation.id),
                "role": "user",
                "content": f"Message with {token_count} tokens",
                "token_count": token_count,
                "message_count": i + 1,
                "provider": "openai",
                "model": "gpt-4"
            }
            
            response = client.post(
                "/api/v1/message",
                json=message_data,
                headers={"Authorization": "Bearer mock-token"}
            )
            assert response.status_code == 201
        
        # Verify token counts are stored correctly
        response = client.get(
            f"/api/v1/message?conversation_id={conversation.id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 4
        
        # Verify token counts match
        stored_token_counts = [msg["token_count"] for msg in messages]
        assert stored_token_counts == token_counts


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_database_rollback_on_error(self, mock_verify_token, client: TestClient, db_session):
        """Test that database operations are rolled back on error."""
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
        db_session.refresh(user)
        
        # Try to create conversation with invalid data (missing title)
        conversation_data = {}  # Missing required 'title' field
        
        response = client.post(
            "/api/v1/conversation",
            json=conversation_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Should return validation error
        assert response.status_code == 422
        
        # Verify no conversation was created
        conversations = db_session.query(Conversation).all()
        assert len(conversations) == 0
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_concurrent_operations(self, mock_verify_token, client: TestClient, db_session):
        """Test handling of concurrent operations."""
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
        db_session.refresh(user)
        
        # Create conversation
        conversation_data = {
            "title": "Concurrent Test"
        }
        
        response = client.post(
            "/api/v1/conversation",
            json=conversation_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 201
        conversation_id = response.json()["conversation_id"]
        
        # Simulate concurrent message creation
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Concurrent message",
            "token_count": 10,
            "message_count": 1,
            "provider": "openai",
            "model": "gpt-4"
        }
        
        # Create multiple messages concurrently
        responses = []
        for i in range(3):
            response = client.post(
                "/api/v1/message",
                json=message_data,
                headers={"Authorization": "Bearer mock-token"}
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 201
        
        # Verify all messages were created
        response = client.get(
            f"/api/v1/message?conversation_id={conversation_id}",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 3


class TestPerformance:
    """Test performance characteristics."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_large_message_retrieval(self, mock_verify_token, client: TestClient, db_session):
        """Test retrieval of large number of messages."""
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
            title="Large Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Create many messages directly in database for performance
        messages = []
        for i in range(100):
            message = Message(
                conversation_id=conversation.id,
                role=MessageRole.User,
                content=f"Message {i}",
                token_count=10,
                message_count=i + 1
            )
            messages.append(message)
        
        db_session.add_all(messages)
        db_session.commit()
        
        # Test pagination with large dataset
        response = client.get(
            f"/api/v1/message?conversation_id={conversation.id}&skip=50&limit=25",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 25  # Should respect limit
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_conversation_pagination_performance(self, mock_verify_token, client: TestClient, db_session):
        """Test conversation pagination with large dataset."""
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
        db_session.refresh(user)
        
        # Create many conversations directly in database
        conversations = []
        for i in range(50):
            conversation = Conversation(
                user_id=user.id,
                title=f"Conversation {i}"
            )
            conversations.append(conversation)
        
        db_session.add_all(conversations)
        db_session.commit()
        
        # Test pagination
        response = client.get(
            "/api/v1/conversations?skip=10&limit=20",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 20  # Should respect limit
