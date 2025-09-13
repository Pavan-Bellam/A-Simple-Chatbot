from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from app.services.auth import jwt_service
from app.services.user import get_user_by_sub
from fastapi import Depends

async def jwt_dependency(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail = 'Missing or Invalid Authorization Header'
        )
    
    token = auth_header.split(" ")[1]
    payload = jwt_service.verify_token(token)
    return payload['sub']

async def get_user_dependency(sub: str = Depends(jwt_dependency)):
    user = get_user_by_sub(sub)
    return user
    