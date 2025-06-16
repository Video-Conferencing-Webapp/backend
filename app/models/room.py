from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import secrets

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, index=True, 
                  default=lambda: secrets.token_urlsafe(8))
    name = Column(String(100), nullable=False)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer, default=100)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    host = relationship("User", back_populates="hosted_rooms")
    participants = relationship("RoomParticipant", back_populates="room")

class RoomParticipant(Base):
    __tablename__ = "room_participants"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    peer_id = Column(String, unique=True)  # WebRTC peer ID
    is_presenter = Column(Boolean, default=False)
    joined_at = Column(DateTime, server_default=func.now())
    left_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="room_participations")
    room = relationship("Room", back_populates="participants")
