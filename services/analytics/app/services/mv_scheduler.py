"""
Materialized Views Scheduler Service
Handles automatic refresh of materialized views using APScheduler
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from .materialized_views import materialized_views_service

logger = logging.getLogger(__name__)

class MaterializedViewsScheduler:
    """
    Scheduler service for automatic materialized views refresh
    """
    
    def __init__(self):
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
        
        self.is_running = False
        self.last_refresh_result: Optional[Dict[str, Any]] = None
    
    async def start(self):
        """Start the scheduler"""
        if not self.is_running:
            try:
                # Add the daily refresh job at 1 AM
                self.scheduler.add_job(
                    func=self._refresh_materialized_views_job,
                    trigger=CronTrigger(hour=1, minute=0),  # 1:00 AM daily
                    id='refresh_materialized_views',
                    name='Refresh Materialized Views',
                    replace_existing=True
                )
                
                # Add a job to refresh views on startup (after 30 seconds)
                self.scheduler.add_job(
                    func=self._refresh_materialized_views_job,
                    trigger='date',
                    run_date=datetime.now().replace(second=30, microsecond=0),
                    id='startup_refresh_materialized_views',
                    name='Startup Refresh Materialized Views'
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info("Materialized Views Scheduler started successfully")
                
            except Exception as e:
                logger.error(f"Error starting Materialized Views Scheduler: {e}")
                raise
    
    async def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            try:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                logger.info("Materialized Views Scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping Materialized Views Scheduler: {e}")
    
    async def _refresh_materialized_views_job(self):
        """
        Job function to refresh materialized views
        This is called by the scheduler
        """
        try:
            logger.info("Starting scheduled refresh of materialized views")
            
            start_time = datetime.now()
            result = await materialized_views_service.refresh_materialized_views()
            end_time = datetime.now()
            
            # Store the result for monitoring
            self.last_refresh_result = {
                **result,
                'job_start_time': start_time.isoformat(),
                'job_end_time': end_time.isoformat(),
                'job_duration_seconds': (end_time - start_time).total_seconds()
            }
            
            if result.get('success'):
                logger.info(
                    f"Materialized views refreshed successfully. "
                    f"Duration: {result.get('total_duration_ms', 0)}ms"
                )
            else:
                logger.error(
                    f"Error refreshing materialized views: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            logger.error(f"Exception in materialized views refresh job: {e}")
            self.last_refresh_result = {
                'success': False,
                'error': str(e),
                'job_start_time': datetime.now().isoformat(),
                'job_end_time': datetime.now().isoformat()
            }
    
    async def trigger_manual_refresh(self) -> Dict[str, Any]:
        """
        Manually trigger a refresh of materialized views
        """
        try:
            logger.info("Manual refresh of materialized views triggered")
            
            # Add a one-time job to run immediately
            job = self.scheduler.add_job(
                func=self._refresh_materialized_views_job,
                trigger='date',
                run_date=datetime.now(),
                id=f'manual_refresh_{datetime.now().timestamp()}',
                name='Manual Refresh Materialized Views'
            )
            
            return {
                'success': True,
                'message': 'Manual refresh job scheduled',
                'job_id': job.id,
                'scheduled_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling manual refresh: {e}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_at': datetime.now().isoformat()
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current status of the scheduler
        """
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'is_running': self.is_running,
                'scheduler_state': self.scheduler.state,
                'jobs': jobs,
                'last_refresh_result': self.last_refresh_result,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    async def reschedule_daily_refresh(self, hour: int = 1, minute: int = 0) -> Dict[str, Any]:
        """
        Reschedule the daily refresh job to a different time
        """
        try:
            # Remove existing job
            try:
                self.scheduler.remove_job('refresh_materialized_views')
            except:
                pass  # Job might not exist
            
            # Add new job with updated schedule
            self.scheduler.add_job(
                func=self._refresh_materialized_views_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='refresh_materialized_views',
                name='Refresh Materialized Views',
                replace_existing=True
            )
            
            logger.info(f"Daily refresh rescheduled to {hour:02d}:{minute:02d}")
            
            return {
                'success': True,
                'message': f'Daily refresh rescheduled to {hour:02d}:{minute:02d}',
                'new_schedule': f'{hour:02d}:{minute:02d}',
                'rescheduled_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error rescheduling daily refresh: {e}")
            return {
                'success': False,
                'error': str(e),
                'rescheduled_at': datetime.now().isoformat()
            }

# Global instance
mv_scheduler = MaterializedViewsScheduler()