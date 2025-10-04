from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    status: ConversationStatus
    created_at: datetime

class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None

class UpdateConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    title: str
    id: UUID
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime

class ChatRequest(BaseModel):
    user_input: str
    provider: str
    model: str

class ChatResponse(BaseModel):
    content: str