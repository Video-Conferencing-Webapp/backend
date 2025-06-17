from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)

class ProfileUpdate(ProfileBase):
    """Schema for updating profile information"""
    pass

class ProfileResponse(ProfileBase):
    """Schema for profile response"""
    id: int
    email: EmailStr
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1)
    confirmation: str = Field(..., pattern=r'^DELETE$')

    @validator('confirmation')
    def validate_confirmation(cls, v):
        if v != 'DELETE':
            raise ValueError('Must type "DELETE" to confirm account deletion')
        return v 