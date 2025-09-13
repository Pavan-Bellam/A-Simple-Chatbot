import uuid
from sqlalchemy import Column, String, TIMESTAMP, func, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import User
from app.db.base import Base
import enum

class ConversationStatus(enum.Enum):
    Active = 'active'
    Archived = 'archived'
    
class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(UUID(as_uuid = True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable = False
    )
    status = Column(Enum(ConversationStatus), default = ConversationStatus.Active)
    updated_at = Column(
        TIMESTAMP(timezone = True), 
        server_default=func.now(),
        onupdate = func.now(),
        nullable=False
    )

    owner = relationship("User", back_populates="conversations")