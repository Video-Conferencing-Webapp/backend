from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional

from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.profile import ProfileUpdate, ChangePasswordRequest
from app.schemas.preferences import PreferencesUpdate
from app.core.security import get_password_hash, verify_password

class ProfileService:
    
    @staticmethod
    async def get_complete_profile(db: AsyncSession, user_id: int) -> User:
        """Get user profile with preferences"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.preferences))
            .filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession, 
        user_id: int, 
        profile_data: ProfileUpdate
    ) -> User:
        """Update user profile information"""
        user = await ProfileService.get_user_by_id(db, user_id)
        
        # Update only provided fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_preferences(db: AsyncSession, user_id: int) -> UserPreferences:
        """Get user preferences, create default if not exists"""
        preferences = await UserPreferences.get_by_user_id(db, user_id)
        
        if not preferences:
            # Create default preferences for user
            preferences = await UserPreferences.create_default_preferences(db, user_id)
        
        return preferences

    @staticmethod
    async def update_preferences(
        db: AsyncSession, 
        user_id: int, 
        preferences_data: PreferencesUpdate
    ) -> UserPreferences:
        """Update user preferences"""
        preferences = await ProfileService.get_user_preferences(db, user_id)
        
        # Update only provided fields
        update_data = preferences_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        await db.commit()
        await db.refresh(preferences)
        return preferences

    @staticmethod
    async def change_password(
        db: AsyncSession, 
        user_id: int, 
        password_data: ChangePasswordRequest
    ) -> bool:
        """Change user password"""
        user = await ProfileService.get_user_by_id(db, user_id)
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        await db.commit()
        return True

    @staticmethod
    async def delete_account(
        db: AsyncSession, 
        user_id: int, 
        password: str
    ) -> bool:
        """Delete user account"""
        user = await ProfileService.get_user_by_id(db, user_id)
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect"
            )
        
        # Delete user (cascade will handle preferences)
        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        """Get user by ID"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    @staticmethod
    async def ensure_user_preferences(db: AsyncSession, user_id: int) -> UserPreferences:
        """Ensure user has preferences, create if not exists"""
        preferences = await UserPreferences.get_by_user_id(db, user_id)
        if not preferences:
            preferences = await UserPreferences.create_default_preferences(db, user_id)
        return preferences 