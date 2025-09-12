from app.models.user import User
from app.db.engine import SessionLocal

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


