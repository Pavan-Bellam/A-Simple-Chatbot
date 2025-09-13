from pydantic import BaseModel
from uuid import UUID
class CreateConversationResponse(BaseModel):
    status: str
    conversation_id: UUID
    title: str
    created_at: str


class CreateConversationRequest(BaseModel):
    title: str