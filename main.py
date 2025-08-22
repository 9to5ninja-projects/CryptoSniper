#!/usr/bin/env python3
"""
Crypto Sniper Dashboard - Main Entry Point
Professional multi-chain trading intelligence platform
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import PyQt6
        import pandas
        import plotly
        import requests
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
    
    print("✅ All dependencies loaded successfully!")
    print("🚀 Ready for development...")
    
    # For now, just test the Kraken API
    try:
        from api_clients.kraken_api import test_kraken_api
        test_kraken_api()
    except ImportError as e:
        print(f"Error importing Kraken API: {e}")

if __name__ == "__main__":
    main()
