from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

class PreferencesBase(BaseModel):
    # Meeting Preferences
    auto_join_audio: Optional[bool] = True
    auto_join_video: Optional[bool] = False
    show_online_status: Optional[bool] = True
    
    # Notification Preferences  
    email_notifications: Optional[bool] = True
    sound_notifications: Optional[bool] = True
    meeting_reminders: Optional[bool] = True
    chat_notifications: Optional[bool] = True
    
    # Privacy Settings
    profile_visibility: Optional[Literal['public', 'private', 'contacts']] = 'public'
    allow_meeting_invites: Optional[bool] = True
    
    # UI Preferences
    theme: Optional[Literal['light', 'dark', 'auto']] = 'light'
    language: Optional[str] = Field('en', max_length=10)
    timezone: Optional[str] = Field('UTC', max_length=50)

class PreferencesUpdate(PreferencesBase):
    """Schema for updating user preferences (partial updates allowed)"""
    pass

class PreferencesResponse(PreferencesBase):
    """Schema for preferences response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CompleteProfileResponse(BaseModel):
    """Schema for complete profile with preferences"""
    # User info
    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Preferences
    preferences: Optional[PreferencesResponse] = None

    class Config:
        from_attributes = True 