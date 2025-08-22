#!/usr/bin/env python3
"""
Crypto Sniper Dashboard - Multi-Chain Trading Intelligence Platform
Main application entry point
"""

import sys
import os
import subprocess

def main():
    """Launch the Crypto Sniper Dashboard"""
    print("🚀 Starting Crypto Sniper Dashboard...")
    print("📊 Launching Streamlit Web Interface...")
    
    # Get the dashboard path
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "streamlit_app.py")
    
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard not found at: {dashboard_path}")
        return
    
    try:
        # Launch Streamlit dashboard
        print(f"🌐 Dashboard will open in your browser at: http://localhost:8501")
        print("💡 Press Ctrl+C to stop the dashboard")
        print("-" * 60)
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_path,
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it:")
        print("   pip install streamlit")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        print("\n💡 Alternative: Run manually with:")
        print(f"   streamlit run {dashboard_path}")

if __name__ == "__main__":
    main()
