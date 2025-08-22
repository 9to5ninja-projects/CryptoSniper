#!/usr/bin/env python3
"""
Verify Signal Generator Integration
Quick test to verify AlertManager works with existing signal generation
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath('.')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard.components.alert_manager import AlertManager
from api_clients.coingecko_api import CoinGeckoAPI

def test_signal_integration():
    """Test integration with existing signal generation"""
    print("🔗 Testing Signal Generator Integration...")
    print("=" * 50)
    
    try:
        # Initialize components
        alert_manager = AlertManager()
        coingecko_api = CoinGeckoAPI()
        
        print("✅ Components initialized successfully")
        
        # Test with real market data (limited to avoid rate limits)
        print("\n📊 Testing with live market data...")
        analyzed_df = coingecko_api.get_analyzed_solana_tokens(5)
        
        if not analyzed_df.empty:
            print(f"✅ Retrieved {len(analyzed_df)} tokens from market")
            
            # Show sample of the data structure
            print("\n📋 Sample token data structure:")
            sample_token = analyzed_df.iloc[0].to_dict()
            for key, value in list(sample_token.items())[:8]:  # Show first 8 fields
                print(f"  {key}: {value}")
            print("  ... (and more fields)")
            
            # Test alert processing
            alerts_created = 0
            for _, token_data in analyzed_df.iterrows():
                token_dict = token_data.to_dict()
                alert = alert_manager.process_token_data(token_dict)
                if alert:
                    alerts_created += 1
                    print(f"  🚨 Alert: {alert.symbol} - {alert.signal_type} ({alert.confidence_score:.1f}%)")
            
            print(f"\n✅ Processed {len(analyzed_df)} tokens")
            print(f"✅ Created {alerts_created} alerts from live data")
            
            # Test alert summary
            summary = alert_manager.get_alert_summary()
            print(f"✅ Alert summary: {summary['total_active_alerts']} active alerts")
            
        else:
            print("⚠️  No market data available (API might be rate limited)")
            
        # Test with existing signal generation patterns
        print("\n🧪 Testing signal generation patterns...")
        
        # Simulate data that matches existing signal patterns
        test_signals = [
            {
                'symbol': 'SOL',
                'signal': 'STRONG BUY',
                'momentum_score': 88.5,
                'price_change_1h': 5.2,
                'volume_mcap_ratio': 150.0
            },
            {
                'symbol': 'AVAX', 
                'signal': 'BUY',
                'momentum_score': 65.0,
                'price_change_1h': 18.5,
                'volume_mcap_ratio': 120.0
            },
            {
                'symbol': 'MATIC',
                'signal': 'WATCH',
                'momentum_score': 70.0,
                'price_change_1h': 6.5,
                'volume_mcap_ratio': 250.0
            }
        ]
        
        pattern_alerts = 0
        for signal_data in test_signals:
            # Add required fields
            full_data = {
                'name': f"{signal_data['symbol']} Token",
                'current_price': 10.0,
                'price_change_24h': 15.0,
                'market_cap': 1000000000,
                'volume_24h': 500000000,
                **signal_data
            }
            
            alert = alert_manager.process_token_data(full_data)
            if alert:
                pattern_alerts += 1
                print(f"  🎯 Pattern Alert: {alert.symbol} - {alert.signal_type}")
        
        print(f"✅ Created {pattern_alerts} alerts from signal patterns")
        
        print("\n" + "=" * 50)
        print("🎉 Signal Generator Integration SUCCESSFUL!")
        print(f"📊 Total alerts in system: {len(alert_manager.get_active_alerts())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_signal_integration()
    sys.exit(0 if success else 1)