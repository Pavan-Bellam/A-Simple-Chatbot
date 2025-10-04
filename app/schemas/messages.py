from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    conversation_id: UUID
    created_at: datetime

class GetMessageRequest(BaseModel):
    conversation_id: UUID

    

