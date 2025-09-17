from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Relationship
from pgvector.sqlalchemy import Vector
from uuid import uuid4
from app.db.base import Base

class MessageEmbedding(Base):
    __tablename__ = 'message_embeddings'

    id = Column(UUID(as_uuid=True), primary_key=True,default=uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_chunk = Column(String, nullable=False)
    embedding = Column(Vector(1024), nullable=False)
    message = Relationship("Message", back_populates="embeddings")