#!/usr/bin/env python3
"""
Crypto Sniper Dashboard - PyQt6 GUI Launcher
Enhanced desktop application with multi-chain trading intelligence
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """Launch the PyQt6 dashboard"""
    try:
        print("🚀 Launching Crypto Sniper Dashboard (PyQt6 GUI)...")
        print("🌐 Multi-Chain Trading Intelligence v2.0")
        print("💡 Features: Kraken Markets, Arbitrage Scanner, Solana Sniper, Phantom Wallet")
        print("----------------------------------------")
        
        # Import and run the dashboard
        from gui.dashboard import main as dashboard_main
        dashboard_main()
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()