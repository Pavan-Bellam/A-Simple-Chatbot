from fastapi import APIRouter, Depends, Query
from app.api.deps import get_user_dependency, get_db_session
from app.models.conversation import Conversation
from app.schemas.conversations import CreateConversationResponse, CreateConversationRequest, GetConversationsResponse, UpdateConversationRequest, UpdateConversationResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated,List
from uuid import UUID

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
    


@router.patch(
    '/conversation/{id}',
    summary = 'Update a conversation(status and title)',
    response_model = UpdateConversationResponse,
    status_code=200
)
async def update_conversation(
          id: UUID,
          request: UpdateConversationRequest,
          user= Depends(get_user_dependency),
          db = Depends(get_db_session)
          ):
    try:
        conversation = db.query(Conversation) \
                    .filter(Conversation.id == id, Conversation.owner == user) \
                    .first()
        
        if not conversation:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail = 'Conversation not found'
            )
        
        if request.title is not None:
            conversation.title = request.title
        if request.status is not None:
            conversation.status = request.status

        db.commit()
        db.refresh(conversation)
        return conversation
    except SQLAlchemyError:
        raise HTTPException(
            status_code= HTTP_500_INTERNAL_SERVER_ERROR,
            detail = 'Failed to communicate with DB'
        )
    


@router.delete(
    '/conversation/{id}',
    summary='Deleate a conversation',
    status_code=HTTP_204_NO_CONTENT
)
async def delete_conversation(
    id: UUID,
    user = Depends(get_user_dependency),
    db = Depends(get_db_session)
):
    try:
        conversation =  db.query(Conversation) \
                        .filter(Conversation.id == id, Conversation.owner == user)\
                        .first()
        
        if not conversation:
            raise HTTPException(
                status_code= HTTP_404_NOT_FOUND,
                detail='Conversation not found'
            )
        db.delete(conversation)
        db.commit()

    except SQLAlchemyError:
        raise HTTPException(
            status_code= HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "Failed to communicate with DB"
        )