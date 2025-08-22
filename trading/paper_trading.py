import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class VirtualPortfolio:
    def __init__(self, starting_balance: float = 10000.0):
        """Initialize virtual portfolio with starting balance"""
        self.starting_balance = starting_balance
        self.cash_balance = starting_balance
        self.positions = {}  # {symbol: {'quantity': float, 'avg_price': float, 'total_cost': float}}
        self.trade_history = []  # List of all executed trades
        self.portfolio_history = []  # Daily portfolio values for performance tracking
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Initialize portfolio value tracking
        self._update_portfolio_value()
    
    def get_current_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current total portfolio value including cash and positions"""
        try:
            total_value = self.cash_balance
            
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    position_value = position['quantity'] * current_prices[symbol]
                    total_value += position_value
                else:
                    self.logger.warning(f"No current price available for {symbol}")
                    # Use last known price or avg_price as fallback
                    position_value = position['quantity'] * position['avg_price']
                    total_value += position_value
            
            return total_value
        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {e}")
            return self.starting_balance
    
    def execute_virtual_trade(self, signal_data: Dict, position_size_usd: float) -> Dict:
        """Execute a virtual trade based on signal data"""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            signal_type = signal_data.get('signal', 'HOLD')
            current_price = signal_data.get('current_price', 0)
            confidence = signal_data.get('confidence_score', 0)
            
            # Validate trade parameters
            if current_price <= 0:
                return {'success': False, 'error': 'Invalid price'}
            
            if position_size_usd <= 0:
                return {'success': False, 'error': 'Invalid position size'}
            
            # Calculate quantity to trade
            quantity = position_size_usd / current_price
            
            # Execute trade based on signal type
            if signal_type in ['BUY', 'STRONG_BUY']:
                return self._execute_buy(symbol, quantity, current_price, signal_data)
            elif signal_type in ['SELL', 'AVOID']:
                return self._execute_sell(symbol, quantity, current_price, signal_data)
            else:
                return {'success': False, 'error': f'No action for signal: {signal_type}'}
                
        except Exception as e:
            self.logger.error(f"Error executing virtual trade: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_buy(self, symbol: str, quantity: float, price: float, signal_data: Dict) -> Dict:
        """Execute a virtual buy order"""
        try:
            total_cost = quantity * price
            
            # Check if we have enough cash
            if total_cost > self.cash_balance:
                return {'success': False, 'error': 'Insufficient cash balance'}
            
            # Update cash balance
            self.cash_balance -= total_cost
            
            # Update position
            if symbol in self.positions:
                # Add to existing position
                old_quantity = self.positions[symbol]['quantity']
                old_total_cost = self.positions[symbol]['total_cost']
                new_quantity = old_quantity + quantity
                new_total_cost = old_total_cost + total_cost
                new_avg_price = new_total_cost / new_quantity
                
                self.positions[symbol] = {
                    'quantity': new_quantity,
                    'avg_price': new_avg_price,
                    'total_cost': new_total_cost
                }
            else:
                # Create new position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'total_cost': total_cost
                }
            
            # Log trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': 'BUY',
                'quantity': quantity,
                'price': price,
                'total_value': total_cost,
                'signal_data': signal_data,
                'cash_balance_after': self.cash_balance,
                'trade_id': f"BUY_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            self.trade_history.append(trade_record)
            self.total_trades += 1
            
            self.logger.info(f"Virtual BUY executed: {quantity:.4f} {symbol} at ${price:.4f}")
            
            return {
                'success': True,
                'trade_record': trade_record,
                'new_position': self.positions[symbol].copy(),
                'remaining_cash': self.cash_balance
            }
            
        except Exception as e:
            self.logger.error(f"Error executing buy order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_sell(self, symbol: str, quantity: float, price: float, signal_data: Dict) -> Dict:
        """Execute a virtual sell order"""
        try:
            # Check if we have the position
            if symbol not in self.positions:
                return {'success': False, 'error': f'No position in {symbol} to sell'}
            
            current_position = self.positions[symbol]
            
            # Check if we have enough quantity
            if quantity > current_position['quantity']:
                # Sell entire position if requested quantity is more than we have
                quantity = current_position['quantity']
            
            total_proceeds = quantity * price
            
            # Calculate P&L for this trade
            avg_cost = current_position['avg_price']
            pnl = (price - avg_cost) * quantity
            pnl_percentage = (price - avg_cost) / avg_cost * 100
            
            # Update cash balance
            self.cash_balance += total_proceeds
            
            # Update position
            remaining_quantity = current_position['quantity'] - quantity
            if remaining_quantity <= 0.0001:  # Close position if very small remainder
                del self.positions[symbol]
                remaining_quantity = 0
            else:
                # Reduce position size, keep same average price
                remaining_cost = remaining_quantity * current_position['avg_price']
                self.positions[symbol] = {
                    'quantity': remaining_quantity,
                    'avg_price': current_position['avg_price'],
                    'total_cost': remaining_cost
                }
            
            # Track win/loss
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Log trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': 'SELL',
                'quantity': quantity,
                'price': price,
                'total_value': total_proceeds,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'avg_cost': avg_cost,
                'signal_data': signal_data,
                'cash_balance_after': self.cash_balance,
                'remaining_position': remaining_quantity,
                'trade_id': f"SELL_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            self.trade_history.append(trade_record)
            self.total_trades += 1
            
            self.logger.info(f"Virtual SELL executed: {quantity:.4f} {symbol} at ${price:.4f}, P&L: ${pnl:.2f}")
            
            return {
                'success': True,
                'trade_record': trade_record,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'remaining_cash': self.cash_balance,
                'remaining_position': remaining_quantity
            }
            
        except Exception as e:
            self.logger.error(f"Error executing sell order: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_performance_metrics(self, current_prices: Dict[str, float]) -> Dict:
        """Calculate comprehensive performance metrics"""
        try:
            current_value = self.get_current_portfolio_value(current_prices)
            total_return = (current_value - self.starting_balance) / self.starting_balance
            total_return_percentage = total_return * 100
            
            # Calculate win rate
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            # Calculate basic Sharpe ratio (simplified)
            if len(self.portfolio_history) > 1:
                returns = []
                for i in range(1, len(self.portfolio_history)):
                    daily_return = (self.portfolio_history[i]['value'] - self.portfolio_history[i-1]['value']) / self.portfolio_history[i-1]['value']
                    returns.append(daily_return)
                
                if len(returns) > 0 and np.std(returns) > 0:
                    avg_return = np.mean(returns)
                    return_std = np.std(returns)
                    sharpe_ratio = (avg_return / return_std) * np.sqrt(252)  # Annualized
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
            
            # Calculate maximum drawdown
            max_drawdown = self._calculate_max_drawdown()
            
            # Calculate total P&L from closed positions
            total_realized_pnl = sum([
                trade.get('pnl', 0) for trade in self.trade_history 
                if trade.get('side') == 'SELL' and 'pnl' in trade
            ])
            
            # Calculate unrealized P&L from open positions
            unrealized_pnl = 0
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    current_market_value = position['quantity'] * current_prices[symbol]
                    unrealized_pnl += (current_market_value - position['total_cost'])
            
            return {
                'current_portfolio_value': current_value,
                'starting_balance': self.starting_balance,
                'total_return': total_return,
                'total_return_percentage': total_return_percentage,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_realized_pnl': total_realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'cash_balance': self.cash_balance,
                'positions_count': len(self.positions),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {
                'error': str(e),
                'current_portfolio_value': self.starting_balance,
                'total_return_percentage': 0.0
            }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from portfolio history"""
        try:
            if len(self.portfolio_history) < 2:
                return 0.0
            
            values = [entry['value'] for entry in self.portfolio_history]
            peak = values[0]
            max_dd = 0.0
            
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
            
            return max_dd * 100  # Return as percentage
            
        except Exception as e:
            self.logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def _update_portfolio_value(self, current_prices: Dict[str, float] = None):
        """Update portfolio value history for performance tracking"""
        try:
            if current_prices is None:
                current_prices = {}
            
            current_value = self.get_current_portfolio_value(current_prices)
            
            portfolio_snapshot = {
                'timestamp': datetime.now().isoformat(),
                'value': current_value,
                'cash': self.cash_balance,
                'positions': self.positions.copy()
            }
            
            self.portfolio_history.append(portfolio_snapshot)
            
            # Keep only last 30 days of history to prevent memory bloat
            if len(self.portfolio_history) > 30:
                self.portfolio_history = self.portfolio_history[-30:]
                
        except Exception as e:
            self.logger.error(f"Error updating portfolio value: {e}")
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            performance = self.calculate_performance_metrics(current_prices)
            
            # Position details
            position_details = []
            for symbol, position in self.positions.items():
                current_price = current_prices.get(symbol, position['avg_price'])
                market_value = position['quantity'] * current_price
                unrealized_pnl = market_value - position['total_cost']
                unrealized_pnl_pct = (unrealized_pnl / position['total_cost']) * 100
                
                position_details.append({
                    'symbol': symbol,
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': current_price,
                    'market_value': market_value,
                    'total_cost': position['total_cost'],
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_percentage': unrealized_pnl_pct
                })
            
            # Recent trades (last 10)
            recent_trades = self.trade_history[-10:] if len(self.trade_history) > 10 else self.trade_history
            
            return {
                'performance_metrics': performance,
                'position_details': position_details,
                'recent_trades': recent_trades,
                'cash_balance': self.cash_balance,
                'total_positions': len(self.positions),
                'total_trades_executed': len(self.trade_history)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}
    
    def save_portfolio_state(self, filepath: str = 'data/virtual_portfolio.json'):
        """Save portfolio state to file for persistence"""
        try:
            portfolio_state = {
                'starting_balance': self.starting_balance,
                'cash_balance': self.cash_balance,
                'positions': self.positions,
                'trade_history': self.trade_history,
                'portfolio_history': self.portfolio_history,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'last_saved': datetime.now().isoformat()
            }
            
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(portfolio_state, f, indent=2)
            
            self.logger.info(f"Portfolio state saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving portfolio state: {e}")
            return False
    
    def load_portfolio_state(self, filepath: str = 'data/virtual_portfolio.json'):
        """Load portfolio state from file"""
        try:
            with open(filepath, 'r') as f:
                portfolio_state = json.load(f)
            
            self.starting_balance = portfolio_state.get('starting_balance', 10000.0)
            self.cash_balance = portfolio_state.get('cash_balance', self.starting_balance)
            self.positions = portfolio_state.get('positions', {})
            self.trade_history = portfolio_state.get('trade_history', [])
            self.portfolio_history = portfolio_state.get('portfolio_history', [])
            self.total_trades = portfolio_state.get('total_trades', 0)
            self.winning_trades = portfolio_state.get('winning_trades', 0)
            self.losing_trades = portfolio_state.get('losing_trades', 0)
            
            self.logger.info(f"Portfolio state loaded from {filepath}")
            return True
            
        except FileNotFoundError:
            self.logger.info(f"No existing portfolio state found at {filepath}, starting fresh")
            return False
        except Exception as e:
            self.logger.error(f"Error loading portfolio state: {e}")
            return False


# Helper function for easy integration
def create_virtual_portfolio(starting_balance: float = 10000.0) -> VirtualPortfolio:
    """Factory function to create and optionally load existing virtual portfolio"""
    portfolio = VirtualPortfolio(starting_balance)
    portfolio.load_portfolio_state()  # Try to load existing state
    return portfolio

# Integration helper for signal system
def execute_signal_trade(portfolio: VirtualPortfolio, signal_data: Dict, position_size_usd: float = 500.0) -> Dict:
    """Helper function to execute trades based on signal data"""
    try:
        result = portfolio.execute_virtual_trade(signal_data, position_size_usd)
        
        # Auto-save portfolio state after each trade
        if result.get('success', False):
            portfolio.save_portfolio_state()
        
        return result
        
    except Exception as e:
        logging.error(f"Error executing signal trade: {e}")
        return {'success': False, 'error': str(e)}