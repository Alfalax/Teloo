"""
Redis configuration for Analytics Service
"""
import redis.asyncio as redis
import json
from typing import Any, Dict, Optional
from app.core.config import settings

class RedisManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
    
    async def connect(self):
        """Connect to Redis"""
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Log connection attempt (masking password)
            masked_url = settings.REDIS_URL
            if ":" in masked_url and "@" in masked_url:
                try:
                    # simplistic masking
                    prefix = masked_url.split("@")[0]
                    suffix = masked_url.split("@")[1]
                    if ":" in prefix:
                        scheme_user = prefix.split(":")[0] + ":" + prefix.split(":")[1]
                        masked_url = f"{scheme_user}:****@{suffix}"
                except:
                    pass
            logger.info(f"Attempting to connect to Redis at: {masked_url}")

            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data"""
        if not self.redis_client:
            return None
            
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_cache(self, key: str, data: Dict[str, Any], ttl: int = None):
        """Set cached data"""
        if not self.redis_client:
            return
            
        ttl = ttl or settings.METRICS_CACHE_TTL
        await self.redis_client.setex(
            key, 
            ttl, 
            json.dumps(data, default=str)
        )
    
    async def subscribe_to_events(self):
        """Subscribe to Redis pub/sub events"""
        if not self.redis_client:
            await self.connect()
            
        self.pubsub = self.redis_client.pubsub()
        
        # Suscribirse a todos los eventos del sistema
        await self.pubsub.psubscribe("teloo:events:*")
        
        return self.pubsub
    
    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to Redis"""
        if not self.redis_client:
            return
            
        channel = f"teloo:events:{event_type}"
        await self.redis_client.publish(
            channel,
            json.dumps(data, default=str)
        )

# Global Redis manager instance
redis_manager = RedisManager()