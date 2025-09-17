from app.db.base import Base
import uuid
from sqlalchemy import Column, String,Integer, UUID, TIMESTAMP, func, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum


class MessageRole(enum.Enum):
    System = 'system'
    AI = 'ai'
    User = 'user'

class Message(Base):
    __tablename__ = 'messages'

    id= Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True),ForeignKey('conversations.id'),nullable=False)
    message_count = Column(Integer, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(String, nullable=True)
    token_count = Column(Integer, nullable=False)
    provider = Column(String)
    model = Column(String)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default= func.now(),
        nullable=False
    )

    conversation = relationship('Conversation', back_populates="messages")
    embeddings = relationship('MessageEmbedding', back_populates="message", cascade='all, delete')