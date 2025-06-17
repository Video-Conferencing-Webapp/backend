from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile fields
    phone = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    hosted_rooms = relationship("Room", back_populates="host")
    room_participations = relationship("RoomParticipant", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str):
        result = await db.execute(select(cls).filter(cls.email == email))
        return result.scalar_one_or_none()
