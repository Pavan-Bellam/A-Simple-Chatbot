from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.message import MessageRole


class MessageBase(BaseModel):
    role: MessageRole
    content: str
    token_count: int
    message_count: int
    provider: Optional[str] = None
    model: Optional[str] = None

class MessageCreate(MessageBase):
    conversation_id: UUID

class MessageRead(MessageBase):
    id: UUID
    conversation_id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

class GetMessageRequest(BaseModel):
    conversation_id: UUID

    

