import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
from trading.paper_trading import VirtualPortfolio, execute_signal_trade

class AutoTradingEngine:
    """Automated paper trading engine that monitors signals and executes trades"""
    
    def __init__(self, portfolio: VirtualPortfolio, alert_manager, coingecko_api):
        self.portfolio = portfolio
        self.alert_manager = alert_manager
        self.coingecko_api = coingecko_api
        self.logger = logging.getLogger(__name__)
        
        # Auto-trading settings
        self.enabled = False
        self.min_confidence_threshold = 85.0  # Only trade signals with 85%+ confidence
        self.default_position_size = 500.0    # Default $500 per trade
        self.max_positions = 10               # Maximum number of open positions
        self.cooldown_period = 300            # 5 minutes between trades for same symbol
        
        # Tracking
        self.last_trade_times = {}            # Track last trade time per symbol
        self.processed_alerts = set()         # Track processed alert IDs
        self.auto_trades_executed = 0
        self.monitoring_thread = None
        self.stop_monitoring = False
    
    def start_monitoring(self):
        """Start the automated trading monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.logger.warning("Monitoring thread already running")
            return False
        
        self.enabled = True
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Auto-trading monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop the automated trading monitoring"""
        self.enabled = False
        self.stop_monitoring = True
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Auto-trading monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in background thread"""
        self.logger.info("Auto-trading monitoring loop started")
        
        while not self.stop_monitoring and self.enabled:
            try:
                # Check for new high-confidence signals
                self._process_new_signals()
                
                # Check for position exit signals
                self._check_exit_signals()
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
        
        self.logger.info("Auto-trading monitoring loop ended")
    
    def _process_new_signals(self):
        """Process new high-confidence signals for auto-trading"""
        try:
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            
            for alert in active_alerts:
                # Skip if already processed
                if alert['id'] in self.processed_alerts:
                    continue
                
                # Check if signal meets criteria for auto-trading
                if self._should_auto_trade(alert):
                    self._execute_auto_trade(alert)
                
                # Mark as processed
                self.processed_alerts.add(alert['id'])
                
        except Exception as e:
            self.logger.error(f"Error processing new signals: {e}")
    
    def _should_auto_trade(self, alert: Dict) -> bool:
        """Determine if an alert should trigger an auto-trade"""
        try:
            # Check confidence threshold
            if alert['confidence_score'] < self.min_confidence_threshold:
                return False
            
            # Only trade BUY and STRONG_BUY signals automatically
            if alert['signal_type'] not in ['BUY', 'STRONG_BUY']:
                return False
            
            # Check position limits
            if len(self.portfolio.positions) >= self.max_positions:
                self.logger.info(f"Max positions ({self.max_positions}) reached, skipping auto-trade")
                return False
            
            # Check cooldown period
            symbol = alert['symbol']
            current_time = datetime.now()
            
            if symbol in self.last_trade_times:
                time_since_last = current_time - self.last_trade_times[symbol]
                if time_since_last.total_seconds() < self.cooldown_period:
                    return False
            
            # Check if we already have a position in this symbol
            if symbol in self.portfolio.positions:
                self.logger.info(f"Already have position in {symbol}, skipping auto-trade")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking auto-trade criteria: {e}")
            return False
    
    def _execute_auto_trade(self, alert: Dict):
        """Execute an automated trade based on alert"""
        try:
            symbol = alert['symbol']
            
            # Get current price from CoinGecko API
            current_price = self._get_current_price(symbol)
            if current_price is None:
                self.logger.warning(f"Could not get current price for {symbol}, skipping auto-trade")
                return
            
            # Create signal data
            signal_data = {
                'symbol': symbol,
                'signal': alert['signal_type'],
                'current_price': current_price,
                'confidence_score': alert['confidence_score']
            }
            
            # Execute the trade
            result = execute_signal_trade(self.portfolio, signal_data, self.default_position_size)
            
            if result.get('success', False):
                self.auto_trades_executed += 1
                self.last_trade_times[symbol] = datetime.now()
                
                self.logger.info(
                    f"Auto-trade executed: {symbol} - {alert['signal_type']} - "
                    f"${self.default_position_size} - Confidence: {alert['confidence_score']:.1f}%"
                )
            else:
                self.logger.error(f"Auto-trade failed for {symbol}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Error executing auto-trade: {e}")
    
    def _check_exit_signals(self):
        """Check for signals to exit existing positions"""
        try:
            # Get current positions
            if not self.portfolio.positions:
                return
            
            # Get active alerts for exit signals
            active_alerts = self.alert_manager.get_active_alerts()
            
            for alert in active_alerts:
                symbol = alert['symbol']
                
                # Check if we have a position in this symbol
                if symbol not in self.portfolio.positions:
                    continue
                
                # Check for exit signals (AVOID, SELL)
                if alert['signal_type'] in ['AVOID', 'SELL']:
                    self._execute_auto_exit(alert)
                    
        except Exception as e:
            self.logger.error(f"Error checking exit signals: {e}")
    
    def _execute_auto_exit(self, alert: Dict):
        """Execute an automated position exit"""
        try:
            symbol = alert['symbol']
            
            # Get current price
            current_price = self._get_current_price(symbol)
            if current_price is None:
                self.logger.warning(f"Could not get current price for {symbol}, skipping auto-exit")
                return
            
            # Get position size to sell
            position = self.portfolio.positions[symbol]
            position_size_usd = position['quantity'] * current_price
            
            # Create signal data for exit
            signal_data = {
                'symbol': symbol,
                'signal': alert['signal_type'],
                'current_price': current_price,
                'confidence_score': alert['confidence_score']
            }
            
            # Execute the exit trade
            result = execute_signal_trade(self.portfolio, signal_data, position_size_usd)
            
            if result.get('success', False):
                self.auto_trades_executed += 1
                self.last_trade_times[symbol] = datetime.now()
                
                pnl = result.get('pnl', 0)
                self.logger.info(
                    f"Auto-exit executed: {symbol} - {alert['signal_type']} - "
                    f"P&L: ${pnl:+.2f} - Confidence: {alert['confidence_score']:.1f}%"
                )
            else:
                self.logger.error(f"Auto-exit failed for {symbol}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Error executing auto-exit: {e}")
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Try to get from analyzed tokens
            analyzed_df = self.coingecko_api.get_analyzed_solana_tokens(limit=100)
            
            if not analyzed_df.empty:
                symbol_data = analyzed_df[analyzed_df['symbol'] == symbol]
                if not symbol_data.empty:
                    return float(symbol_data.iloc[0]['current_price'])
            
            # Fallback: could implement direct price lookup here
            self.logger.warning(f"Could not find current price for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_status(self) -> Dict:
        """Get current status of the auto-trading engine"""
        return {
            'enabled': self.enabled,
            'monitoring_active': self.monitoring_thread and self.monitoring_thread.is_alive(),
            'auto_trades_executed': self.auto_trades_executed,
            'processed_alerts_count': len(self.processed_alerts),
            'current_positions': len(self.portfolio.positions),
            'max_positions': self.max_positions,
            'min_confidence_threshold': self.min_confidence_threshold,
            'default_position_size': self.default_position_size,
            'cooldown_period': self.cooldown_period
        }
    
    def update_settings(self, **kwargs):
        """Update auto-trading settings"""
        if 'min_confidence_threshold' in kwargs:
            self.min_confidence_threshold = float(kwargs['min_confidence_threshold'])
        
        if 'default_position_size' in kwargs:
            self.default_position_size = float(kwargs['default_position_size'])
        
        if 'max_positions' in kwargs:
            self.max_positions = int(kwargs['max_positions'])
        
        if 'cooldown_period' in kwargs:
            self.cooldown_period = int(kwargs['cooldown_period'])
        
        self.logger.info(f"Auto-trading settings updated: {kwargs}")
    
    def clear_processed_alerts(self):
        """Clear the processed alerts cache"""
        self.processed_alerts.clear()
        self.logger.info("Processed alerts cache cleared")


# Helper functions for easy integration
def create_auto_trading_engine(portfolio: VirtualPortfolio, alert_manager, coingecko_api) -> AutoTradingEngine:
    """Factory function to create auto-trading engine"""
    return AutoTradingEngine(portfolio, alert_manager, coingecko_api)

def setup_auto_trading(portfolio: VirtualPortfolio, alert_manager, coingecko_api, 
                      min_confidence: float = 85.0, position_size: float = 500.0) -> AutoTradingEngine:
    """Setup and start auto-trading with specified parameters"""
    engine = create_auto_trading_engine(portfolio, alert_manager, coingecko_api)
    
    engine.update_settings(
        min_confidence_threshold=min_confidence,
        default_position_size=position_size
    )
    
    return engine