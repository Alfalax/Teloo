"""
Shared async Redis client singleton for core-api.
"""

import os
import logging
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    """Returns the shared Redis client, initializing it on first call.
    Returns None if Redis is unavailable — callers must handle gracefully."""
    global _client
    if _client is None:
        try:
            url = os.getenv("REDIS_URL", "redis://localhost:6379")
            _client = aioredis.from_url(url, decode_responses=True)
            await _client.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable — token blacklist disabled: {e}")
            _client = None
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
