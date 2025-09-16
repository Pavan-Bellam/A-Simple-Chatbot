from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from uuid import UUID
from typing import List
from app.services.message import get_messages, get_k_messages, create_message
from app.core.settings import settings
from app.schemas.messages import MessageCreate


def get_history(k, db, conversation_id: UUID) ->List[BaseMessage]:
    messages = get_k_messages(k, conversation_id, db)
    token_sum = messages[-1].token_count
    history = []
    for message in messages:
        if message.role.value=='system':
            history.append(SystemMessage(content=message.content))
        if message.role.value=='ai':
            history.append(AIMessage(content=message.content))
        if message.role.value=='user':
            history.append(HumanMessage(content=message.content))
    return history, token_sum

def chat(db,conversation_id: UUID, user_input: str, model: str, provider: str) -> str:
    
    llm = ChatOpenAI(model='gpt-5',api_key=settings.OPENAI_API_KEY)
    history, token_count = get_history(20,db, conversation_id)
    history.append(HumanMessage(content=user_input))

    response = llm.invoke(history)
    
    token_count+=response.response_metadata['token_usage']['prompt_tokens']
    
    user_message = MessageCreate(
        role='user',
        content=user_input,
        token_count=token_count,
        message_count=0,
        conversation_id=conversation_id
    )
    
    token_count+=response.response_metadata['token_usage']['completion_tokens']
    
    response_message = MessageCreate(
        role='ai',
        content=response.content,
        token_count=token_count,
        message_count=0,
        provider=provider,
        model=model,
        conversation_id=conversation_id
    )
    
    create_message(db=db, message=user_message)
    create_message(
        db=db,
        message=response_message
    )
    return response.content

