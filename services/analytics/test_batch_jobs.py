"""
Test script for batch jobs functionality
"""
import asyncio
import sys
import os
from datetime import datetime, date, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_batch_jobs():
    """Test the batch jobs functionality"""
    try:
        # Initialize database
        from app.core.database import init_db, close_db
        await init_db()
        print("✓ Database initialized")
        
        # Test batch jobs service
        from app.services.batch_jobs import batch_jobs_service
        
        # Test daily job
        print("\n--- Testing Daily Batch Job ---")
        yesterday = (datetime.now() - timedelta(days=1)).date()
        daily_result = await batch_jobs_service.run_daily_batch_job(yesterday)
        
        if daily_result['success']:
            print(f"✓ Daily job completed in {daily_result['execution_time_seconds']:.2f}s")
            results = daily_result.get('results', {})
            for key, value in results.items():
                if isinstance(value, dict) and 'error' not in value:
                    print(f"  - {key}: OK")
                elif 'error' in value:
                    print(f"  - {key}: ERROR - {value['error']}")
        else:
            print(f"✗ Daily job failed: {daily_result.get('error', 'Unknown error')}")
        
        # Test weekly job
        print("\n--- Testing Weekly Batch Job ---")
        weekly_result = await batch_jobs_service.run_weekly_batch_job(yesterday)
        
        if weekly_result['success']:
            print(f"✓ Weekly job completed in {weekly_result['execution_time_seconds']:.2f}s")
            results = weekly_result.get('results', {})
            for key, value in results.items():
                if isinstance(value, dict) and 'error' not in value:
                    print(f"  - {key}: OK")
                elif 'error' in value:
                    print(f"  - {key}: ERROR - {value['error']}")
        else:
            print(f"✗ Weekly job failed: {weekly_result.get('error', 'Unknown error')}")
        
        # Test scheduler
        print("\n--- Testing Scheduler ---")
        from app.services.scheduler import analytics_scheduler
        
        await analytics_scheduler.initialize()
        print("✓ Scheduler initialized")
        
        status = analytics_scheduler.get_job_status()
        print(f"✓ Scheduler status: {status['status']}")
        print(f"✓ Configured jobs: {len(status.get('jobs', []))}")
        
        for job in status.get('jobs', []):
            print(f"  - {job['name']} (ID: {job['id']})")
            print(f"    Next run: {job['next_run']}")
        
        # Test metrics storage
        print("\n--- Testing Metrics Storage ---")
        from app.models.metrics import MetricaCalculada
        
        # Count stored metrics
        total_metrics = await MetricaCalculada.all().count()
        print(f"✓ Total stored metrics: {total_metrics}")
        
        # Get recent metrics
        recent_metrics = await MetricaCalculada.all().order_by('-calculado_en').limit(5)
        print("✓ Recent metrics:")
        for metric in recent_metrics:
            print(f"  - {metric.nombre}: {metric.valor} ({metric.calculado_en.strftime('%Y-%m-%d %H:%M')})")
        
        await analytics_scheduler.shutdown()
        print("✓ Scheduler shutdown")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database
        await close_db()
        print("✓ Database closed")

if __name__ == "__main__":
    print("Testing Analytics Batch Jobs...")
    asyncio.run(test_batch_jobs())
    print("\nTest completed!")