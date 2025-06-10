from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.websocket import sio
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.core.redis_client import redis_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables and initialize connections
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    
    # Initialize database
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Initialize Redis
    try:
        await redis_client.connect()
        logger.info("Redis connection initialized successfully")
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        # Continue without Redis if it fails (optional, remove raise to continue)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await redis_client.disconnect()
    await engine.dispose()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

# Health check
@app.get("/health")
async def health_check():
    redis_status = await redis_client.ping()
    return {
        "status": "healthy",
        "redis": "connected" if redis_status else "disconnected"
    }

# Export for uvicorn
app = socket_app