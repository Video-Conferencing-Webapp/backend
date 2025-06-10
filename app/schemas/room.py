from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    max_participants: int = Field(default=100, ge=2, le=1000)

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    max_participants: Optional[int] = Field(None, ge=2, le=1000)
    is_active: Optional[bool] = None

class RoomResponse(RoomBase):
    id: str
    code: str
    host_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RoomJoin(BaseModel):
    peer_id: str = Field(..., min_length=1)

class ParticipantResponse(BaseModel):
    id: str
    user_id: str
    peer_id: str
    is_presenter: bool
    joined_at: datetime
    left_at: Optional[datetime]
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

class RoomDetailResponse(RoomResponse):
    participants: List[ParticipantResponse] = []
    participant_count: int = 0
