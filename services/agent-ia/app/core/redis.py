"""
Redis connection and utilities
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_pool_size
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.redis_client:
            logger.warning(f"Redis not connected, cannot GET key {key}")
            return None
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        if not self.redis_client:
            logger.warning(f"Redis not connected, cannot SET key {key}")
            return False
        try:
            if ttl:
                return await self.redis_client.setex(key, ttl, value)
            else:
                return await self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis_client:
            logger.warning(f"Redis not connected, cannot DELETE key {key}")
            return False
        try:
            return bool(await self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in Redis"""
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        try:
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def publish(self, channel: str, message: dict) -> bool:
        """Publish message to Redis channel"""
        try:
            await self.redis_client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Redis PUBLISH error for channel {channel}: {e}")
            return False
    
    async def lpush(self, key: str, value: str) -> Optional[int]:
        """Push value to left of list"""
        try:
            return await self.redis_client.lpush(key, value)
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return None
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop value from right of list"""
        try:
            return await self.redis_client.rpop(key)
        except Exception as e:
            logger.error(f"Redis RPOP error for key {key}: {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Get length of list"""
        try:
            return await self.redis_client.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN error for key {key}: {e}")
            return 0
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET_JSON error for key {key}: {e}")
            return None
    
    async def set_json(self, key: str, value: dict, ttl: Optional[int] = None) -> bool:
        """Set JSON value in Redis with optional TTL"""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            logger.error(f"Redis SET_JSON error for key {key}: {e}")
            return False


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    if not redis_manager.redis_client:
        await redis_manager.connect()
    return redis_manager.redis_client