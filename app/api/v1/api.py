from fastapi import APIRouter
from app.api.v1.endpoints import room, auth, profile

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(room.router, prefix="/rooms", tags=["rooms"])
