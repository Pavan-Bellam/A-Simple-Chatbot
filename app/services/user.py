from app.models.user import User
from app.db.engine import SessionLocal
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
from fastapi import HTTPException

def create_user(user: dict[str, str]) -> None:
    """Create a new user in the database."""
    db = SessionLocal()
    try:
        new_user = User(
            cognito_sub = user['sub'],
            email = user.get('email'),
            first_name = user.get('first_name'),
            last_name = user.get('last_name')
        )
        db.add(new_user)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_user_by_sub(sub: str) -> User | None:
    """Retrieve a user from the database by their Cognito sub."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.cognito_sub == sub).first()
        
        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        db.close()


