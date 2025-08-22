#!/usr/bin/env python3
"""
Crypto Sniper Dashboard - Main Entry Point
Professional multi-chain trading intelligence platform
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import pandas
        import plotly
        import ccxt
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def main():
    """Main application entry point"""
    print("=" * 60)
    print("    CRYPTO SNIPER DASHBOARD")
    print("    Professional Trading Intelligence Platform")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get project root
    project_root = Path(__file__).parent
    dashboard_path = project_root / "dashboard" / "streamlit_app.py"
    
    if not dashboard_path.exists():
        print(f"Error: Dashboard file not found at {dashboard_path}")
        sys.exit(1)
    
    # Launch Streamlit dashboard
    print(f"Starting dashboard...")
    print(f"Dashboard will open at: http://localhost:8501")
    print("Press Ctrl+C to stop the application")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\nShutting down Crypto Sniper Dashboard...")
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
