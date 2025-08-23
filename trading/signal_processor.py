from trading.paper_trading import create_virtual_portfolio, execute_signal_trade
from datetime import datetime
import logging
import json

class SignalProcessor:
    def __init__(self):
        self.portfolio = create_virtual_portfolio()
        self.auto_trading = True
        self.min_confidence_buy = 75    # Only buy above 75% confidence
        self.min_confidence_sell = 60   # Sell above 60% confidence AVOID signals
        self.position_size_usd = 500    # $500 per trade
        self.logger = logging.getLogger(__name__)
        self.processed_signals = []     # Track all processed signals
        
    def process_new_signal(self, signal_data):
        """
        Main function: Takes a signal and decides whether to trade
        
        signal_data format:
        {
            'symbol': 'SOL',
            'signal': 'BUY',  # BUY, STRONG_BUY, SELL, AVOID, HOLD, WATCH
            'confidence_score': 85,
            'current_price': 183.99,
            'timestamp': '2025-08-21T23:48:16'
        }
        """
        if not self.auto_trading:
            self.logger.info(f"Auto-trading disabled, skipping signal: {signal_data}")
            return {'action': 'skipped', 'reason': 'auto_trading_disabled'}
        
        symbol = signal_data.get('symbol')
        signal_type = signal_data.get('signal')
        confidence = signal_data.get('confidence_score', 0)
        
        # DECISION LOGIC: When to act on signals
        trade_decision = self._make_trade_decision(signal_data)
        
        if trade_decision['should_trade']:
            result = self._execute_trade(signal_data, trade_decision['action'])
            
            # Log the decision and outcome for learning
            self._log_trade_decision(signal_data, trade_decision, result)
            return result
        else:
            self.logger.info(f"No trade: {signal_type} {symbol} {confidence}% - {trade_decision['reason']}")
            return {'action': 'no_trade', 'reason': trade_decision['reason']}
    
    def _make_trade_decision(self, signal_data):
        """Decide whether and how to trade based on signal"""
        symbol = signal_data.get('symbol')
        signal_type = signal_data.get('signal')
        confidence = signal_data.get('confidence_score', 0)
        
        # BUY DECISIONS
        if signal_type in ['BUY', 'STRONG_BUY']:
            if confidence >= self.min_confidence_buy:
                # Check if we already have this position
                if self._has_position(symbol):
                    return {'should_trade': False, 'reason': f'already_holding_{symbol}'}
                else:
                    return {'should_trade': True, 'action': 'BUY', 'reason': f'{signal_type}_above_threshold'}
            else:
                return {'should_trade': False, 'reason': f'confidence_{confidence}_below_buy_threshold_{self.min_confidence_buy}'}
        
        # SELL DECISIONS  
        elif signal_type in ['SELL', 'AVOID']:
            if confidence >= self.min_confidence_sell:
                if self._has_position(symbol):
                    return {'should_trade': True, 'action': 'SELL', 'reason': f'{signal_type}_exit_signal'}
                else:
                    return {'should_trade': False, 'reason': f'no_position_to_sell_{symbol}'}
            else:
                return {'should_trade': False, 'reason': f'confidence_{confidence}_below_sell_threshold_{self.min_confidence_sell}'}
        
        # HOLD/WATCH - No action
        else:
            return {'should_trade': False, 'reason': f'{signal_type}_signal_no_action_required'}
    
    def _execute_trade(self, signal_data, action):
        """Execute the actual trade"""
        try:
            if action == 'BUY':
                result = execute_signal_trade(self.portfolio, signal_data, self.position_size_usd)
                if result.get('success'):
                    self.logger.info(f"✅ BUY executed: {signal_data['symbol']} ${self.position_size_usd}")
                return result
            
            elif action == 'SELL':
                symbol = signal_data.get('symbol')
                position = self.portfolio.positions.get(symbol, {})
                quantity = position.get('quantity', 0)
                price = signal_data.get('current_price', position.get('avg_price', 0))
                
                result = self.portfolio._execute_sell(symbol, quantity, price, signal_data)
                if result.get('success'):
                    pnl = result.get('pnl', 0)
                    self.logger.info(f"✅ SELL executed: {symbol} P&L: ${pnl:.2f}")
                return result
                
        except Exception as e:
            self.logger.error(f"Trade execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _has_position(self, symbol):
        """Check if we currently hold this symbol"""
        return symbol in self.portfolio.positions and self.portfolio.positions[symbol]['quantity'] > 0
    
    def _log_trade_decision(self, signal_data, decision, result):
        """Log every signal and decision for learning"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'signal': signal_data,
            'decision': decision,
            'trade_result': result,
            'portfolio_value_after': self.portfolio.get_current_portfolio_value({})
        }
        self.processed_signals.append(log_entry)
    
    def get_daily_performance_data(self):
        """Get all data needed for tomorrow's training"""
        return {
            'processed_signals': self.processed_signals,
            'trade_history': self.portfolio.trade_history,
            'portfolio_history': self.portfolio.portfolio_history,
            'final_portfolio_value': self.portfolio.get_current_portfolio_value({}),
            'total_trades': self.portfolio.total_trades,
            'winning_trades': self.portfolio.winning_trades,
            'losing_trades': self.portfolio.losing_trades
        }