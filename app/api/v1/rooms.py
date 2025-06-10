from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.room import Room, RoomParticipant
from app.schemas.room import RoomCreate, RoomResponse, RoomJoin
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/create", response_model=RoomResponse)
async def create_room(
    room_data: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new room"""
    room = Room(
        name=room_data.name,
        host_id=current_user.id,
        max_participants=room_data.max_participants
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    
    return room

@router.post("/join/{room_code}")
async def join_room(
    room_code: str,
    join_data: RoomJoin,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a room"""
    # Find room
    result = await db.execute(
        select(Room).where(Room.code == room_code)
    )
    room = result.scalar_one_or_none()
    
    if not room or not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found or inactive"
        )
    
    # Check if already in room
    existing = await db.execute(
        select(RoomParticipant).where(
            (RoomParticipant.room_id == room.id) &
            (RoomParticipant.user_id == current_user.id) &
            (RoomParticipant.left_at == None)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already in room"
        )
    
    # Add participant
    participant = RoomParticipant(
        room_id=room.id,
        user_id=current_user.id,
        peer_id=join_data.peer_id
    )
    db.add(participant)
    await db.commit()
    
    return {
        "room_id": room.id,
        "room_name": room.name,
        "is_host": room.host_id == current_user.id
    }

@router.get("/active", response_model=List[RoomResponse])
async def get_active_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's active rooms"""
    result = await db.execute(
        select(Room).where(
            (Room.host_id == current_user.id) & 
            (Room.is_active == True)
        )
    )
    return result.scalars().all()
