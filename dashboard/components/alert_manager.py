import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pandas as pd

# Import the existing CoinGecko API for signal integration
import sys
import os

# Add the project root to Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api_clients.coingecko_api import CoinGeckoAPI
from config.settings import get_alert_config, save_alert_settings

@dataclass
class Alert:
    """Data class for storing alert information"""
    id: str
    symbol: str
    signal_type: str
    confidence_score: float
    timestamp: datetime
    price: float
    message: str
    alert_condition: str
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Alert':
        """Create alert from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class AlertManager:
    """
    Alert Manager for cryptocurrency signals and market conditions.
    Integrates with existing signal generation to create actionable alerts.
    """
    
    def __init__(self, coingecko_api: Optional[CoinGeckoAPI] = None):
        """
        Initialize AlertManager
        
        Args:
            coingecko_api: Optional CoinGecko API instance. If None, creates new instance.
        """
        self.coingecko_api = coingecko_api or CoinGeckoAPI()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_check_time = None
        
        # Load alert configuration from settings
        self.config = get_alert_config()
        self.alerts_enabled = self.config['ENABLE_ALERTS']
        self.strong_buy_confidence_threshold = float(self.config['STRONG_BUY_THRESHOLD'])
        self.high_volatility_threshold = float(self.config['VOLATILITY_THRESHOLD'])
        self.volume_spike_threshold = float(self.config['VOLUME_SPIKE_THRESHOLD'])
        self.max_alerts_display = self.config['MAX_ALERTS_DISPLAY']
        self.alert_retention_minutes = self.config['ALERT_RETENTION_MINUTES']
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("AlertManager initialized successfully with config-based thresholds")
    
    def generate_alert_id(self, symbol: str, alert_type: str) -> str:
        """Generate unique alert ID"""
        timestamp = int(time.time())
        return f"{symbol}_{alert_type}_{timestamp}"
    
    def check_signal_threshold(self, signal_data: Dict) -> bool:
        """
        Check if signal data meets alert threshold criteria
        
        Args:
            signal_data: Dictionary containing token analysis data
            
        Returns:
            bool: True if alert should be created
        """
        try:
            signal = signal_data.get('signal', '')
            momentum_score = signal_data.get('momentum_score', 0)
            price_change_1h = signal_data.get('price_change_1h', 0)
            volume_mcap_ratio = signal_data.get('volume_mcap_ratio', 0)
            
            # Strong Buy signals with high confidence
            if signal == 'STRONG BUY' and momentum_score > self.strong_buy_confidence_threshold:
                return True
            
            # High volatility alerts
            if abs(price_change_1h) > self.high_volatility_threshold:
                return True
            
            # Volume spike alerts
            if volume_mcap_ratio > self.volume_spike_threshold:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking signal threshold: {e}")
            return False
    
    def create_alert(self, symbol: str, signal_type: str, confidence_score: float, 
                    price: float = 0, additional_data: Dict = None) -> Optional[Alert]:
        """
        Create a new alert
        
        Args:
            symbol: Token symbol
            signal_type: Type of signal/alert
            confidence_score: Confidence score (0-100)
            price: Current token price
            additional_data: Additional data for alert context
            
        Returns:
            Alert: Created alert object or None if creation failed
        """
        try:
            additional_data = additional_data or {}
            
            # Generate alert ID and message
            alert_id = self.generate_alert_id(symbol, signal_type)
            
            # Create contextual message based on signal type
            if signal_type == 'STRONG_BUY':
                message = f"Strong buy signal detected for {symbol} with {confidence_score:.1f}% confidence"
                alert_condition = f"Momentum score > {self.strong_buy_confidence_threshold}%"
            elif signal_type == 'HIGH_VOLATILITY':
                price_change = additional_data.get('price_change_1h', 0)
                message = f"High volatility alert for {symbol}: {price_change:+.2f}% in 1 hour"
                alert_condition = f"Price change > {self.high_volatility_threshold}%"
            elif signal_type == 'VOLUME_SPIKE':
                volume_ratio = additional_data.get('volume_mcap_ratio', 0)
                message = f"Volume spike detected for {symbol}: {volume_ratio:.1f}% volume/mcap ratio"
                alert_condition = f"Volume ratio > {self.volume_spike_threshold}%"
            else:
                message = f"Alert for {symbol}: {signal_type}"
                alert_condition = "Custom condition"
            
            # Create alert object
            alert = Alert(
                id=alert_id,
                symbol=symbol,
                signal_type=signal_type,
                confidence_score=confidence_score,
                timestamp=datetime.now(),
                price=price,
                message=message,
                alert_condition=alert_condition,
                is_active=True
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            self.logger.info(f"Created alert: {message}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Error creating alert for {symbol}: {e}")
            return None
    
    def get_active_alerts(self) -> List[Dict]:
        """
        Get all active alerts
        
        Returns:
            List[Dict]: List of active alerts as dictionaries
        """
        try:
            active_alerts = [alert.to_dict() for alert in self.active_alerts.values() if alert.is_active]
            return sorted(active_alerts, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []
    
    def clear_old_alerts(self, max_age_minutes: int = 60) -> int:
        """
        Clear alerts older than specified age
        
        Args:
            max_age_minutes: Maximum age of alerts in minutes
            
        Returns:
            int: Number of alerts cleared
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            cleared_count = 0
            
            # Mark old alerts as inactive
            for alert_id, alert in self.active_alerts.items():
                if alert.timestamp < cutoff_time:
                    alert.is_active = False
                    cleared_count += 1
            
            # Remove inactive alerts from active list
            self.active_alerts = {
                alert_id: alert for alert_id, alert in self.active_alerts.items() 
                if alert.is_active
            }
            
            if cleared_count > 0:
                self.logger.info(f"Cleared {cleared_count} old alerts")
            
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing old alerts: {e}")
            return 0
    
    def remove_alert(self, alert_id: str) -> bool:
        """
        Remove specific alert by ID
        
        Args:
            alert_id: ID of alert to remove
            
        Returns:
            bool: True if alert was removed successfully
        """
        try:
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].is_active = False
                del self.active_alerts[alert_id]
                self.logger.info(f"Removed alert: {alert_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing alert {alert_id}: {e}")
            return False
    
    def process_token_data(self, token_data: Dict) -> Optional[Alert]:
        """
        Process individual token data and create alerts if conditions are met
        
        Args:
            token_data: Token analysis data from CoinGecko API
            
        Returns:
            Alert: Created alert or None
        """
        try:
            symbol = token_data.get('symbol', 'UNKNOWN')
            price = token_data.get('current_price', 0)
            
            # Check if alert should be created
            if not self.check_signal_threshold(token_data):
                return None
            
            # Determine alert type and create appropriate alert
            signal = token_data.get('signal', '')
            momentum_score = token_data.get('momentum_score', 0)
            price_change_1h = token_data.get('price_change_1h', 0)
            volume_mcap_ratio = token_data.get('volume_mcap_ratio', 0)
            
            # Strong buy signal
            if signal == 'STRONG BUY' and momentum_score > self.strong_buy_confidence_threshold:
                return self.create_alert(
                    symbol=symbol,
                    signal_type='STRONG_BUY',
                    confidence_score=momentum_score,
                    price=price,
                    additional_data=token_data
                )
            
            # High volatility alert
            elif abs(price_change_1h) > self.high_volatility_threshold:
                return self.create_alert(
                    symbol=symbol,
                    signal_type='HIGH_VOLATILITY',
                    confidence_score=abs(price_change_1h),
                    price=price,
                    additional_data=token_data
                )
            
            # Volume spike alert
            elif volume_mcap_ratio > self.volume_spike_threshold:
                return self.create_alert(
                    symbol=symbol,
                    signal_type='VOLUME_SPIKE',
                    confidence_score=volume_mcap_ratio,
                    price=price,
                    additional_data=token_data
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing token data: {e}")
            return None
    
    def scan_for_alerts(self, limit: int = 25) -> List[Alert]:
        """
        Scan current market data for alert conditions
        
        Args:
            limit: Number of tokens to analyze
            
        Returns:
            List[Alert]: List of newly created alerts
        """
        try:
            self.logger.info(f"Scanning {limit} tokens for alert conditions...")
            
            # Get analyzed token data
            analyzed_df = self.coingecko_api.get_analyzed_solana_tokens(limit)
            
            if analyzed_df.empty:
                self.logger.warning("No token data available for alert scanning")
                return []
            
            new_alerts = []
            
            # Process each token
            for _, token_data in analyzed_df.iterrows():
                token_dict = token_data.to_dict()
                alert = self.process_token_data(token_dict)
                if alert:
                    new_alerts.append(alert)
            
            # Clear old alerts
            self.clear_old_alerts()
            
            # Update last check time
            self.last_check_time = datetime.now()
            
            self.logger.info(f"Alert scan complete. Created {len(new_alerts)} new alerts")
            return new_alerts
            
        except Exception as e:
            self.logger.error(f"Error during alert scan: {e}")
            return []
    
    def reload_config(self) -> bool:
        """
        Reload configuration from settings file
        
        Returns:
            bool: True if config was reloaded successfully
        """
        try:
            self.config = get_alert_config()
            self.alerts_enabled = self.config['ENABLE_ALERTS']
            self.strong_buy_confidence_threshold = float(self.config['STRONG_BUY_THRESHOLD'])
            self.high_volatility_threshold = float(self.config['VOLATILITY_THRESHOLD'])
            self.volume_spike_threshold = float(self.config['VOLUME_SPIKE_THRESHOLD'])
            self.max_alerts_display = self.config['MAX_ALERTS_DISPLAY']
            self.alert_retention_minutes = self.config['ALERT_RETENTION_MINUTES']
            
            self.logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False
    
    def update_threshold(self, threshold_type: str, new_value: float) -> bool:
        """
        Update a specific threshold value
        
        Args:
            threshold_type: Type of threshold ('STRONG_BUY', 'VOLATILITY', 'VOLUME_SPIKE')
            new_value: New threshold value
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update the instance variable
            if threshold_type == 'STRONG_BUY':
                self.strong_buy_confidence_threshold = float(new_value)
                self.config['STRONG_BUY_THRESHOLD'] = new_value
            elif threshold_type == 'VOLATILITY':
                self.high_volatility_threshold = float(new_value)
                self.config['VOLATILITY_THRESHOLD'] = new_value
            elif threshold_type == 'VOLUME_SPIKE':
                self.volume_spike_threshold = float(new_value)
                self.config['VOLUME_SPIKE_THRESHOLD'] = new_value
            else:
                self.logger.error(f"Unknown threshold type: {threshold_type}")
                return False
            
            # Save to configuration file
            if save_alert_settings(self.config):
                self.logger.info(f"Updated {threshold_type} threshold to {new_value}")
                return True
            else:
                self.logger.error(f"Failed to save {threshold_type} threshold update")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating threshold: {e}")
            return False
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current configuration settings
        
        Returns:
            Dict containing current configuration
        """
        return {
            'alerts_enabled': self.alerts_enabled,
            'strong_buy_threshold': self.strong_buy_confidence_threshold,
            'volatility_threshold': self.high_volatility_threshold,
            'volume_spike_threshold': self.volume_spike_threshold,
            'max_alerts_display': self.max_alerts_display,
            'alert_retention_minutes': self.alert_retention_minutes,
            'full_config': self.config.copy()
        }
    
    def enable_alerts(self, enabled: bool = True) -> bool:
        """
        Enable or disable alert generation
        
        Args:
            enabled: Whether to enable alerts
            
        Returns:
            bool: True if setting was updated successfully
        """
        try:
            self.alerts_enabled = enabled
            self.config['ENABLE_ALERTS'] = enabled
            
            if save_alert_settings(self.config):
                status = "enabled" if enabled else "disabled"
                self.logger.info(f"Alerts {status}")
                return True
            else:
                self.logger.error("Failed to save alert enable/disable setting")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating alert enable setting: {e}")
            return False
    
    def clear_all_alerts(self) -> int:
        """
        Clear all active alerts
        
        Returns:
            int: Number of alerts cleared
        """
        try:
            cleared_count = len(self.active_alerts)
            
            # Mark all alerts as inactive
            for alert in self.active_alerts.values():
                alert.is_active = False
            
            # Clear the active alerts dictionary
            self.active_alerts.clear()
            
            if cleared_count > 0:
                self.logger.info(f"Cleared all {cleared_count} active alerts")
            
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing all alerts: {e}")
            return 0
    
    def get_alert_summary(self) -> Dict:
        """
        Get summary of current alert status
        
        Returns:
            Dict: Alert summary statistics
        """
        try:
            active_alerts = self.get_active_alerts()
            
            # Count alerts by type
            alert_counts = {}
            for alert in active_alerts:
                signal_type = alert['signal_type']
                alert_counts[signal_type] = alert_counts.get(signal_type, 0) + 1
            
            return {
                'total_active_alerts': len(active_alerts),
                'alert_types': alert_counts,
                'last_scan_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'total_historical_alerts': len(self.alert_history)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alert summary: {e}")
            return {
                'total_active_alerts': 0,
                'alert_types': {},
                'last_scan_time': None,
                'total_historical_alerts': 0
            }

# Test function
def test_alert_manager():
    """Test AlertManager functionality"""
    print("🚨 Testing AlertManager...")
    
    try:
        # Initialize AlertManager
        alert_manager = AlertManager()
        print("✅ AlertManager initialized")
        
        # Test manual alert creation
        test_alert = alert_manager.create_alert(
            symbol="SOL",
            signal_type="STRONG_BUY",
            confidence_score=85.0,
            price=100.50
        )
        
        if test_alert:
            print(f"✅ Created test alert: {test_alert.message}")
        
        # Test getting active alerts
        active_alerts = alert_manager.get_active_alerts()
        print(f"✅ Retrieved {len(active_alerts)} active alerts")
        
        # Test alert summary
        summary = alert_manager.get_alert_summary()
        print(f"✅ Alert summary: {summary['total_active_alerts']} active alerts")
        
        # Test live market scan (this will make API calls)
        print("\n🔍 Testing live market scan...")
        new_alerts = alert_manager.scan_for_alerts(limit=10)
        print(f"✅ Market scan complete. Found {len(new_alerts)} new alerts")
        
        # Display any new alerts
        if new_alerts:
            print("\n🚨 New Alerts Found:")
            for alert in new_alerts:
                print(f"  - {alert.message}")
        
        # Test clearing old alerts
        cleared = alert_manager.clear_old_alerts(max_age_minutes=0)  # Clear all for test
        print(f"✅ Cleared {cleared} alerts")
        
        print("\n✅ AlertManager test SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ AlertManager test failed: {e}")
        return False

if __name__ == "__main__":
    test_alert_manager()