from pydantic import BaseModel
from .user import User

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenResponse(Token):
    user: User

class TokenPayload(BaseModel):
    sub: str | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str 