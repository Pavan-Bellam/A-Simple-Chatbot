from fastapi import APIRouter, Depends
from app.api.deps import get_user_dependency, get_db_session
from app.models.conversation import Conversation, ConversationStatus
from app.schemas.conversations import CreateConversationResponse, CreateConversationRequest
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
router = APIRouter()

@router.post(
            '/conversation',
            summary='Create a new conversation',
            description="""
                        Creates a new conversation for the authenticated user.
                        - Requires a `title` in the request
                        - Conversation Status is Active when created
                        - return the conversation ID and metadata with a stauts code of 201 when successful
                        """,
            response_model=CreateConversationResponse,
            status_code=201
            )
async def create_conversation(request: CreateConversationRequest, user=Depends(get_user_dependency), db=Depends(get_db_session)):
    try: 
        new_conversation = Conversation(
            owner = user,
            title = request.title,
        )
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        return CreateConversationResponse(
            status = "success",
            conversation_id = new_conversation.id,
            title = new_conversation.title,
            created_at = new_conversation.created_at.isoformat()
        )
    except SQLAlchemyError as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Conversation"
        )
        




