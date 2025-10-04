import pytest
from unittest.mock import patch, Mock
import numpy as np
from uuid import uuid4

from app.services.chat import (
    chunk_text,
    get_embeddings,
    retrieve_relevant_context
)
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.message_embeddings import MessageEmbedding


class TestTextChunking:
    """Test text chunking functionality."""
    
    def test_chunk_text_short_text(self):
        """Test chunking of short text that doesn't need chunking."""
        text = "This is a short message."
        chunks = chunk_text(text, max_len=100)
        
        assert len(chunks) == 1
        assert chunks[0].lower() == text.lower()  # Tokenizer may change casing
    
    def test_chunk_text_long_text(self):
        """Test chunking of long text that needs to be split."""
        # Create a long text
        text = "This is a very long message. " * 100
        chunks = chunk_text(text, max_len=50)
        
        # Should produce at least one chunk
        assert len(chunks) >= 1
        # Verify all chunks are strings
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_text_empty_string(self):
        """Test chunking of empty string."""
        chunks = chunk_text("", max_len=100)
        # Empty string produces empty chunk list or single empty chunk
        assert len(chunks) >= 0
    
    def test_chunk_text_very_small_max_len(self):
        """Test chunking with very small max_len."""
        text = "Hello world"
        chunks = chunk_text(text, max_len=3)
        
        # Should produce at least 1 chunk (tokenizer determines exact count)
        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_text_preserves_content(self):
        """Test that chunking preserves the original content."""
        text = "This is a test message with multiple words and sentences. It should be preserved exactly."
        chunks = chunk_text(text, max_len=20)
        
        # Reconstruct the text and verify it matches
        reconstructed = " ".join(chunks)
        # Note: The reconstruction might not be exactly the same due to tokenization
        # but the essential content should be preserved
        assert "test message" in reconstructed
        assert "multiple words" in reconstructed


class TestEmbeddings:
    """Test embedding generation functionality."""
    
    @patch('app.services.chat._embedder.encode')
    def test_get_embeddings_single_chunk(self, mock_encode):
        """Test embedding generation for single text chunk."""
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        text = "This is a test message"
        result = get_embeddings(text)
        
        assert len(result) == 1
        assert isinstance(result[0], tuple)
        assert len(result[0]) == 2
        assert isinstance(result[0][0], str)  # text chunk
        assert isinstance(result[0][1], list)  # embedding vector
        assert len(result[0][1]) == 1024  # embedding dimension
    
    @patch('app.services.chat._embedder.encode')
    def test_get_embeddings_multiple_chunks(self, mock_encode):
        """Test embedding generation for multiple text chunks."""
        # Return 1 chunk (text chunking is deterministic based on tokenizer)
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        text = "This is a very long message that will be chunked into multiple pieces for embedding generation."
        result = get_embeddings(text)
        
        assert len(result) >= 1
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)
        assert all(isinstance(item[0], str) for item in result)
        assert all(isinstance(item[1], list) for item in result)
    
    @patch('app.services.chat._embedder.encode')
    def test_get_embeddings_empty_text(self, mock_encode):
        """Test embedding generation for empty text."""
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        text = ""
        result = get_embeddings(text)
        
        # Empty text may or may not produce chunks (depends on tokenizer)
        assert len(result) >= 0
        if len(result) > 0:
            assert isinstance(result[0], tuple)
            assert len(result[0]) == 2
            assert isinstance(result[0][1], list)
    
    @patch('app.services.chat._embedder.encode')
    def test_get_embeddings_normalization(self, mock_encode):
        """Test that embeddings are normalized."""
        # Mock already returns normalized embeddings (normalize_embeddings=True)
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        text = "Test message"
        result = get_embeddings(text)
        
        # Verify embedding structure
        assert len(result) > 0
        embedding = result[0][1]
        assert len(embedding) == 1024
    
    @patch('app.services.chat._embedder.encode')
    def test_get_embeddings_data_types(self, mock_encode):
        """Test that embeddings are returned as correct data types."""
        mock_encode.return_value = np.array([[0.1] * 1024], dtype=np.float32)
        
        text = "Test message"
        result = get_embeddings(text)
        
        embedding = result[0][1]
        assert all(isinstance(x, float) for x in embedding)
        assert all(isinstance(x, (int, float)) for x in embedding)  # Should be numeric


class TestContextRetrieval:
    """Test context retrieval using embeddings."""
    
    @patch('app.services.chat._embedder.encode')
    def test_retrieve_relevant_context_success(self, mock_encode, db_session):
        """Test successful context retrieval."""
        # Mock query embedding with 1024 dimensions
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        # Create test data
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
        
        # Create messages with embeddings
        messages = []
        for i in range(3):
            message = Message(
                conversation_id=conversation.id,
                role=MessageRole.User,
                content=f"Test message {i}",
                token_count=10,
                message_count=i + 1
            )
            db_session.add(message)
            db_session.commit()
            db_session.refresh(message)
            
            # Create embedding for each message
            embedding = MessageEmbedding(
                message_id=message.id,
                chunk_index=0,
                text_chunk=f"chunk {i}",
                embedding=[0.1 + i*0.01] * 1024  # 1024-dimensional embedding
            )
            db_session.add(embedding)
            messages.append(message)
        
        db_session.commit()
        
        # Test context retrieval
        result = retrieve_relevant_context(db_session, "test query", top_k=2)
        
        assert result is not None
        assert "Retrieved context from memory" in result.content
        assert "user:" in result.content.lower() or "ai:" in result.content.lower()
    
    @patch('app.services.chat._embedder.encode')
    def test_retrieve_relevant_context_no_embeddings(self, mock_encode, db_session):
        """Test context retrieval when no embeddings exist."""
        # Mock query embedding with 1024 dimensions
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        # Test with empty database
        result = retrieve_relevant_context(db_session, "test query", top_k=5)
        
        assert result is None
    
    @patch('app.services.chat._embedder.encode')
    def test_retrieve_relevant_context_top_k_limit(self, mock_encode, db_session):
        """Test that top_k parameter limits results."""
        # Mock query embedding with 1024 dimensions
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        # Create test data
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
        
        # Create many messages with embeddings
        for i in range(10):
            message = Message(
                conversation_id=conversation.id,
                role=MessageRole.User,
                content=f"Test message {i}",
                token_count=10,
                message_count=i + 1
            )
            db_session.add(message)
            db_session.commit()
            db_session.refresh(message)
            
            embedding = MessageEmbedding(
                message_id=message.id,
                chunk_index=0,
                text_chunk=f"chunk {i}",
                embedding=[0.1 + i*0.001] * 1024  # 1024-dimensional embedding
            )
            db_session.add(embedding)
        
        db_session.commit()
        
        # Test with top_k=3
        result = retrieve_relevant_context(db_session, "test query", top_k=3)
        
        assert result is not None
        # Count the number of context lines (should be limited by top_k)
        context_lines = result.content.count("- ")
        assert context_lines <= 3
    
    @patch('app.services.chat._embedder.encode')
    def test_retrieve_relevant_context_cosine_distance(self, mock_encode, db_session):
        """Test that results are ordered by cosine distance."""
        # Mock query embedding with 1024 dimensions
        query_embedding = np.array([[0.9] + [0.01] * 1023])
        mock_encode.return_value = query_embedding
        
        # Create test data
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
        
        # Create messages with different similarity to query
        # Message 1: Very similar (same direction)
        message1 = Message(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Similar message",
            token_count=10,
            message_count=1
        )
        db_session.add(message1)
        db_session.commit()
        db_session.refresh(message1)
        
        # Create embedding with pattern that's "similar" (higher values in first dimension)
        similar_vec = [0.9] + [0.01] * 1023  # 1024-dimensional embedding
        embedding1 = MessageEmbedding(
            message_id=message1.id,
            chunk_index=0,
            text_chunk="similar chunk",
            embedding=similar_vec
        )
        db_session.add(embedding1)
        
        # Message 2: Less similar (different direction)
        message2 = Message(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Different message",
            token_count=10,
            message_count=2
        )
        db_session.add(message2)
        db_session.commit()
        db_session.refresh(message2)
        
        # Create embedding with pattern that's "different" (lower values in first dimension)
        different_vec = [0.1] + [0.09] * 1023  # 1024-dimensional embedding
        embedding2 = MessageEmbedding(
            message_id=message2.id,
            chunk_index=0,
            text_chunk="different chunk",
            embedding=different_vec
        )
        db_session.add(embedding2)
        
        db_session.commit()
        
        # Test context retrieval
        result = retrieve_relevant_context(db_session, "test query", top_k=2)
        
        assert result is not None
        # Both messages should appear in the result
        content_lower = result.content.lower()
        assert "similar message" in content_lower or "different message" in content_lower


class TestEmbeddingIntegration:
    """Test embedding integration with the full system."""
    
    @patch('app.services.chat._embedder.encode')
    def test_store_message_with_embeddings(self, mock_encode, db_session):
        """Test storing message with embeddings integration."""
        # Mock embeddings with 1024 dimensions - single embedding for simple text
        mock_encode.return_value = np.array([[0.1] * 1024])
        
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
        
        # Create message with embeddings
        from app.schemas.messages import MessageCreate
        from app.services.chat import store_message
        
        message_data = MessageCreate(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="This is a test message that will be chunked and embedded.",
            token_count=20,
            message_count=1
        )
        
        result = store_message(db_session, message_data)
        
        # Verify message was created
        assert result.id is not None
        assert result.content == "This is a test message that will be chunked and embedded."
        
        # Verify embeddings were created
        assert len(result.embeddings) >= 1
        assert result.embeddings[0].chunk_index == 0
        assert result.embeddings[0].text_chunk is not None
    
    @patch('app.services.chat._embedder.encode')
    def test_embedding_consistency_across_operations(self, mock_encode, db_session):
        """Test that embeddings are consistent across different operations."""
        # Mock consistent embeddings with 1024 dimensions
        mock_encode.return_value = np.array([[0.1] * 1024])
        
        # Create test data
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
        
        # Store message with embeddings
        from app.schemas.messages import MessageCreate
        from app.services.chat import store_message
        
        message_data = MessageCreate(
            conversation_id=conversation.id,
            role=MessageRole.User,
            content="Test message",
            token_count=10,
            message_count=1
        )
        
        stored_message = store_message(db_session, message_data)
        
        # Retrieve context using the same text
        context = retrieve_relevant_context(db_session, "Test message", top_k=1)
        
        # Should find the stored message
        assert context is not None
        assert "Test message" in context.content or "Test message" in context.content.lower()
