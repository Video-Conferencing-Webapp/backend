from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.profile import (
    ProfileUpdate, 
    ProfileResponse, 
    ChangePasswordRequest, 
    DeleteAccountRequest
)
from app.schemas.preferences import (
    PreferencesUpdate, 
    PreferencesResponse, 
    CompleteProfileResponse
)
from app.services.profile_service import ProfileService

router = APIRouter()

@router.get("/me", response_model=CompleteProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's complete profile with preferences.
    """
    user_with_preferences = await ProfileService.get_complete_profile(db, current_user.id)
    return user_with_preferences

@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.
    """
    updated_user = await ProfileService.update_profile(db, current_user.id, profile_data)
    return updated_user

@router.get("/preferences", response_model=PreferencesResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's preferences.
    """
    preferences = await ProfileService.get_user_preferences(db, current_user.id)
    return preferences

@router.put("/preferences", response_model=PreferencesResponse)
async def update_my_preferences(
    preferences_data: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's preferences.
    """
    updated_preferences = await ProfileService.update_preferences(
        db, current_user.id, preferences_data
    )
    return updated_preferences

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password.
    """
    success = await ProfileService.change_password(db, current_user.id, password_data)
    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.delete("/me")
async def delete_my_account(
    delete_data: DeleteAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's account.
    """
    success = await ProfileService.delete_account(db, current_user.id, delete_data.password)
    if success:
        return {"message": "Account deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        ) 