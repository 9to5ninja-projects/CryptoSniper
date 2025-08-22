#!/usr/bin/env python3
"""
Test script for paper trading integration
Tests the complete flow from signal generation to paper trading execution
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from trading.paper_trading import create_virtual_portfolio, execute_signal_trade
from trading.signal_integration import create_auto_trading_engine
from dashboard.components.alert_manager import AlertManager
from api_clients.coingecko_api import CoinGeckoAPI

def test_paper_trading_integration():
    """Test the complete paper trading integration"""
    print("🧪 Testing Paper Trading Integration")
    print("=" * 50)
    
    # Step 1: Create portfolio
    print("\n1. Creating virtual portfolio...")
    portfolio = create_virtual_portfolio(10000.0)
    print(f"   ✅ Portfolio created with ${portfolio.cash_balance:,.2f}")
    
    # Step 2: Test manual trade execution
    print("\n2. Testing manual trade execution...")
    test_signal = {
        'symbol': 'SOL',
        'signal': 'STRONG_BUY',
        'current_price': 25.50,
        'confidence_score': 92.5
    }
    
    result = execute_signal_trade(portfolio, test_signal, 500.0)
    if result.get('success', False):
        print(f"   ✅ Manual trade executed: {test_signal['symbol']} - ${500}")
        print(f"   📊 New portfolio value: ${portfolio.get_current_portfolio_value({'SOL': 26.00}):,.2f}")
    else:
        print(f"   ❌ Manual trade failed: {result.get('error', 'Unknown error')}")
    
    # Step 3: Test portfolio summary
    print("\n3. Testing portfolio summary...")
    current_prices = {'SOL': 26.00}  # Simulate price increase
    summary = portfolio.get_portfolio_summary(current_prices)
    performance = summary['performance_metrics']
    
    print(f"   📈 Portfolio Value: ${performance['current_portfolio_value']:,.2f}")
    print(f"   💰 Total Return: {performance['total_return_percentage']:+.2f}%")
    print(f"   📊 Positions: {performance['positions_count']}")
    print(f"   🎯 Total Trades: {performance['total_trades']}")
    
    # Step 4: Test auto-trading engine
    print("\n4. Testing auto-trading engine...")
    try:
        alert_manager = AlertManager()
        coingecko_api = CoinGeckoAPI()
        
        auto_engine = create_auto_trading_engine(portfolio, alert_manager, coingecko_api)
        status = auto_engine.get_status()
        
        print(f"   ✅ Auto-trading engine created")
        print(f"   🔧 Status: {'Enabled' if status['enabled'] else 'Disabled'}")
        print(f"   ⚙️  Min Confidence: {status['min_confidence_threshold']:.0f}%")
        print(f"   💵 Default Position Size: ${status['default_position_size']:,.0f}")
        print(f"   📊 Max Positions: {status['max_positions']}")
        
    except Exception as e:
        print(f"   ❌ Auto-trading engine error: {e}")
    
    # Step 5: Test sell trade
    print("\n5. Testing sell trade...")
    sell_signal = {
        'symbol': 'SOL',
        'signal': 'SELL',
        'current_price': 27.25,
        'confidence_score': 88.0
    }
    
    result = execute_signal_trade(portfolio, sell_signal, 500.0)
    if result.get('success', False):
        pnl = result.get('pnl', 0)
        print(f"   ✅ Sell trade executed: {sell_signal['symbol']}")
        print(f"   💰 P&L: ${pnl:+,.2f}")
        print(f"   💵 New cash balance: ${portfolio.cash_balance:,.2f}")
    else:
        print(f"   ❌ Sell trade failed: {result.get('error', 'Unknown error')}")
    
    # Step 6: Final portfolio state
    print("\n6. Final portfolio state...")
    final_summary = portfolio.get_portfolio_summary(current_prices)
    final_performance = final_summary['performance_metrics']
    
    print(f"   📊 Final Portfolio Value: ${final_performance['current_portfolio_value']:,.2f}")
    print(f"   📈 Total Return: {final_performance['total_return_percentage']:+.2f}%")
    print(f"   🎯 Total Trades: {final_performance['total_trades']}")
    print(f"   🏆 Win Rate: {final_performance['win_rate']:.1f}%")
    print(f"   💰 Realized P&L: ${final_performance.get('total_realized_pnl', 0):+,.2f}")
    
    print("\n" + "=" * 50)
    print("🎉 Paper Trading Integration Test Complete!")
    
    return True

if __name__ == "__main__":
    try:
        test_paper_trading_integration()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)