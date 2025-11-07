"""
Scheduler Service for Analytics Batch Jobs
Manages scheduled execution of complex metrics calculations
"""
import logging
from typing import Optional
from datetime import datetime, timedelta, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import asyncio

from app.services.batch_jobs import batch_jobs_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnalyticsScheduler:
    """
    Scheduler for Analytics batch jobs
    """
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
    
    async def initialize(self):
        """Initialize the scheduler with batch jobs"""
        try:
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
                'misfire_grace_time': 1800  # 30 minutes
            }
            
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='America/Bogota'
            )
            
            # Setup scheduled jobs
            await self._setup_batch_jobs()
            
            logger.info("Analytics scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing analytics scheduler: {e}")
            raise
    
    async def start(self):
        """Start the scheduler"""
        if self.scheduler and not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Analytics scheduler started")
    
    async def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler and self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Analytics scheduler shutdown")
    
    async def _setup_batch_jobs(self):
        """Setup all batch jobs"""
        
        # Job diario: 2 AM - ranking de asesores, especialización por repuesto
        self.scheduler.add_job(
            func=self._run_daily_batch_job,
            trigger=CronTrigger(hour=settings.BATCH_JOB_HOUR, minute=0),  # 2 AM por defecto
            id='daily_metrics_batch',
            name='Job diario de métricas complejas',
            replace_existing=True
        )
        
        # Job semanal: Lunes 3 AM - evolución temporal, análisis de tendencias
        self.scheduler.add_job(
            func=self._run_weekly_batch_job,
            trigger=CronTrigger(day_of_week='mon', hour=3, minute=0),  # Lunes 3 AM
            id='weekly_metrics_batch',
            name='Job semanal de análisis de tendencias',
            replace_existing=True
        )
        
        # Job de limpieza: Domingo 4 AM - limpiar métricas expiradas
        self.scheduler.add_job(
            func=self._cleanup_expired_metrics,
            trigger=CronTrigger(day_of_week='sun', hour=4, minute=0),  # Domingo 4 AM
            id='cleanup_metrics',
            name='Limpieza de métricas expiradas',
            replace_existing=True
        )
        
        # Job de verificación de alertas: cada 5 minutos
        self.scheduler.add_job(
            func=self._check_alerts,
            trigger=CronTrigger(minute='*/5'),  # Cada 5 minutos
            id='alert_check',
            name='Verificación de alertas automáticas',
            replace_existing=True
        )
        
        logger.info("Analytics batch jobs configured")
    
    async def _run_daily_batch_job(self):
        """Execute daily batch job"""
        try:
            logger.info("Iniciando job diario de métricas")
            
            # Ejecutar para el día anterior
            fecha = (datetime.now() - timedelta(days=1)).date()
            
            result = await batch_jobs_service.run_daily_batch_job(fecha)
            
            if result['success']:
                logger.info(f"Job diario completado exitosamente en {result['execution_time_seconds']:.2f}s")
                
                # Log resultados principales
                results = result.get('results', {})
                if 'ranking_asesores' in results:
                    ranking_data = results['ranking_asesores']
                    logger.info(f"Ranking calculado para {ranking_data.get('total_asesores', 0)} asesores")
                
                if 'especializacion_repuestos' in results:
                    esp_data = results['especializacion_repuestos']
                    logger.info(f"Especialización calculada para {esp_data.get('total_asesores_especializados', 0)} asesores")
                
            else:
                logger.error(f"Job diario falló: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error ejecutando job diario: {e}")
    
    async def _run_weekly_batch_job(self):
        """Execute weekly batch job"""
        try:
            logger.info("Iniciando job semanal de análisis de tendencias")
            
            # Ejecutar para la semana anterior (termina ayer)
            fecha_fin = (datetime.now() - timedelta(days=1)).date()
            
            result = await batch_jobs_service.run_weekly_batch_job(fecha_fin)
            
            if result['success']:
                logger.info(f"Job semanal completado exitosamente en {result['execution_time_seconds']:.2f}s")
                
                # Log resultados principales
                results = result.get('results', {})
                if 'tendencias_solicitudes' in results:
                    tend_data = results['tendencias_solicitudes']
                    logger.info(f"Tendencia de solicitudes: {tend_data.get('tendencia', 'N/A')}")
                
                if 'evolucion_asesores' in results:
                    evol_data = results['evolucion_asesores']
                    logger.info(f"Evolución analizada para {evol_data.get('total_asesores_analizados', 0)} asesores")
                
            else:
                logger.error(f"Job semanal falló: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error ejecutando job semanal: {e}")
    
    async def _cleanup_expired_metrics(self):
        """Clean up expired metrics"""
        try:
            logger.info("Iniciando limpieza de métricas expiradas")
            
            from app.models.metrics import MetricaCalculada
            
            # Eliminar métricas expiradas
            now = datetime.now()
            expired_count = await MetricaCalculada.filter(expira_en__lt=now).count()
            
            if expired_count > 0:
                await MetricaCalculada.filter(expira_en__lt=now).delete()
                logger.info(f"Eliminadas {expired_count} métricas expiradas")
            else:
                logger.info("No hay métricas expiradas para eliminar")
            
            # También limpiar eventos antiguos (más de 30 días)
            from app.models.events import EventoSistema, EventoMetrica
            
            cutoff_date = now - timedelta(days=30)
            
            old_events_count = await EventoSistema.filter(timestamp__lt=cutoff_date).count()
            if old_events_count > 0:
                await EventoSistema.filter(timestamp__lt=cutoff_date).delete()
                logger.info(f"Eliminados {old_events_count} eventos antiguos")
            
            old_metric_events_count = await EventoMetrica.filter(timestamp__lt=cutoff_date).count()
            if old_metric_events_count > 0:
                await EventoMetrica.filter(timestamp__lt=cutoff_date).delete()
                logger.info(f"Eliminados {old_metric_events_count} eventos de métricas antiguos")
            
            logger.info("Limpieza de métricas completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza de métricas: {e}")
    
    async def _check_alerts(self):
        """Check all active alerts"""
        try:
            logger.debug("Iniciando verificación de alertas")
            
            # Import here to avoid circular imports
            from app.services.alert_manager import alert_manager
            
            await alert_manager.check_all_alerts()
            
            logger.debug("Verificación de alertas completada")
            
        except Exception as e:
            logger.error(f"Error verificando alertas: {e}")
    
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
        """Manually trigger a batch job"""
        if not self.scheduler:
            raise ValueError("Scheduler not initialized")
        
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            start_time = datetime.now()
            
            # Execute the appropriate job function
            if job_id == 'daily_metrics_batch':
                result = await self._run_daily_batch_job()
            elif job_id == 'weekly_metrics_batch':
                result = await self._run_weekly_batch_job()
            elif job_id == 'cleanup_metrics':
                result = await self._cleanup_expired_metrics()
            elif job_id == 'alert_check':
                result = await self._check_alerts()
            else:
                raise ValueError(f"Unknown job ID: {job_id}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'job_id': job_id,
                'executed_at': start_time.isoformat(),
                'execution_time_seconds': execution_time,
                'message': f'Job {job_id} executed successfully'
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
analytics_scheduler = AnalyticsScheduler()