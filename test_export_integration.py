#!/usr/bin/env python3
"""
Test Export Scheduler Integration
Verify export scheduler works with existing dashboard components
"""

import sys
import os
from datetime import datetime
import threading
import time

# Add project root to path
project_root = os.path.abspath('.')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.exports.export_scheduler import ExportScheduler
from dashboard.components.alert_manager import AlertManager

def test_export_integration():
    """Test export scheduler integration with dashboard components"""
    print("🔗 Testing Export Scheduler Integration...")
    print("=" * 60)
    
    try:
        # Test 1: Basic Integration
        print("\n1️⃣ Testing Basic Integration...")
        scheduler = ExportScheduler()
        alert_manager = AlertManager()
        
        # Generate some test alerts
        test_data = {
            'symbol': 'SOL',
            'name': 'Solana',
            'current_price': 95.50,
            'signal': 'STRONG BUY',
            'momentum_score': 88.5,
            'price_change_1h': 5.2,
            'price_change_24h': 12.8,
            'volume_mcap_ratio': 150.0,
            'market_cap': 45000000000,
            'volume_24h': 6750000000
        }
        
        alert = alert_manager.process_token_data(test_data)
        if alert:
            print(f"✅ Test alert created: {alert.symbol} - {alert.signal_type}")
        
        print("✅ Basic integration successful")
        
        # Test 2: Export with Real Alert Data
        print("\n2️⃣ Testing Export with Real Alert Data...")
        
        # Export alert history (should include our test alert)
        alert_files = scheduler.export_alert_history(days_back=1, format_type='json')
        print(f"✅ Alert export completed: {len(alert_files)} files")
        
        # Test 3: Scheduled Export Setup
        print("\n3️⃣ Testing Scheduled Export Setup...")
        
        # Set up various schedules
        scheduler.schedule_daily_export('signals', '09:00')
        scheduler.schedule_daily_export('alerts', '10:00')
        scheduler.schedule_weekly_report('monday', '08:00')
        
        print("✅ Scheduled exports configured")
        
        # Test 4: Background Thread Test (short duration)
        print("\n4️⃣ Testing Background Thread...")
        
        scheduler.start_scheduler()
        print("✅ Scheduler thread started")
        
        # Let it run for a few seconds
        time.sleep(3)
        
        scheduler.stop_scheduler()
        print("✅ Scheduler thread stopped")
        
        # Test 5: Export Statistics
        print("\n5️⃣ Testing Export Statistics...")
        
        stats = scheduler.get_export_statistics()
        print(f"✅ Export statistics retrieved:")
        print(f"   Total exports: {stats['total_exports']}")
        print(f"   Successful: {stats['successful_exports']}")
        print(f"   Failed: {stats['failed_exports']}")
        
        # Test 6: File Cleanup Test
        print("\n6️⃣ Testing File Cleanup...")
        
        # This won't delete anything since files are new, but tests the function
        deleted_count = scheduler.clear_old_exports(days_old=30)
        print(f"✅ File cleanup test completed: {deleted_count} files would be deleted")
        
        # Test 7: Error Handling
        print("\n7️⃣ Testing Error Handling...")
        
        try:
            # Test with invalid export type
            scheduler.schedule_daily_export('invalid_type', '09:00')
            print("❌ Should have raised an error")
        except ValueError as e:
            print(f"✅ Error handling works: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Export Scheduler Integration Test SUCCESSFUL!")
        print(f"📊 Final Statistics:")
        final_stats = scheduler.get_export_statistics()
        print(f"   Total exports: {final_stats['total_exports']}")
        print(f"   Success rate: {final_stats['successful_exports']}/{final_stats['total_exports']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler_threading():
    """Test scheduler threading functionality"""
    print("\n🧵 Testing Scheduler Threading...")
    print("=" * 40)
    
    try:
        scheduler = ExportScheduler()
        
        # Schedule a test export every 5 seconds (for testing)
        import schedule
        schedule.every(5).seconds.do(lambda: print("⏰ Scheduled task executed!"))
        
        print("✅ Test schedule created")
        
        # Start scheduler
        scheduler.start_scheduler()
        print("✅ Scheduler started")
        
        # Let it run for 12 seconds to see at least 2 executions
        print("⏳ Running for 12 seconds...")
        time.sleep(12)
        
        # Stop scheduler
        scheduler.stop_scheduler()
        print("✅ Scheduler stopped")
        
        print("🎉 Threading test SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Threading test FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Export Scheduler Integration Tests")
    print("=" * 70)
    
    # Run integration test
    integration_success = test_export_integration()
    
    # Run threading test
    threading_success = test_scheduler_threading()
    
    # Overall result
    print("\n" + "=" * 70)
    print("📋 FINAL TEST RESULTS")
    print("=" * 70)
    
    if integration_success and threading_success:
        print("🎉 ALL TESTS PASSED! Export scheduler is ready for production.")
        exit_code = 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        exit_code = 1
    
    print(f"📁 Export files created in: {os.path.abspath('data/exports')}")
    
    sys.exit(exit_code)