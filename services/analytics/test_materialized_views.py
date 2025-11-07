#!/usr/bin/env python3
"""
Test script for materialized views functionality
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_materialized_views():
    """
    Test materialized views service functionality
    """
    try:
        # Import after adding to path
        from app.core.database import init_db, close_db
        from app.services.materialized_views import materialized_views_service
        from app.services.mv_scheduler import mv_scheduler
        
        print("TeLOO V3 - Materialized Views Test")
        print("=" * 40)
        
        # Initialize database
        print("Initializing database connection...")
        await init_db()
        
        # Test 1: Check view status
        print("\n1. Checking materialized views status...")
        status = await materialized_views_service.get_view_status()
        print(f"   Views found: {len(status.get('views', []))}")
        for view in status.get('views', []):
            print(f"   - {view['name']}: {'populated' if view['is_populated'] else 'empty'}")
        
        # Test 2: Refresh views
        print("\n2. Testing materialized views refresh...")
        refresh_result = await materialized_views_service.refresh_materialized_views()
        print(f"   Refresh success: {refresh_result.get('success')}")
        print(f"   Total duration: {refresh_result.get('total_duration_ms', 0)}ms")
        
        for detail in refresh_result.get('details', []):
            status_icon = "✅" if detail['status'] == 'SUCCESS' else "❌"
            print(f"   {status_icon} {detail['view_name']}: {detail['status']}")
            if detail.get('error_message'):
                print(f"      Error: {detail['error_message']}")
        
        # Test 3: Query monthly metrics
        print("\n3. Testing monthly metrics query...")
        monthly_metrics = await materialized_views_service.get_monthly_metrics()
        print(f"   Monthly metrics found: {len(monthly_metrics)}")
        
        if monthly_metrics:
            latest = monthly_metrics[0]
            print(f"   Latest month: {latest.get('mes', 'N/A')}")
            print(f"   Solicitudes creadas: {latest.get('solicitudes_creadas', 0)}")
            print(f"   Tasa aceptación: {latest.get('tasa_aceptacion_pct', 0):.1f}%")
        
        # Test 4: Query advisor rankings
        print("\n4. Testing advisor rankings query...")
        rankings = await materialized_views_service.get_advisor_rankings(limit=5)
        print(f"   Advisor rankings found: {len(rankings)}")
        
        for i, advisor in enumerate(rankings[:3], 1):
            print(f"   #{i} {advisor.get('asesor_nombre', 'N/A')} ({advisor.get('ciudad', 'N/A')})")
            print(f"      Ofertas ganadoras: {advisor.get('ofertas_ganadoras', 0)}")
            print(f"      Tasa respuesta: {advisor.get('tasa_respuesta_pct', 0):.1f}%")
        
        # Test 5: Test scheduler (without starting it)
        print("\n5. Testing scheduler functionality...")
        scheduler_status = mv_scheduler.get_scheduler_status()
        print(f"   Scheduler running: {scheduler_status.get('is_running')}")
        print(f"   Jobs configured: {len(scheduler_status.get('jobs', []))}")
        
        # Close database
        await close_db()
        
        print("\n" + "=" * 40)
        print("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_sample_data():
    """
    Test with some sample data if the views are empty
    """
    try:
        from app.core.database import init_db, close_db
        from tortoise import connections
        
        await init_db()
        conn = connections.get("default")
        
        print("\n6. Checking if sample data is needed...")
        
        # Check if we have any data
        result = await conn.execute_query("SELECT COUNT(*) FROM solicitudes;")
        solicitudes_count = result[1][0][0] if result[1] else 0
        
        result = await conn.execute_query("SELECT COUNT(*) FROM asesores;")
        asesores_count = result[1][0][0] if result[1] else 0
        
        print(f"   Solicitudes in DB: {solicitudes_count}")
        print(f"   Asesores in DB: {asesores_count}")
        
        if solicitudes_count == 0 or asesores_count == 0:
            print("   ⚠️  No data found. Materialized views will be empty.")
            print("   💡 Consider running the data import scripts first.")
        else:
            print("   ✅ Data found. Materialized views should have content.")
        
        await close_db()
        
    except Exception as e:
        print(f"   ❌ Error checking sample data: {e}")

def main():
    """Main function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        print("   Please set it in your .env file or environment")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(test_materialized_views())
    
    # Check sample data
    asyncio.run(test_with_sample_data())
    
    if success:
        print("\n🎉 Materialized views are working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()