"""
Rate limiting service using Redis
"""

import time
from typing import Optional
import logging
from app.core.redis import redis_manager
from app.core.config import settings
from app.models.whatsapp import RateLimitInfo
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self):
        self.window_size = 60  # 1 minute window
        self.max_requests = settings.rate_limit_per_minute
    
    async def is_rate_limited(self, ip_address: str) -> RateLimitInfo:
        """Check if IP is rate limited"""
        try:
            current_time = int(time.time())
            window_start = current_time - (current_time % self.window_size)
            
            # Redis key for this IP and time window
            key = f"rate_limit:{ip_address}:{window_start}"
            
            # Get current count
            current_count = await redis_manager.get(key)
            request_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            is_limited = request_count >= self.max_requests
            
            if not is_limited:
                # Increment counter
                new_count = await redis_manager.incr(key)
                if new_count == 1:
                    # Set expiration for new key
                    await redis_manager.expire(key, self.window_size)
                request_count = new_count
            
            return RateLimitInfo(
                ip_address=ip_address,
                request_count=request_count,
                window_start=datetime.fromtimestamp(window_start),
                is_limited=is_limited
            )
            
        except Exception as e:
            logger.error(f"Rate limiter error for IP {ip_address}: {e}")
            # On error, allow request (fail open)
            return RateLimitInfo(
                ip_address=ip_address,
                request_count=0,
                window_start=datetime.now(),
                is_limited=False
            )
    
    async def get_rate_limit_status(self, ip_address: str) -> dict:
        """Get current rate limit status for IP"""
        try:
            current_time = int(time.time())
            window_start = current_time - (current_time % self.window_size)
            key = f"rate_limit:{ip_address}:{window_start}"
            
            current_count = await redis_manager.get(key)
            request_count = int(current_count) if current_count else 0
            
            remaining = max(0, self.max_requests - request_count)
            reset_time = window_start + self.window_size
            
            return {
                "limit": self.max_requests,
                "remaining": remaining,
                "reset": reset_time,
                "window_size": self.window_size
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status for IP {ip_address}: {e}")
            return {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset": int(time.time()) + self.window_size,
                "window_size": self.window_size
            }


# Global rate limiter instance
rate_limiter = RateLimiter()