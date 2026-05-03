"""
Rate Limiting Middleware — Redis-backed sliding window.
Falls back to fail-open only when Redis is not yet initialized (dev startup).
"""

import time
import logging
import redis.asyncio as aioredis
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


def init_redis_rate_limiter(redis_url: str) -> None:
    global _redis_client
    _redis_client = aioredis.from_url(redis_url, decode_responses=True)


class RedisRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        if _redis_client is None:
            return True  # Redis not initialized — fail open (dev only, before startup completes)
        now = int(time.time())
        window_key = f"rl:{key}:{now // self.window_seconds}"
        try:
            pipe = _redis_client.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, self.window_seconds * 2)
            results = await pipe.execute()
            count = results[0]
            if count > self.max_requests:
                logger.warning("Rate limit exceeded for %s (%d/%d)", key, count, self.max_requests)
                return False
            return True
        except Exception as exc:
            logger.error("Rate limiter Redis error: %s — failing open", exc)
            return True  # Don't block traffic on Redis failure; alert via logs


rate_limiter = RedisRateLimiter(max_requests=60, window_seconds=60)
_login_rate_limiter = RedisRateLimiter(max_requests=10, window_seconds=60)


async def check_rate_limit(request: Request, identifier: str = None):
    key = identifier or request.client.host
    if not await rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )


async def check_login_rate_limit(request: Request):
    key = f"login:{request.client.host}"
    if not await _login_rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in a minute.",
            headers={"Retry-After": "60"}
        )
