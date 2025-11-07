"""
Concurrencia Service for TeLOO V3
Handles distributed locks and concurrency control using Redis
"""

import logging
from typing import Optional, AsyncContextManager, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import time
import uuid

logger = logging.getLogger(__name__)


class ConcurrenciaService:
    """Service for managing concurrency and distributed locks"""
    
    # Lock configuration
    EVALUATION_LOCK_TTL = 300  # 5 minutes TTL for evaluation locks
    LOCK_RETRY_DELAY = 0.1  # 100ms between lock acquisition attempts
    LOCK_MAX_RETRIES = 50  # Maximum retries for lock acquisition
    
    @staticmethod
    async def is_evaluacion_en_progreso(solicitud_id: str, redis_client=None) -> bool:
        """
        Check if evaluation is currently in progress for a solicitud
        
        Args:
            solicitud_id: ID of the solicitud to check
            redis_client: Redis client (optional, will use default if None)
            
        Returns:
            bool: True if evaluation is in progress, False otherwise
        """
        try:
            if redis_client is None:
                # TODO: Get Redis client from dependency injection
                # For now, return False to allow evaluation (will be fixed when Redis is set up)
                logger.warning("Redis client not available, skipping concurrency check")
                return False
            
            lock_key = f"evaluation_lock:{solicitud_id}"
            
            # Check if lock exists
            lock_exists = await redis_client.exists(lock_key)
            
            if lock_exists:
                # Get lock metadata to check if it's still valid
                lock_data = await redis_client.get(lock_key)
                if lock_data:
                    logger.info(f"Evaluación en progreso para solicitud {solicitud_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando evaluación en progreso: {e}")
            # In case of Redis error, allow evaluation to proceed
            return False
    
    @staticmethod
    @asynccontextmanager
    async def lock_evaluacion(
        solicitud_id: str, 
        redis_client=None,
        ttl_seconds: Optional[int] = None
    ) -> AsyncContextManager[str]:
        """
        Acquire distributed lock for evaluation
        
        Args:
            solicitud_id: ID of the solicitud to lock
            redis_client: Redis client (optional)
            ttl_seconds: Lock TTL in seconds (uses default if None)
            
        Yields:
            str: Lock token for the acquired lock
            
        Raises:
            RuntimeError: If lock cannot be acquired
        """
        if redis_client is None:
            # TODO: Get Redis client from dependency injection
            # For now, yield a dummy token (will be fixed when Redis is set up)
            logger.warning("Redis client not available, using dummy lock")
            yield "dummy_lock_token"
            return
        
        if ttl_seconds is None:
            ttl_seconds = ConcurrenciaService.EVALUATION_LOCK_TTL
        
        lock_key = f"evaluation_lock:{solicitud_id}"
        lock_token = str(uuid.uuid4())
        
        # Try to acquire lock
        acquired = False
        retries = 0
        
        while not acquired and retries < ConcurrenciaService.LOCK_MAX_RETRIES:
            try:
                # Use SET with NX (only if not exists) and EX (expiration)
                result = await redis_client.set(
                    lock_key,
                    lock_token,
                    nx=True,  # Only set if key doesn't exist
                    ex=ttl_seconds  # Set expiration
                )
                
                if result:
                    acquired = True
                    logger.info(
                        f"Lock adquirido para evaluación de solicitud {solicitud_id} "
                        f"(token: {lock_token[:8]}..., TTL: {ttl_seconds}s)"
                    )
                    break
                else:
                    # Lock is held by someone else, wait and retry
                    retries += 1
                    if retries < ConcurrenciaService.LOCK_MAX_RETRIES:
                        await asyncio.sleep(ConcurrenciaService.LOCK_RETRY_DELAY)
                    
            except Exception as e:
                logger.error(f"Error adquiriendo lock de evaluación: {e}")
                retries += 1
                if retries < ConcurrenciaService.LOCK_MAX_RETRIES:
                    await asyncio.sleep(ConcurrenciaService.LOCK_RETRY_DELAY)
        
        if not acquired:
            raise RuntimeError(
                f"No se pudo adquirir lock para evaluación de solicitud {solicitud_id} "
                f"después de {ConcurrenciaService.LOCK_MAX_RETRIES} intentos"
            )
        
        try:
            # Yield the lock token
            yield lock_token
            
        finally:
            # Release lock using Lua script to ensure atomicity
            # Only release if we still own the lock (token matches)
            try:
                lua_script = """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("DEL", KEYS[1])
                else
                    return 0
                end
                """
                
                result = await redis_client.eval(lua_script, 1, lock_key, lock_token)
                
                if result == 1:
                    logger.info(f"Lock liberado para solicitud {solicitud_id}")
                else:
                    logger.warning(
                        f"Lock para solicitud {solicitud_id} ya había expirado o fue liberado"
                    )
                    
            except Exception as e:
                logger.error(f"Error liberando lock de evaluación: {e}")
    
    @staticmethod
    async def validar_oferta_concurrencia(
        solicitud_id: str,
        redis_client=None
    ) -> Dict[str, Any]:
        """
        Validate that an offer can be created (no evaluation in progress)
        
        Args:
            solicitud_id: ID of the solicitud
            redis_client: Redis client (optional)
            
        Returns:
            Dict with validation result
            
        Raises:
            ValueError: If offer cannot be created due to concurrent evaluation
        """
        try:
            # Check if evaluation is in progress
            evaluacion_en_progreso = await ConcurrenciaService.is_evaluacion_en_progreso(
                solicitud_id, redis_client
            )
            
            if evaluacion_en_progreso:
                raise ValueError(
                    f"No se puede crear oferta para solicitud {solicitud_id}: "
                    "evaluación en progreso"
                )
            
            return {
                'valid': True,
                'solicitud_id': solicitud_id,
                'evaluacion_en_progreso': False,
                'message': 'Oferta puede ser creada'
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error validando concurrencia para oferta: {e}")
            # In case of error, allow offer creation (fail-open approach)
            return {
                'valid': True,
                'solicitud_id': solicitud_id,
                'evaluacion_en_progreso': False,
                'warning': f'Error verificando concurrencia: {str(e)}',
                'message': 'Oferta puede ser creada (verificación de concurrencia falló)'
            }
    
    @staticmethod
    async def get_lock_info(solicitud_id: str, redis_client=None) -> Optional[Dict[str, Any]]:
        """
        Get information about evaluation lock for a solicitud
        
        Args:
            solicitud_id: ID of the solicitud
            redis_client: Redis client (optional)
            
        Returns:
            Dict with lock information or None if no lock exists
        """
        try:
            if redis_client is None:
                logger.warning("Redis client not available, cannot get lock info")
                return None
            
            lock_key = f"evaluation_lock:{solicitud_id}"
            
            # Get lock data and TTL
            lock_data = await redis_client.get(lock_key)
            if not lock_data:
                return None
            
            ttl = await redis_client.ttl(lock_key)
            
            return {
                'solicitud_id': solicitud_id,
                'lock_key': lock_key,
                'lock_token': lock_data[:8] + "..." if len(lock_data) > 8 else lock_data,
                'ttl_seconds': ttl,
                'expires_at': time.time() + ttl if ttl > 0 else None,
                'is_active': ttl > 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de lock: {e}")
            return None
    
    @staticmethod
    async def force_release_lock(
        solicitud_id: str,
        redis_client=None,
        reason: str = "manual_release"
    ) -> Dict[str, Any]:
        """
        Force release evaluation lock (admin function)
        
        Args:
            solicitud_id: ID of the solicitud
            redis_client: Redis client (optional)
            reason: Reason for force release
            
        Returns:
            Dict with release result
        """
        try:
            if redis_client is None:
                logger.warning("Redis client not available, cannot force release lock")
                return {
                    'success': False,
                    'message': 'Redis client not available'
                }
            
            lock_key = f"evaluation_lock:{solicitud_id}"
            
            # Get current lock info before deleting
            lock_info = await ConcurrenciaService.get_lock_info(solicitud_id, redis_client)
            
            # Force delete the lock
            result = await redis_client.delete(lock_key)
            
            if result > 0:
                logger.warning(
                    f"Lock forzadamente liberado para solicitud {solicitud_id} "
                    f"por razón: {reason}"
                )
                return {
                    'success': True,
                    'solicitud_id': solicitud_id,
                    'reason': reason,
                    'previous_lock_info': lock_info,
                    'message': f'Lock liberado forzadamente: {reason}'
                }
            else:
                return {
                    'success': False,
                    'solicitud_id': solicitud_id,
                    'message': 'No había lock activo para liberar'
                }
                
        except Exception as e:
            logger.error(f"Error liberando lock forzadamente: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Error liberando lock: {str(e)}'
            }