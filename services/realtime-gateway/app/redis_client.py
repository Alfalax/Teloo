"""
Redis client for pub/sub and Socket.IO adapter
"""

import redis.asyncio as redis
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for async operations"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            redis_url = settings.get_redis_url()
            self.client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    
    async def subscribe(self, *channels: str):
        """Subscribe to Redis channels"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        
        self.pubsub = self.client.pubsub()
        await self.pubsub.subscribe(*channels)
        logger.info(f"Subscribed to channels: {', '.join(channels)}")
    
    async def publish(self, channel: str, message: str):
        """Publish message to Redis channel"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        
        await self.client.publish(channel, message)
    
    async def get_message(self, timeout: float = 1.0):
        """Get message from subscribed channels"""
        if not self.pubsub:
            raise RuntimeError("Not subscribed to any channels")
        
        return await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout)


# Global Redis client instance
redis_client = RedisClient()
