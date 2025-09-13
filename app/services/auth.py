import jwt
from jwt import PyJWKClient
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.settings import settings


class JWTService:
    def __init__(self):
        self.jwk_client = PyJWKClient(settings.jwks_url)

    def verify_token(self, token: str):
        try: 
            signing_key = self.jwk_client.get_signing_key_from_jwt(token).key
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                issuer = settings.issuer,
                options = {
                    "require" : ['exp', 'sub', 'iss', 'token_use']
                },
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail = 'Token Expired')
        except jwt.InvalidKeyError as e:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")



jwt_service = JWTService()

