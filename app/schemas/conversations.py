from pydantic import BaseModel
from uuid import UUID
from app.models.conversation import ConversationStatus
from datetime import datetime
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
