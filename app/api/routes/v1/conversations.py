from fastapi import APIRouter, Depends, Query
from app.api.deps import get_user_dependency, get_db_session
from app.models.conversation import Conversation
from app.schemas.conversations import CreateConversationResponse, CreateConversationRequest, GetConversationsResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated,List


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
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Conversation"
        )
        


@router.get(
    '/conversations',
    summary='get latest `n` conversations',
    response_model = List[GetConversationsResponse],
    status_code=200
    )
async def get_conversations(
        skip: Annotated[int,Query(ge=0, description="Number of records to skip")] = 0,
        limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of records to return")] = 10,
        user=Depends(get_user_dependency),
        db=Depends(get_db_session)
        ): 
    try:
        conversations = db.query(Conversation) \
                        .filter(Conversation.owner == user) \
                        .offset(skip) \
                        .limit(limit) \
                        .all()
        return conversations
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retreive conversations from DB'
        )
    




