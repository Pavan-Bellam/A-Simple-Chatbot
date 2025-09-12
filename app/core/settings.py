from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    database_url: PostgresDsn
    cognito_region: str
    cognito_user_pool_id: str
    cognito_app_client_secret: str
    cognito_app_client_id: str
    
    @property
    def jwks_url(self) -> str:
        return  f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json"
    
    
    @property
    def issuer(self)->str:
        return  f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()