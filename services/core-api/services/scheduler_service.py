"""
Scheduler Service for TeLOO V3
Handles background jobs and scheduled tasks
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import asyncio
import redis.asyncio as redis

from services.ofertas_service import OfertasService
from services.configuracion_service import ConfiguracionService

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing scheduled background jobs
    """
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.redis_client: Optional[redis.Redis] = None
        self._is_running = False
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize the scheduler with job stores and executors
        
        Args:
            redis_url: Redis connection URL
        """
        try:
            # Initialize Redis client
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Configure scheduler
            jobstores = {
                'default': MemoryJobStore()
            }
            
            executors = {
                'default': AsyncIOExecutor()
            }
            
            job_defaults = {
                'coalesce': False,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5 minutes
            }
            
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='America/Bogota'
            )
            
            # Add scheduled jobs
            await self._setup_scheduled_jobs()
            
            logger.info("Scheduler service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing scheduler service: {e}")
            raise
    
    async def start(self):
        """Start the scheduler"""
        if self.scheduler and not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Scheduler started")
    
    async def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler and self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Scheduler shutdown")
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def _setup_scheduled_jobs(self):
        """Setup all scheduled jobs"""
        
        # Job 1: Process offer expiration every hour
        self.scheduler.add_job(
            func=self._procesar_expiracion_ofertas,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id='procesar_expiracion_ofertas',
            name='Procesar expiración de ofertas',
            replace_existing=True
        )
        
        # Job 2: Send expiration warnings every 30 minutes
        self.scheduler.add_job(
            func=self._enviar_advertencias_expiracion,
            trigger=IntervalTrigger(minutes=30),
            id='advertencias_expiracion',
            name='Enviar advertencias de expiración',
            replace_existing=True
        )
        
        # Job 3: Cleanup expired notifications daily at 2 AM
        self.scheduler.add_job(
            func=self._limpiar_notificaciones_expiradas,
            trigger=CronTrigger(hour=2, minute=0),
            id='limpiar_notificaciones',
            name='Limpiar notificaciones expiradas',
            replace_existing=True
        )
        
        logger.info("Scheduled jobs configured")
    
    async def _procesar_expiracion_ofertas(self):
        """
        Process offer expiration - runs every hour
        Marks offers as expired after configured timeout
        """
        try:
            from jobs.scheduled_jobs import procesar_expiracion_ofertas
            result = await procesar_expiracion_ofertas(redis_client=self.redis_client)
            
            if result['success']:
                logger.info(f"Job expiración completado: {result['ofertas_procesadas']} ofertas procesadas")
            else:
                logger.error(f"Job expiración falló: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error ejecutando job de expiración: {e}")
    
    async def _enviar_advertencias_expiracion(self):
        """
        Send expiration warnings to clients
        Runs every 30 minutes to check for offers expiring soon
        """
        try:
            from jobs.scheduled_jobs import enviar_notificaciones_expiracion
            result = await enviar_notificaciones_expiracion(redis_client=self.redis_client)
            
            if result['success']:
                logger.info(f"Job notificaciones completado: {result['notificaciones_enviadas']} notificaciones enviadas")
            else:
                logger.error(f"Job notificaciones falló: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error ejecutando job de notificaciones: {e}")
    

    
    async def _limpiar_notificaciones_expiradas(self):
        """
        Clean up expired notification tracking keys and temporary data
        Runs daily at 2 AM
        """
        try:
            from jobs.scheduled_jobs import limpiar_datos_temporales
            result = await limpiar_datos_temporales()
            
            if result['success']:
                logger.info(f"Job limpieza completado: {result['items_eliminados']} elementos eliminados")
            else:
                logger.error(f"Job limpieza falló: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error ejecutando job de limpieza: {e}")
    
    def get_job_status(self) -> dict:
        """Get status of all scheduled jobs"""
        if not self.scheduler:
            return {'status': 'not_initialized', 'jobs': []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'status': 'running' if self._is_running else 'stopped',
            'jobs': jobs
        }
    
    async def trigger_job_manually(self, job_id: str) -> dict:
        """
        Manually trigger a scheduled job
        
        Args:
            job_id: ID of the job to trigger
            
        Returns:
            Dict with execution result
        """
        if not self.scheduler:
            raise ValueError("Scheduler not initialized")
        
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Import and run the job function directly
            from jobs.scheduled_jobs import ejecutar_job_manual
            
            # Map job IDs to function names
            job_mapping = {
                'procesar_expiracion_ofertas': 'procesar_expiracion_ofertas',
                'advertencias_expiracion': 'enviar_notificaciones_expiracion',
                'limpiar_notificaciones': 'limpiar_datos_temporales'
            }
            
            if job_id not in job_mapping:
                raise ValueError(f"Unknown job ID: {job_id}")
            
            # Execute the job
            result = await ejecutar_job_manual(
                job_mapping[job_id],
                redis_client=self.redis_client
            )
            
            return {
                'success': result['success'],
                'job_id': job_id,
                'executed_at': datetime.now().isoformat(),
                'result': result,
                'message': f'Job {job_id} executed {"successfully" if result["success"] else "with errors"}'
            }
            
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e),
                'executed_at': datetime.now().isoformat()
            }


# Global scheduler instance
scheduler_service = SchedulerService()