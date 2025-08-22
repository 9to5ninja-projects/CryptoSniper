#!/usr/bin/env python3
"""
Quick launcher for Crypto Sniper Dashboard
"""

import os
import sys
import subprocess

def launch_dashboard():
    """Quick launch function"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "streamlit_app.py")
    
    print("🚀 Crypto Sniper Dashboard")
    print("🌐 Opening at: http://localhost:8501")
    print("💡 Press Ctrl+C to stop")
    print("-" * 40)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_path,
            "--server.port=8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")

if __name__ == "__main__":
    launch_dashboard()