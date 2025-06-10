import redis.asyncio as redis
from typing import Optional
from app.core.config import settings
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self._pool: Optional[redis.ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        self._connection_retries = 3
        self._retry_delay = 1  # seconds
    
    async def _create_pool(self):
        """Create Redis connection pool"""
        try:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                retry_on_timeout=True,
                socket_keepalive=True,
                # socket_keepalive_options={
                #     1: 1,  # TCP_KEEPIDLE
                #     2: 5,  # TCP_KEEPINTVL
                #     3: 5,  # TCP_KEEPCNT
                # }
            )
            self._redis = redis.Redis(connection_pool=self._pool)
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to create Redis pool: {e}")
            raise
    
    async def connect(self):
        """Initialize Redis connection with retry logic"""
        for attempt in range(self._connection_retries):
            try:
                await self._create_pool()
                return
            except Exception as e:
                if attempt < self._connection_retries - 1:
                    logger.warning(f"Redis connection attempt {attempt + 1} failed, retrying in {self._retry_delay}s...")
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(f"Failed to connect to Redis after {self._connection_retries} attempts")
                    raise
    
    async def disconnect(self):
        """Close Redis connection and pool"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        self._redis = None
        self._pool = None
    
    async def _ensure_connected(self):
        """Ensure Redis is connected, reconnect if necessary"""
        if not self._redis:
            await self.connect()
        else:
            try:
                await self._redis.ping()
            except (redis.ConnectionError, redis.TimeoutError):
                logger.warning("Redis connection lost, reconnecting...")
                await self.disconnect()
                await self.connect()
    
    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute Redis operation with automatic retry on connection errors"""
        for attempt in range(self._connection_retries):
            try:
                await self._ensure_connected()
                return await operation(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if attempt < self._connection_retries - 1:
                    logger.warning(f"Redis operation failed (attempt {attempt + 1}), retrying...")
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error(f"Redis operation failed after {self._connection_retries} attempts: {e}")
                    raise
    
    async def get(self, key: str) -> Optional[str]:
        return await self._execute_with_retry(self._redis.get, key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        await self._execute_with_retry(self._redis.set, key, value, ex=expire)
    
    async def delete(self, key: str):
        await self._execute_with_retry(self._redis.delete, key)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        return await self._execute_with_retry(self._redis.hget, name, key)
    
    async def hset(self, name: str, key: str, value: str):
        await self._execute_with_retry(self._redis.hset, name, key, value)
    
    async def hdel(self, name: str, key: str):
        await self._execute_with_retry(self._redis.hdel, name, key)
    
    async def sadd(self, key: str, *values):
        await self._execute_with_retry(self._redis.sadd, key, *values)
    
    async def srem(self, key: str, *values):
        await self._execute_with_retry(self._redis.srem, key, *values)
    
    async def smembers(self, key: str) -> set:
        result = await self._execute_with_retry(self._redis.smembers, key)
        return result if result else set()
    
    async def publish(self, channel: str, message: dict):
        await self._execute_with_retry(self._redis.publish, channel, json.dumps(message))
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            await self._execute_with_retry(self._redis.ping)
            return True
        except Exception:
            return False

redis_client = RedisClient()
