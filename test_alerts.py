#!/usr/bin/env python3
"""
Test Alert System Integration
Comprehensive tests for the alert system functionality
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

# Add project root to path
project_root = os.path.abspath('.')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard.components.alert_manager import AlertManager
from api_clients.coingecko_api import CoinGeckoAPI
from config.settings import get_alert_config, reset_alert_config

class AlertSystemTester:
    """Test suite for alert system integration"""
    
    def __init__(self):
        """Initialize test environment"""
        self.alert_manager = AlertManager()
        self.coingecko_api = CoinGeckoAPI()
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def create_test_data_strong_buy(self) -> Dict:
        """Create test data that should trigger strong buy alert"""
        return {
            'symbol': 'SOL',
            'name': 'Solana',
            'current_price': 95.50,
            'signal': 'STRONG BUY',
            'momentum_score': 88.5,  # Above default threshold of 80
            'price_change_1h': 5.2,
            'price_change_24h': 12.8,
            'volume_mcap_ratio': 150.0,
            'market_cap': 45000000000,
            'volume_24h': 6750000000
        }
    
    def create_test_data_high_volatility(self) -> Dict:
        """Create test data that should trigger high volatility alert"""
        return {
            'symbol': 'AVAX',
            'name': 'Avalanche',
            'current_price': 42.30,
            'signal': 'BUY',
            'momentum_score': 65.0,
            'price_change_1h': 18.5,  # Above default threshold of 15%
            'price_change_24h': 25.2,
            'volume_mcap_ratio': 120.0,
            'market_cap': 15000000000,
            'volume_24h': 1800000000
        }
    
    def create_test_data_volume_spike(self) -> Dict:
        """Create test data that should trigger volume spike alert"""
        return {
            'symbol': 'MATIC',
            'name': 'Polygon',
            'current_price': 0.85,
            'signal': 'WATCH',
            'momentum_score': 72.0,
            'price_change_1h': 8.2,
            'price_change_24h': 15.5,
            'volume_mcap_ratio': 250.0,  # Above default threshold of 200%
            'market_cap': 8000000000,
            'volume_24h': 20000000000
        }
    
    def create_test_data_no_alert(self) -> Dict:
        """Create test data that should NOT trigger any alerts"""
        return {
            'symbol': 'ADA',
            'name': 'Cardano',
            'current_price': 0.45,
            'signal': 'HOLD',
            'momentum_score': 55.0,  # Below threshold
            'price_change_1h': 2.1,  # Below threshold
            'price_change_24h': 4.8,
            'volume_mcap_ratio': 80.0,  # Below threshold
            'market_cap': 16000000000,
            'volume_24h': 1280000000
        }
    
    def test_alert_creation(self):
        """Test basic alert creation functionality"""
        print("\n🧪 Testing Alert Creation...")
        
        # Test 1: Strong Buy Alert
        test_data = self.create_test_data_strong_buy()
        alert = self.alert_manager.process_token_data(test_data)
        
        if alert and alert.signal_type == 'STRONG_BUY':
            self.log_test("Strong Buy Alert Creation", True, f"Created alert for {alert.symbol}")
        else:
            self.log_test("Strong Buy Alert Creation", False, "Failed to create strong buy alert")
        
        # Test 2: High Volatility Alert
        test_data = self.create_test_data_high_volatility()
        alert = self.alert_manager.process_token_data(test_data)
        
        if alert and alert.signal_type == 'HIGH_VOLATILITY':
            self.log_test("High Volatility Alert Creation", True, f"Created alert for {alert.symbol}")
        else:
            self.log_test("High Volatility Alert Creation", False, "Failed to create volatility alert")
        
        # Test 3: Volume Spike Alert
        test_data = self.create_test_data_volume_spike()
        alert = self.alert_manager.process_token_data(test_data)
        
        if alert and alert.signal_type == 'VOLUME_SPIKE':
            self.log_test("Volume Spike Alert Creation", True, f"Created alert for {alert.symbol}")
        else:
            self.log_test("Volume Spike Alert Creation", False, "Failed to create volume spike alert")
        
        # Test 4: No Alert Condition
        test_data = self.create_test_data_no_alert()
        alert = self.alert_manager.process_token_data(test_data)
        
        if alert is None:
            self.log_test("No Alert Condition", True, "Correctly did not create alert")
        else:
            self.log_test("No Alert Condition", False, f"Incorrectly created alert: {alert.signal_type}")
    
    def test_configuration_integration(self):
        """Test configuration system integration"""
        print("\n🔧 Testing Configuration Integration...")
        
        # Test 1: Configuration Loading
        config = get_alert_config()
        expected_keys = ['ENABLE_ALERTS', 'STRONG_BUY_THRESHOLD', 'VOLATILITY_THRESHOLD', 
                        'VOLUME_SPIKE_THRESHOLD', 'MAX_ALERTS_DISPLAY', 'ALERT_RETENTION_MINUTES']
        
        has_all_keys = all(key in config for key in expected_keys)
        self.log_test("Configuration Loading", has_all_keys, f"Loaded {len(config)} settings")
        
        # Test 2: AlertManager Uses Configuration
        original_threshold = self.alert_manager.strong_buy_confidence_threshold
        
        # Update threshold and reload
        success = self.alert_manager.update_threshold('STRONG_BUY', 75)
        new_threshold = self.alert_manager.strong_buy_confidence_threshold
        
        threshold_updated = success and new_threshold == 75.0
        self.log_test("Threshold Update", threshold_updated, f"Updated from {original_threshold} to {new_threshold}")
        
        # Test 3: Configuration Persistence
        self.alert_manager.reload_config()
        reloaded_threshold = self.alert_manager.strong_buy_confidence_threshold
        
        persistence_works = reloaded_threshold == 75.0
        self.log_test("Configuration Persistence", persistence_works, f"Threshold persisted: {reloaded_threshold}")
        
        # Reset for other tests
        self.alert_manager.update_threshold('STRONG_BUY', original_threshold)
    
    def test_alert_management(self):
        """Test alert management functionality"""
        print("\n📋 Testing Alert Management...")
        
        # Clear existing alerts
        self.alert_manager.clear_all_alerts()
        
        # Test 1: Alert Storage and Retrieval
        test_alerts = [
            self.create_test_data_strong_buy(),
            self.create_test_data_high_volatility(),
            self.create_test_data_volume_spike()
        ]
        
        created_alerts = []
        for test_data in test_alerts:
            alert = self.alert_manager.process_token_data(test_data)
            if alert:
                created_alerts.append(alert)
        
        active_alerts = self.alert_manager.get_active_alerts()
        storage_works = len(active_alerts) == len(created_alerts)
        self.log_test("Alert Storage", storage_works, f"Stored {len(active_alerts)} alerts")
        
        # Test 2: Alert Summary
        summary = self.alert_manager.get_alert_summary()
        summary_works = (
            'total_active_alerts' in summary and
            'alert_counts_by_type' in summary and
            summary['total_active_alerts'] == len(created_alerts)
        )
        self.log_test("Alert Summary", summary_works, f"Summary shows {summary['total_active_alerts']} alerts")
        
        # Test 3: Alert Clearing
        cleared_count = self.alert_manager.clear_all_alerts()
        remaining_alerts = self.alert_manager.get_active_alerts()
        
        clearing_works = cleared_count > 0 and len(remaining_alerts) == 0
        self.log_test("Alert Clearing", clearing_works, f"Cleared {cleared_count} alerts")
    
    def test_threshold_sensitivity(self):
        """Test alert sensitivity to threshold changes"""
        print("\n🎯 Testing Threshold Sensitivity...")
        
        # Create borderline test data
        borderline_data = {
            'symbol': 'TEST',
            'name': 'Test Token',
            'current_price': 1.0,
            'signal': 'STRONG BUY',
            'momentum_score': 79.0,  # Just below default threshold of 80
            'price_change_1h': 14.0,  # Just below default threshold of 15
            'price_change_24h': 10.0,
            'volume_mcap_ratio': 190.0,  # Just below default threshold of 200
            'market_cap': 1000000000,
            'volume_24h': 1900000000
        }
        
        # Test 1: No alerts with default thresholds
        alert = self.alert_manager.process_token_data(borderline_data)
        no_alert_default = alert is None
        self.log_test("No Alert at Default Thresholds", no_alert_default, "Correctly no alert created")
        
        # Test 2: Alert created with lowered thresholds
        self.alert_manager.update_threshold('STRONG_BUY', 75)
        self.alert_manager.update_threshold('VOLATILITY', 10)
        self.alert_manager.update_threshold('VOLUME_SPIKE', 150)
        
        alert = self.alert_manager.process_token_data(borderline_data)
        alert_with_lower_threshold = alert is not None
        self.log_test("Alert with Lower Thresholds", alert_with_lower_threshold, 
                     f"Created {alert.signal_type if alert else 'no'} alert")
        
        # Reset thresholds
        self.alert_manager.update_threshold('STRONG_BUY', 80)
        self.alert_manager.update_threshold('VOLATILITY', 15)
        self.alert_manager.update_threshold('VOLUME_SPIKE', 200)
    
    def test_signal_generator_integration(self):
        """Test integration with existing signal generation"""
        print("\n🔗 Testing Signal Generator Integration...")
        
        try:
            # Test with real market data (limited to avoid API rate limits)
            analyzed_df = self.coingecko_api.get_analyzed_solana_tokens(5)
            
            if not analyzed_df.empty:
                self.log_test("Market Data Retrieval", True, f"Retrieved {len(analyzed_df)} tokens")
                
                # Test processing real market data
                alerts_created = 0
                for _, token_data in analyzed_df.iterrows():
                    token_dict = token_data.to_dict()
                    alert = self.alert_manager.process_token_data(token_dict)
                    if alert:
                        alerts_created += 1
                
                integration_works = True  # If we got here without errors
                self.log_test("Real Data Processing", integration_works, 
                             f"Processed {len(analyzed_df)} tokens, created {alerts_created} alerts")
            else:
                self.log_test("Market Data Retrieval", False, "No market data available")
                
        except Exception as e:
            self.log_test("Signal Generator Integration", False, f"Error: {str(e)}")
    
    def generate_sample_alerts_for_dashboard(self) -> List[Dict]:
        """Generate sample alerts for dashboard testing"""
        print("\n🎭 Generating Sample Alerts for Dashboard...")
        
        # Clear existing alerts
        self.alert_manager.clear_all_alerts()
        
        # Create diverse sample alerts
        sample_data = [
            {
                'symbol': 'SOL',
                'signal': 'STRONG BUY',
                'momentum_score': 92.5,
                'price_change_1h': 8.2,
                'volume_mcap_ratio': 180.0,
                'current_price': 98.75
            },
            {
                'symbol': 'AVAX',
                'signal': 'BUY',
                'momentum_score': 65.0,
                'price_change_1h': 22.1,
                'volume_mcap_ratio': 140.0,
                'current_price': 45.20
            },
            {
                'symbol': 'MATIC',
                'signal': 'WATCH',
                'momentum_score': 70.0,
                'price_change_1h': 6.5,
                'volume_mcap_ratio': 280.0,
                'current_price': 0.92
            },
            {
                'symbol': 'DOT',
                'signal': 'STRONG BUY',
                'momentum_score': 87.3,
                'price_change_1h': 12.8,
                'volume_mcap_ratio': 160.0,
                'current_price': 7.45
            },
            {
                'symbol': 'ATOM',
                'signal': 'BUY',
                'momentum_score': 75.0,
                'price_change_1h': 18.9,
                'volume_mcap_ratio': 190.0,
                'current_price': 12.30
            }
        ]
        
        created_alerts = []
        for data in sample_data:
            # Add required fields
            full_data = {
                'name': f"{data['symbol']} Token",
                'market_cap': 10000000000,
                'volume_24h': 1000000000,
                'price_change_24h': 15.0,
                **data
            }
            
            alert = self.alert_manager.process_token_data(full_data)
            if alert:
                created_alerts.append({
                    'symbol': alert.symbol,
                    'signal_type': alert.signal_type,
                    'confidence_score': alert.confidence_score,
                    'timestamp': alert.timestamp.isoformat(),
                    'price': alert.price
                })
        
        self.log_test("Sample Alert Generation", len(created_alerts) > 0, 
                     f"Generated {len(created_alerts)} sample alerts")
        
        return created_alerts
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Alert System Integration Tests")
        print("=" * 60)
        
        # Run all test categories
        self.test_alert_creation()
        self.test_configuration_integration()
        self.test_alert_management()
        self.test_threshold_sensitivity()
        self.test_signal_generator_integration()
        
        # Generate sample alerts for dashboard testing
        sample_alerts = self.generate_sample_alerts_for_dashboard()
        
        # Print test summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {result['test']}")
            if result['message']:
                print(f"    {result['message']}")
        
        print(f"\n📈 OVERALL: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Alert system is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        print(f"\n🎭 Generated {len(sample_alerts)} sample alerts for dashboard testing")
        print("   Run the Streamlit dashboard to see them in action!")
        
        return passed_tests == total_tests

def main():
    """Run the test suite"""
    tester = AlertSystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)