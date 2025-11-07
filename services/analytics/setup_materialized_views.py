#!/usr/bin/env python3
"""
Setup script for materialized views
Runs the SQL migration to create enhanced materialized views
"""
import asyncio
import asyncpg
import os
import sys
from pathlib import Path

async def setup_materialized_views():
    """
    Setup materialized views by running the SQL migration
    """
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not set")
            return False
        
        print("Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Read the SQL migration file
        sql_file = Path(__file__).parent.parent.parent / "scripts" / "create_enhanced_materialized_views.sql"
        
        if not sql_file.exists():
            print(f"ERROR: SQL file not found: {sql_file}")
            return False
        
        print(f"Reading SQL migration from: {sql_file}")
        sql_content = sql_file.read_text()
        
        # Execute the SQL
        print("Executing SQL migration...")
        await conn.execute(sql_content)
        
        print("✅ Materialized views created successfully!")
        
        # Test the views
        print("\nTesting materialized views...")
        
        # Test mv_metricas_mensuales
        result = await conn.fetch("SELECT COUNT(*) as count FROM mv_metricas_mensuales;")
        print(f"mv_metricas_mensuales: {result[0]['count']} rows")
        
        # Test mv_ranking_asesores
        result = await conn.fetch("SELECT COUNT(*) as count FROM mv_ranking_asesores;")
        print(f"mv_ranking_asesores: {result[0]['count']} rows")
        
        # Test refresh function
        print("\nTesting refresh function...")
        result = await conn.fetch("SELECT * FROM refresh_all_mv();")
        for row in result:
            print(f"  {row['view_name']}: {row['refresh_status']} ({row['refresh_time_ms']}ms)")
        
        await conn.close()
        print("\n✅ Setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up materialized views: {e}")
        return False

async def check_pg_cron():
    """
    Check if pg_cron extension is available and configure it
    """
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return False
        
        conn = await asyncpg.connect(database_url)
        
        # Check if pg_cron is installed
        result = await conn.fetch(
            "SELECT * FROM pg_extension WHERE extname = 'pg_cron';"
        )
        
        if result:
            print("✅ pg_cron extension is installed")
            
            # Try to schedule the job
            try:
                await conn.execute(
                    "SELECT cron.schedule('refresh-materialized-views', '0 1 * * *', 'SELECT refresh_all_mv();');"
                )
                print("✅ Scheduled daily refresh job at 1:00 AM")
            except Exception as e:
                print(f"⚠️  Could not schedule cron job: {e}")
                print("   The application scheduler will handle automatic refresh instead")
        else:
            print("⚠️  pg_cron extension not found")
            print("   The application scheduler will handle automatic refresh instead")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"⚠️  Could not check pg_cron: {e}")
        print("   The application scheduler will handle automatic refresh instead")
        return False

def main():
    """Main function"""
    print("TeLOO V3 - Materialized Views Setup")
    print("=" * 40)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run setup
    success = asyncio.run(setup_materialized_views())
    
    if success:
        # Check pg_cron
        print("\nChecking pg_cron extension...")
        asyncio.run(check_pg_cron())
        
        print("\n" + "=" * 40)
        print("Setup completed! The materialized views are ready.")
        print("\nNext steps:")
        print("1. Start the analytics service: python main.py")
        print("2. The scheduler will automatically refresh views daily at 1:00 AM")
        print("3. Use the API endpoints to query the materialized views")
        print("4. Monitor the scheduler status via /materialized-views/scheduler/status")
        
        sys.exit(0)
    else:
        print("\n" + "=" * 40)
        print("Setup failed! Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()