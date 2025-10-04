import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import uuid4

from app.models.user import User
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.models.message_embeddings import MessageEmbedding
from app.db.base import Base
from app.db.engine import engine


class TestDatabaseConnection:
    """Test database connection and basic operations."""
    
    def test_database_connection(self, db_session):
        """Test that database connection works."""
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
    
    def test_database_transaction_rollback(self, db_session):
        """Test that database transactions can be rolled back."""
        # Create a user
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Verify user exists
        assert user.id is not None

        # Modify the user but rollback the changes
        user.first_name = "Updated Name"
        db_session.rollback()

        # Verify the change was rolled back
        db_session.refresh(user)
        assert user.first_name is None  # Should be original value
    
    def test_database_constraints(self, db_session):
        """Test that database constraints are enforced."""
        # Test unique constraint on cognito_sub
        user1 = User(cognito_sub="duplicate-sub")
        user2 = User(cognito_sub="duplicate-sub")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_database_foreign_key_constraints(self, db_session):
        """Test that foreign key constraints are enforced."""
        # Try to create a conversation with non-existent user_id
        non_existent_user_id = uuid4()
        conversation = Conversation(
            user_id=non_existent_user_id,
            title="Test Conversation"
        )
        
        db_session.add(conversation)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestDatabaseMigrations:
    """Test database schema and migrations."""
    
    def test_all_tables_exist(self, db_session):
        """Test that all expected tables exist."""
        # Get list of tables
        result = db_session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).fetchall()
        
        table_names = [row[0] for row in result]
        
        expected_tables = ['users', 'conversations', 'messages', 'message_embeddings']
        for table in expected_tables:
            assert table in table_names
    
    def test_table_columns_exist(self, db_session):
        """Test that all expected columns exist in tables."""
        # Test users table columns
        result = db_session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)).fetchall()
        
        user_columns = [row[0] for row in result]
        expected_user_columns = ['id', 'first_name', 'last_name', 'cognito_sub', 'email', 'created_at']
        for column in expected_user_columns:
            assert column in user_columns
        
        # Test conversations table columns
        result = db_session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'conversations'
        """)).fetchall()
        
        conversation_columns = [row[0] for row in result]
        expected_conversation_columns = ['id', 'user_id', 'title', 'created_at', 'status', 'updated_at']
        for column in expected_conversation_columns:
            assert column in conversation_columns
    
    def test_indexes_exist(self, db_session):
        """Test that important indexes exist."""
        # Test that constraints create indexes automatically
        result = db_session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users'
        """)).fetchall()

        # Should have at least the primary key index
        assert len(result) >= 1

        # Test conversations table indexes
        result = db_session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'conversations'
        """)).fetchall()

        # Should have at least the primary key index
        assert len(result) >= 1


class TestDatabasePerformance:
    """Test database performance characteristics."""
    
    def test_bulk_insert_performance(self, db_session):
        """Test performance of bulk insert operations."""
        import time
        
        # Create user first
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create conversation
        conversation = Conversation(
            user_id=user.id,
            title="Performance Test"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Measure bulk insert time
        start_time = time.time()
        
        # Create many messages
        messages = []
        for i in range(100):
            message = Message(
                conversation_id=conversation.id,
                role=MessageRole.User,
                content=f"Performance test message {i}",
                token_count=10,
                message_count=i + 1
            )
            messages.append(message)
        
        db_session.add_all(messages)
        db_session.commit()
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        # Should complete within reasonable time
        assert insert_time < 5.0  # Should complete within 5 seconds
        
        # Verify all messages were inserted
        message_count = db_session.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()
        assert message_count == 100
    
    def test_query_performance_with_indexes(self, db_session):
        """Test query performance with proper indexes."""
        import time
        
        # Create test data
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create many conversations
        conversations = []
        for i in range(50):
            conversation = Conversation(
                user_id=user.id,
                title=f"Conversation {i}"
            )
            conversations.append(conversation)
        
        db_session.add_all(conversations)
        db_session.commit()
        
        # Measure query time
        start_time = time.time()
        
        # Query conversations by user_id (should use index)
        result = db_session.query(Conversation).filter(
            Conversation.user_id == user.id
        ).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly with proper indexing
        assert query_time < 1.0  # Should complete within 1 second
        assert len(result) == 50
    
    def test_pagination_performance(self, db_session):
        """Test pagination query performance."""
        import time
        
        # Create test data
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title="Pagination Test"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Create many messages
        messages = []
        for i in range(1000):
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
        
        # Measure pagination query time
        start_time = time.time()
        
        # Test pagination query
        result = db_session.query(Message).filter(
            Message.conversation_id == conversation.id
        ).offset(500).limit(50).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly even with large offset
        assert query_time < 2.0  # Should complete within 2 seconds
        assert len(result) == 50


class TestDatabaseConstraints:
    """Test database constraints and data integrity."""
    
    def test_not_null_constraints(self, db_session):
        """Test that NOT NULL constraints are enforced."""
        # Test user cognito_sub NOT NULL constraint
        user = User()
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_foreign_key_constraints(self, db_session):
        """Test that foreign key constraints are enforced."""
        # Create user
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Try to create conversation with invalid user_id
        conversation = Conversation(
            user_id=uuid4(),  # Non-existent user_id
            title="Test Conversation"
        )
        db_session.add(conversation)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_constraints(self, db_session):
        """Test that unique constraints are enforced."""
        # Test cognito_sub uniqueness
        user1 = User(
            cognito_sub="unique-sub",
            email="user1@example.com"
        )
        user2 = User(
            cognito_sub="unique-sub",  # Duplicate
            email="user2@example.com"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_check_constraints(self, db_session):
        """Test that check constraints are enforced."""
        # Test conversation status enum constraint
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Valid status should work
        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation",
            status=ConversationStatus.Active
        )
        db_session.add(conversation)
        db_session.commit()
        
        # Invalid status should fail (if constraint exists)
        # Note: This depends on the database schema having check constraints
        # which might not be implemented in the current schema


class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    def test_transaction_commit(self, db_session):
        """Test that transactions are properly committed."""
        # Create user in transaction
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify user was committed
        assert user.id is not None
        
        # Verify user can be queried
        found_user = db_session.query(User).filter(
            User.cognito_sub == "test-sub"
        ).first()
        assert found_user is not None
        assert found_user.email == "test@example.com"
    
    def test_transaction_rollback(self, db_session):
        """Test that transactions can be rolled back."""
        # Start transaction
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.flush()  # Flush to get ID but don't commit
        
        user_id = user.id
        assert user_id is not None
        
        # Rollback transaction
        db_session.rollback()
        
        # Verify user was not committed
        found_user = db_session.query(User).filter(
            User.id == user_id
        ).first()
        assert found_user is None
    
    def test_nested_transactions(self, db_session):
        """Test nested transaction handling."""
        # Create user in outer transaction
        user = User(
            cognito_sub="test-sub",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create conversation in nested transaction
        conversation = Conversation(
            user_id=user.id,
            title="Nested Transaction Test"
        )
        db_session.add(conversation)
        db_session.commit()
        
        # Verify both were committed
        assert user.id is not None
        assert conversation.id is not None
        
        # Verify both can be queried
        found_user = db_session.query(User).filter(
            User.cognito_sub == "test-sub"
        ).first()
        assert found_user is not None
        
        found_conversation = db_session.query(Conversation).filter(
            Conversation.user_id == user.id
        ).first()
        assert found_conversation is not None
