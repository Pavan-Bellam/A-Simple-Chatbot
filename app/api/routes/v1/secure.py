from fastapi import APIRouter, Depends
from app.services.auth import jwt_dependency


router = APIRouter()

@router.get('/secure')
async def secure_route(payload=Depends(jwt_dependency)):
    return {
            "message" : "Access Granted",
            "user_sub": payload['sub']
        }