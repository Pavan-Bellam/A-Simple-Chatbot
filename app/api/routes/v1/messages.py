from fastapi import APIRouter, Depends, Query, HTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_204_NO_CONTENT
from typing import List, Annotated
from uuid import UUID
from app.api.deps import get_db_session, get_user_dependency
from app.schemas.messages import MessageCreate, MessageRead, GetMessageRequest
from app.models.message import Message
from app.services.message import create_message as create_message_service, get_messages as get_message_service
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

@router.post(
    '/message',
    summary = "Insert a message into messages table",
    response_model = MessageRead,
    status_code= HTTP_201_CREATED
)
async def create_message(
        request: MessageCreate,
        user = Depends(get_user_dependency),
        db = Depends(get_db_session)
):
    return create_message_service(db, request)

@router.get(
    '/message',
    summary='get top `k` messages',
    response_model=List[MessageRead],
    status_code=HTTP_200_OK
)
async def get_messages(
    request: GetMessageRequest,
    skip: Annotated[int, Query(ge=0,description='Number of records to skip')]=0,
    limit: Annotated[int, Query(ge=1,le=100, description='Maximum number of records to return')] = 10,
    user = Depends(get_user_dependency),
    db = Depends(get_db_session)
):
    return get_message_service(db, request.conversation_id, skip, limit)

@router.delete(
    'message/{conversation_id}/{message_id}',
    summary= 'Delete a message',
    status_code=HTTP_204_NO_CONTENT
)
async def delete_message(
    conversation_id: UUID,
    message_id: UUID,
    user = Depends(get_user_dependency),
    db = Depends(get_db_session)
):
    try:
        message = db.query(Message)\
                  .filter(Message.conversation_id == conversation_id, Message.id == message_id) \
                  .first()
        if not message:
            return HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail= "No message with given id in given conversation id"
            )
        db.delete(message)
        db.commit()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail= 'DB error'
        )