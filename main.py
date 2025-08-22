#!/usr/bin/env python3
"""
Crypto Sniper Dashboard - Multi-Chain Trading Intelligence Platform
Main application entry point
"""

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.dashboard import main

if __name__ == "__main__":
    main()
