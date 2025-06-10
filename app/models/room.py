from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import secrets

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, index=True, 
                  default=lambda: secrets.token_urlsafe(8))
    name = Column(String, nullable=False)
    host_id = Column(String, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    host = relationship("User", backref="hosted_rooms")
    participants = relationship("RoomParticipant", back_populates="room")

class RoomParticipant(Base):
    __tablename__ = "room_participants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("rooms.id"))
    user_id = Column(String, ForeignKey("users.id"))
    peer_id = Column(String, unique=True)  # WebRTC peer ID
    is_presenter = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    room = relationship("Room", back_populates="participants")
    user = relationship("User")
