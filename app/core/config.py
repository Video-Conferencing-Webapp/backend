from typing import List
from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Meet Clone"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./meet_clone.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # TURN server
    TURN_SERVER_URL: str
    TURN_USERNAME: str
    TURN_PASSWORD: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
