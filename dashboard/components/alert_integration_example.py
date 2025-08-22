"""
Example integration of AlertManager with existing dashboard components.
This demonstrates how to use the AlertManager in your main application.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from dashboard.components.alert_manager import AlertManager
from api_clients.coingecko_api import CoinGeckoAPI
import time

def run_alert_monitoring_example():
    """
    Example of how to integrate AlertManager into your main application loop
    """
    print("🚨 Starting Alert Monitoring Example...")
    
    # Initialize components
    coingecko_api = CoinGeckoAPI()
    alert_manager = AlertManager(coingecko_api)
    
    print("✅ Alert monitoring system initialized")
    
    # Simulate monitoring loop (in real app, this would be continuous)
    for cycle in range(3):
        print(f"\n🔄 Monitoring Cycle {cycle + 1}")
        
        # Scan for new alerts
        new_alerts = alert_manager.scan_for_alerts(limit=15)
        
        if new_alerts:
            print(f"🚨 Found {len(new_alerts)} new alerts:")
            for alert in new_alerts:
                print(f"  📢 {alert.message}")
                print(f"     Price: ${alert.price:.6f} | Confidence: {alert.confidence_score:.1f}%")
        else:
            print("✅ No new alerts this cycle")
        
        # Get current alert summary
        summary = alert_manager.get_alert_summary()
        print(f"📊 Alert Summary: {summary['total_active_alerts']} active alerts")
        
        # Display active alerts
        active_alerts = alert_manager.get_active_alerts()
        if active_alerts:
            print("📋 Current Active Alerts:")
            for alert in active_alerts[:3]:  # Show top 3
                print(f"  - {alert['symbol']}: {alert['signal_type']} ({alert['confidence_score']:.1f}%)")
        
        # Wait before next cycle (in real app, you might use a scheduler)
        if cycle < 2:  # Don't wait on last cycle
            print("⏳ Waiting 10 seconds before next scan...")
            time.sleep(10)
    
    print("\n✅ Alert monitoring example completed!")
    return alert_manager

def demonstrate_alert_filtering():
    """
    Demonstrate how to filter and work with alerts
    """
    print("\n🔍 Demonstrating Alert Filtering...")
    
    alert_manager = AlertManager()
    
    # Create some test alerts
    test_alerts = [
        ("BTC", "STRONG_BUY", 85.0, 45000.0),
        ("ETH", "HIGH_VOLATILITY", 18.5, 3200.0),
        ("SOL", "VOLUME_SPIKE", 250.0, 100.0),
        ("BONK", "STRONG_BUY", 92.0, 0.000015)
    ]
    
    for symbol, signal_type, confidence, price in test_alerts:
        alert_manager.create_alert(symbol, signal_type, confidence, price)
    
    # Get all active alerts
    all_alerts = alert_manager.get_active_alerts()
    print(f"📊 Total alerts created: {len(all_alerts)}")
    
    # Filter by signal type
    strong_buy_alerts = [a for a in all_alerts if a['signal_type'] == 'STRONG_BUY']
    print(f"🚀 Strong Buy alerts: {len(strong_buy_alerts)}")
    
    # Filter by confidence threshold
    high_confidence_alerts = [a for a in all_alerts if a['confidence_score'] > 80]
    print(f"⭐ High confidence alerts (>80%): {len(high_confidence_alerts)}")
    
    # Show alert details
    print("\n📋 Alert Details:")
    for alert in all_alerts:
        print(f"  {alert['symbol']}: {alert['signal_type']} - {alert['confidence_score']:.1f}% confidence")
    
    return alert_manager

if __name__ == "__main__":
    # Run the examples
    alert_manager = run_alert_monitoring_example()
    demonstrate_alert_filtering()
    
    print("\n🎯 Integration examples completed successfully!")