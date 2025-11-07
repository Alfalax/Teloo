#!/usr/bin/env python3
"""
Analytics Service Test Runner
Ejecuta todos los tests del Analytics Service de forma organizada
"""
import asyncio
import sys
import os
import subprocess
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)

def print_section(title):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 40)

async def run_test_file(test_file, description):
    """Run a specific test file"""
    print(f"\n🔍 Running {description}...")
    print(f"   File: {test_file}")
    
    try:
        # Check if file exists
        if not os.path.exists(test_file):
            print(f"   ❌ Test file not found: {test_file}")
            return False
        
        # Run the test file
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"   ✅ {description} - PASSED")
            if result.stdout:
                # Print last few lines of output for summary
                lines = result.stdout.strip().split('\n')
                for line in lines[-3:]:
                    if line.strip():
                        print(f"   {line}")
            return True
        else:
            print(f"   ❌ {description} - FAILED")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            if result.stdout:
                print(f"   Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"   ❌ {description} - ERROR: {e}")
        return False

def check_environment():
    """Check if the environment is properly configured"""
    print_section("Environment Check")
    
    # Check Python version
    python_version = sys.version_info
    print(f"   Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("   ❌ Python 3.8+ required")
        return False
    else:
        print("   ✅ Python version OK")
    
    # Check environment variables
    required_env_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set them in your .env file")
        return False
    else:
        print("   ✅ Environment variables OK")
    
    # Check if we're in the right directory
    current_dir = os.path.basename(os.getcwd())
    if current_dir != "analytics":
        print(f"   ⚠️  Current directory: {current_dir}")
        print("   Expected to be in 'analytics' directory")
    
    return True

async def run_existing_tests():
    """Run existing test files"""
    print_section("Existing Analytics Tests")
    
    existing_tests = [
        ("test_alert_system.py", "Alert System Tests"),
        ("test_batch_jobs.py", "Batch Jobs Tests"),
        ("test_materialized_views.py", "Materialized Views Tests")
    ]
    
    results = {}
    
    for test_file, description in existing_tests:
        if os.path.exists(test_file):
            results[description] = await run_test_file(test_file, description)
        else:
            print(f"   ⚠️  {test_file} not found, skipping...")
            results[description] = None
    
    return results

async def run_new_comprehensive_tests():
    """Run new comprehensive test files"""
    print_section("New Comprehensive Tests")
    
    new_tests = [
        ("test_event_processing.py", "Event Processing Tests"),
        ("test_metrics_calculation.py", "Metrics Calculation Tests"),
        ("test_analytics_complete.py", "Complete Analytics Service Tests")
    ]
    
    results = {}
    
    for test_file, description in new_tests:
        if os.path.exists(test_file):
            results[description] = await run_test_file(test_file, description)
        else:
            print(f"   ⚠️  {test_file} not found, skipping...")
            results[description] = None
    
    return results

def print_final_summary(existing_results, new_results):
    """Print final test summary"""
    print_header("Final Test Summary")
    
    all_results = {**existing_results, **new_results}
    
    passed = sum(1 for r in all_results.values() if r is True)
    failed = sum(1 for r in all_results.values() if r is False)
    skipped = sum(1 for r in all_results.values() if r is None)
    total = len(all_results)
    
    print(f"📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   📈 Total: {total}")
    
    print(f"\n📋 Detailed Results:")
    for test_name, result in all_results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        
        print(f"   {test_name}: {status}")
    
    # Overall result
    if failed == 0:
        if passed > 0:
            print(f"\n🎉 All tests completed successfully!")
            print(f"   Analytics Service is working correctly.")
        else:
            print(f"\n⚠️  No tests were executed.")
        return True
    else:
        print(f"\n💥 {failed} test(s) failed.")
        print(f"   Please review the errors above.")
        return False

async def main():
    """Main test runner function"""
    start_time = datetime.now()
    
    print_header("Analytics Service Test Suite")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    try:
        # Run existing tests
        existing_results = await run_existing_tests()
        
        # Run new comprehensive tests
        new_results = await run_new_comprehensive_tests()
        
        # Print final summary
        success = print_final_summary(existing_results, new_results)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\nCompleted at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration.total_seconds():.2f} seconds")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)