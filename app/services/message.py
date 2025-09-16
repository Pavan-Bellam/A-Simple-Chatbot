from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.messages import MessageCreate, MessageRead
from app.models.message import Message
from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND
from uuid import UUID
from typing import List

def create_message(
        db: Session,
        message: MessageCreate
)->MessageRead:
    try:
        new_message = Message(
            conversation_id = message.conversation_id,
            message_count = message.message_count,
            role = message.role,
            content = message.content,
            token_count = message.token_count,
            provider = getattr(message,"provider",None),
            model = getattr(message,"model",None)
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message
    
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=' Failed to Create new message'
        )
    
def get_messages(
        db: Session, 
        conversation_id: UUID,
        skip: int, 
        limit: int
)-> List[MessageRead]:
    try:
            
        messages =  db.query(Message)\
                    .filter(Message.conversation_id == conversation_id)\
                    .offset(skip)\
                    .limit(limit)\
                    .all()
        if not messages:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No messsages for given conversation id"
            )
        return messages
    except SQLAlchemyError:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Unable to get data from DB"
        )
    

def get_k_messages(k: int, conversation_id: UUID, db: Session) -> List[MessageRead]:
    """Return k latest messages in ASC order"""
    messages = db.query(Message)\
               .filter(Message.conversation_id == conversation_id)\
               .order_by(Message.created_at.asc())\
               .limit(k)\
               .all()
    return messages