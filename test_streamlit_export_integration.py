#!/usr/bin/env python3
"""
Test Streamlit + Export Scheduler Integration
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath('.')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_streamlit_export_integration():
    """Test Streamlit integration with export scheduler"""
    print("🧪 Testing Streamlit + Export Scheduler Integration...")
    print("=" * 60)
    
    try:
        from dashboard.components.alert_manager import AlertManager
        from data.exports.export_scheduler import ExportScheduler
        from config.settings import get_alert_config
        
        # Test component initialization
        alert_manager = AlertManager()
        export_scheduler = ExportScheduler()
        config = get_alert_config()
        
        print("✅ All components initialized successfully")
        
        # Test export functionality
        files = export_scheduler.export_alert_history(1, 'json')
        print(f"✅ Export test successful: {len(files)} files created")
        
        # Test statistics
        stats = export_scheduler.get_export_statistics()
        print(f"✅ Statistics retrieved: {stats['total_exports']} total exports")
        
        # Test scheduling setup
        export_scheduler.schedule_daily_export('signals', '09:00')
        print("✅ Scheduling test successful")
        
        print("\n🎉 Streamlit + Export Scheduler integration SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streamlit_export_integration()
    sys.exit(0 if success else 1)