from fastapi import APIRouter, Depends
from app.api.deps import get_user_dependency

router = APIRouter()

@router.get('/secure')
async def secure_route(user=Depends(get_user_dependency)):
    return {
            "message" : "Access Granted",
            "user" : {
                user
            }
        }