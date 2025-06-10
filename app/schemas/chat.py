from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ChatMessage(BaseModel):
    id: str
    room_id: str
    user_id: str
    user_name: str
    message: str = Field(..., min_length=1, max_length=1000)
    timestamp: datetime
    
class ChatMessageCreate(BaseModel):
    room_id: str
    message: str = Field(..., min_length=1, max_length=1000)

class ChatMessageResponse(ChatMessage):
    class Config:
        from_attributes = True
