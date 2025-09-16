from pydantic import BaseModel
from uuid import UUID
from app.models.conversation import ConversationStatus
from datetime import datetime
from typing import Optional
class CreateConversationResponse(BaseModel):
    status: str
    conversation_id: UUID
    title: str
    created_at: str


class CreateConversationRequest(BaseModel):
    title: str


class GetConversationsResponse(BaseModel):
    id: UUID
    title: str
    status: ConversationStatus
    created_at: datetime
    

    class Config:
        from_attributes = True

class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None

class UpdateConversationResponse(BaseModel):
    title: str
    id: UUID
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attribures = True

class ChatRequest(BaseModel):
    user_input: str
    provider: str
    model: str

class ChatResponse(BaseModel):
    content: str