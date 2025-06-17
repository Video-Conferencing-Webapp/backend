from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import Base

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Meeting Preferences
    auto_join_audio = Column(Boolean, default=True, nullable=False)
    auto_join_video = Column(Boolean, default=False, nullable=False)
    show_online_status = Column(Boolean, default=True, nullable=False)
    
    # Notification Preferences  
    email_notifications = Column(Boolean, default=True, nullable=False)
    sound_notifications = Column(Boolean, default=True, nullable=False)
    meeting_reminders = Column(Boolean, default=True, nullable=False)
    chat_notifications = Column(Boolean, default=True, nullable=False)
    
    # Privacy Settings
    profile_visibility = Column(String(20), default='public', nullable=False)  # 'public', 'private', 'contacts'
    allow_meeting_invites = Column(Boolean, default=True, nullable=False)
    
    # UI Preferences
    theme = Column(String(20), default='light', nullable=False)  # 'light', 'dark', 'auto'
    language = Column(String(10), default='en', nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

    @classmethod
    async def get_by_user_id(cls, db: AsyncSession, user_id: int):
        result = await db.execute(select(cls).filter(cls.user_id == user_id))
        return result.scalar_one_or_none()

    @classmethod
    async def create_default_preferences(cls, db: AsyncSession, user_id: int):
        """Create default preferences for a new user"""
        preferences = cls(user_id=user_id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
        return preferences 