import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.settings import settings

engine = create_engine(
    str(settings.database_url),
    pool_pre_ping= True,
    future = True,
)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush=False,
    autocommit= False,
    expire_on_commit=True,
    class_=Session
)

#dependency for FastAPI routes
def get_session() -> Generator[Session, None, None]:
    """
    Yileds a database session for a request
    ensures the session is closed after the request ends 
    """
    db = SessionLocal()
    try:
        yield db
    except:  # rollback if exception happened
        db.rollback()
        raise
    finally:
        db.close()