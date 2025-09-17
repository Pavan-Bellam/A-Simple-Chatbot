from uuid import UUID
from typing import List, Tuple

import numpy as np
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sqlalchemy import select
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

from app.core.settings import settings
from app.models.message import Message
from app.models.message_embeddings import MessageEmbedding
from app.schemas.messages import MessageCreate
from app.services.message import create_message, get_k_messages




_EMBED_MODEL_NAME = "intfloat/e5-large"

_embedder = SentenceTransformer(_EMBED_MODEL_NAME)
_tokenizer = AutoTokenizer.from_pretrained(_EMBED_MODEL_NAME)
MAX_LEN = _tokenizer.model_max_length  # 512




def get_history(k, db, conversation_id: UUID) -> List[BaseMessage]:
    """
    Retrieve the latest k messages as LangChain BaseMessage objects.

    Parameters
    ----------
    k : int
        Number of messages to retrieve.
    db : Session
        SQLAlchemy session.
    conversation_id : UUID
        Conversation identifier.

    Returns
    -------
    (history, token_sum)
        history : list of BaseMessage
            Messages in their LangChain forms (SystemMessage, AIMessage, HumanMessage).
        token_sum : int
            Token count carried from the last stored message.

    Notes
    -----
    This function intentionally returns a tuple (history, token_sum).
    """
    messages = get_k_messages(k, conversation_id, db)
    if not messages:
        return [], 0

    token_sum = messages[-1].token_count
    history = []
    for message in messages:
        if message.role.value == "system":
            history.append(SystemMessage(content=message.content))
        if message.role.value == "ai":
            history.append(AIMessage(content=message.content))
        if message.role.value == "user":
            history.append(HumanMessage(content=message.content))
    return history, token_sum



def chunk_text(text: str, max_len: int = MAX_LEN) -> List[str]:
    """
    Tokenize and split text into chunks of size ≤ max_len, then decode back to strings.

    Parameters
    ----------
    text : str
        Input text to chunk.
    max_len : int
        Maximum tokens per chunk.

    Returns
    -------
    List[str]
        Decoded text chunks.
    """
    tokens = _tokenizer.encode(text, add_special_tokens=False)
    chunks = [tokens[i : i + max_len] for i in range(0, len(tokens), max_len)]
    return [_tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks]


def get_embeddings(text: str) -> List[Tuple[str, List[float]]]:
    """
    Split long text into ≤512-token chunks, embed each, and return list of (chunk_text, embedding).

    Parameters
    ----------
    text : str
        Text to embed.

    Returns
    -------
    List[Tuple[str, List[float]]]
        Each item is (chunk_text, embedding_vector_as_list).
    """
    chunks = chunk_text(text)
    embeddings = _embedder.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    results: List[Tuple[str, List[float]]] = []
    for chunk, vec in zip(chunks, embeddings):
        results.append((chunk, vec.astype(np.float32).tolist()))
    return results



def store_message(db, message_in: MessageCreate) -> Message:
    """
    Persist a message and store its chunked embeddings.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    message_in : MessageCreate
        Incoming message payload.

    Returns
    -------
    Message
        The newly stored Message with embeddings persisted.
    """
    msg: Message = create_message(db=db, message=message_in)
    embeddings = get_embeddings(msg.content)
    for idx, (chunk_text_value, vec) in enumerate(embeddings):
        msg.embeddings.append(
            MessageEmbedding(
                chunk_index=idx,
                text_chunk=chunk_text_value,
                embedding=vec,
            )
        )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg



def retrieve_relevant_context(db, query: str, top_k: int = 5) -> SystemMessage | None:
    """
    Retrieve top_k most relevant messages for a query using cosine distance over stored embeddings.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    query : str
        Search query string.
    top_k : int
        Number of results to retrieve.

    Returns
    -------
    HumanMessage | None
        A constructed HumanMessage containing retrieved context lines, or None if no rows.
    """
    query_vec = _embedder.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0].astype(np.float32)

    stmt = (
        select(
            Message.role,
            Message.content,
            MessageEmbedding.embedding.cosine_distance(query_vec).label("distance"),
        )
        .join(MessageEmbedding, Message.id == MessageEmbedding.message_id)
        .order_by("distance")
        .limit(top_k)
    )

    rows = db.execute(stmt).all()
    if not rows:
        return None

    context_texts = "\n".join(
        [
            f"- {row.role.value if hasattr(row.role, 'value') else row.role}: {row.content}"
            for row in rows
        ]
    )
    return HumanMessage(content=f"[Retrieved context from memory]\n{context_texts}")




def chat(db, conversation_id: UUID, user_input: str, model: str, provider: str) -> str:
    """
    Run a chat turn with retrieved history and context, then persist both user and AI messages.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    conversation_id : UUID
        Conversation identifier.
    user_input : str
        The user's input message content.
    model : str
        Model identifier for bookkeeping.
    provider : str
        Provider identifier for bookkeeping.

    Returns
    -------
    str
        The AI response content.
    """
    llm = ChatOpenAI(model="gpt-5", api_key=settings.OPENAI_API_KEY)

    history, token_count = get_history(20, db, conversation_id)
    context_message = retrieve_relevant_context(db, user_input, top_k=5)
    if context_message:
        history.append(context_message)

    history.append(HumanMessage(content=user_input))
    print(history)

    response = llm.invoke(history)

    token_count += response.response_metadata["token_usage"]["prompt_tokens"]

    user_message = MessageCreate(
        role="user",
        content=user_input,
        token_count=token_count,
        message_count=0,
        conversation_id=conversation_id,
    )

    token_count += response.response_metadata["token_usage"]["completion_tokens"]

    response_message = MessageCreate(
        role="ai",
        content=response.content,
        token_count=token_count,
        message_count=0,
        provider=provider,
        model=model,
        conversation_id=conversation_id,
    )

    store_message(db=db, message_in=user_message)
    store_message(db=db, message_in=response_message)

    return response.content
