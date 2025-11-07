"""
Circuit breaker for LLM providers
"""

import time
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta

from app.models.llm import CircuitBreakerState, CircuitBreakerInfo
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker implementation for LLM providers"""
    
    def __init__(self, provider_name: str, failure_threshold: int = 3, timeout_seconds: int = 300):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.redis_key = f"circuit_breaker:{provider_name}"
    
    async def get_state(self) -> CircuitBreakerInfo:
        """Get current circuit breaker state"""
        try:
            data = await redis_manager.get(self.redis_key)
            if not data:
                # Initialize circuit breaker
                info = CircuitBreakerInfo(
                    provider=self.provider_name,
                    state=CircuitBreakerState.CLOSED,
                    failure_count=0
                )
                await self._save_state(info)
                return info
            
            import json
            state_data = json.loads(data)
            
            return CircuitBreakerInfo(
                provider=self.provider_name,
                state=CircuitBreakerState(state_data["state"]),
                failure_count=state_data["failure_count"],
                last_failure_time=datetime.fromisoformat(state_data["last_failure_time"]) if state_data.get("last_failure_time") else None,
                next_attempt_time=datetime.fromisoformat(state_data["next_attempt_time"]) if state_data.get("next_attempt_time") else None
            )
            
        except Exception as e:
            logger.error(f"Error getting circuit breaker state for {self.provider_name}: {e}")
            # Return safe default
            return CircuitBreakerInfo(
                provider=self.provider_name,
                state=CircuitBreakerState.CLOSED,
                failure_count=0
            )
    
    async def _save_state(self, info: CircuitBreakerInfo):
        """Save circuit breaker state to Redis"""
        try:
            import json
            state_data = {
                "state": info.state.value,
                "failure_count": info.failure_count,
                "last_failure_time": info.last_failure_time.isoformat() if info.last_failure_time else None,
                "next_attempt_time": info.next_attempt_time.isoformat() if info.next_attempt_time else None
            }
            
            # Save with TTL to prevent stale data
            await redis_manager.set(
                self.redis_key, 
                json.dumps(state_data), 
                ttl=self.timeout_seconds * 2
            )
            
        except Exception as e:
            logger.error(f"Error saving circuit breaker state for {self.provider_name}: {e}")
    
    async def is_available(self) -> bool:
        """Check if provider is available (circuit breaker allows calls)"""
        info = await self.get_state()
        
        if info.state == CircuitBreakerState.CLOSED:
            return True
        elif info.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if info.next_attempt_time and datetime.now() >= info.next_attempt_time:
                # Move to half-open state
                info.state = CircuitBreakerState.HALF_OPEN
                await self._save_state(info)
                return True
            return False
        elif info.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    async def record_success(self):
        """Record successful call"""
        info = await self.get_state()
        
        if info.state == CircuitBreakerState.HALF_OPEN:
            # Reset circuit breaker
            info.state = CircuitBreakerState.CLOSED
            info.failure_count = 0
            info.last_failure_time = None
            info.next_attempt_time = None
            await self._save_state(info)
            logger.info(f"Circuit breaker for {self.provider_name} reset to CLOSED")
        elif info.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            if info.failure_count > 0:
                info.failure_count = 0
                await self._save_state(info)
    
    async def record_failure(self):
        """Record failed call"""
        info = await self.get_state()
        info.failure_count += 1
        info.last_failure_time = datetime.now()
        
        if info.failure_count >= self.failure_threshold:
            # Open circuit breaker
            info.state = CircuitBreakerState.OPEN
            info.next_attempt_time = datetime.now() + timedelta(seconds=self.timeout_seconds)
            logger.warning(f"Circuit breaker for {self.provider_name} opened after {info.failure_count} failures")
        
        await self._save_state(info)
    
    async def call_with_circuit_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not await self.is_available():
            from .base_adapter import ProviderUnavailableError
            raise ProviderUnavailableError(f"Circuit breaker is OPEN for {self.provider_name}")
        
        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise e


class CircuitBreakerManager:
    """Manager for all circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, provider_name: str, failure_threshold: int = 3, timeout_seconds: int = 300) -> CircuitBreaker:
        """Get or create circuit breaker for provider"""
        if provider_name not in self.circuit_breakers:
            self.circuit_breakers[provider_name] = CircuitBreaker(
                provider_name=provider_name,
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds
            )
        return self.circuit_breakers[provider_name]
    
    async def get_all_states(self) -> Dict[str, CircuitBreakerInfo]:
        """Get states of all circuit breakers"""
        states = {}
        for provider_name, breaker in self.circuit_breakers.items():
            states[provider_name] = await breaker.get_state()
        return states
    
    async def reset_circuit_breaker(self, provider_name: str) -> bool:
        """Manually reset circuit breaker"""
        if provider_name in self.circuit_breakers:
            breaker = self.circuit_breakers[provider_name]
            info = await breaker.get_state()
            info.state = CircuitBreakerState.CLOSED
            info.failure_count = 0
            info.last_failure_time = None
            info.next_attempt_time = None
            await breaker._save_state(info)
            logger.info(f"Circuit breaker for {provider_name} manually reset")
            return True
        return False


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()