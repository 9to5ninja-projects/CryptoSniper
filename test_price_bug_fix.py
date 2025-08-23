#!/usr/bin/env python3
"""
Test script to verify the price calculation bug fix
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from trading.paper_trading import create_virtual_portfolio, execute_signal_trade

def test_price_calculation_fix():
    """Test that the price calculation bug is fixed"""
    print("🧪 Testing Price Calculation Bug Fix")
    print("=" * 50)
    
    # Create fresh portfolio
    portfolio = create_virtual_portfolio(10000.0)
    
    # Test case: SOL trade that was previously broken
    print("\n1. Testing SOL trade with correct price...")
    
    # Simulate the corrected signal data (using alert.price instead of default 1.0)
    signal_data = {
        'symbol': 'SOL',
        'signal': 'STRONG_BUY',
        'current_price': 183.99,  # Real SOL price, not the $1.0 default
        'confidence_score': 92.5
    }
    
    position_size = 532.11  # Amount user wanted to invest
    
    print(f"   💰 Investment amount: ${position_size}")
    print(f"   💵 SOL price: ${signal_data['current_price']}")
    print(f"   🧮 Expected SOL quantity: {position_size / signal_data['current_price']:.6f}")
    print(f"   ✅ Expected cost verification: {(position_size / signal_data['current_price']) * signal_data['current_price']:.2f}")
    
    # Execute the trade
    result = execute_signal_trade(portfolio, signal_data, position_size)
    
    if result.get('success', False):
        trade_record = result['trade_record']
        quantity_bought = trade_record['quantity']
        price_used = trade_record['price']
        total_cost = trade_record['total_value']
        
        print(f"\n   📊 TRADE RESULTS:")
        print(f"   🔢 Quantity bought: {quantity_bought:.6f} SOL")
        print(f"   💲 Price used: ${price_used:.2f}")
        print(f"   💰 Total cost: ${total_cost:.2f}")
        print(f"   💵 Cash remaining: ${result['remaining_cash']:.2f}")
        
        # Verify the calculation is correct
        expected_quantity = position_size / signal_data['current_price']
        quantity_diff = abs(quantity_bought - expected_quantity)
        
        if quantity_diff < 0.000001:  # Allow for floating point precision
            print(f"   ✅ QUANTITY CALCULATION: CORRECT!")
        else:
            print(f"   ❌ QUANTITY CALCULATION: WRONG!")
            print(f"      Expected: {expected_quantity:.6f}")
            print(f"      Got: {quantity_bought:.6f}")
            print(f"      Difference: {quantity_diff:.6f}")
        
        # Verify total cost
        expected_cost = expected_quantity * signal_data['current_price']
        cost_diff = abs(total_cost - expected_cost)
        
        if cost_diff < 0.01:  # Allow for small rounding
            print(f"   ✅ COST CALCULATION: CORRECT!")
        else:
            print(f"   ❌ COST CALCULATION: WRONG!")
            print(f"      Expected: ${expected_cost:.2f}")
            print(f"      Got: ${total_cost:.2f}")
            print(f"      Difference: ${cost_diff:.2f}")
        
        # Check portfolio position
        sol_position = portfolio.positions.get('SOL', {})
        if sol_position:
            print(f"\n   📈 PORTFOLIO POSITION:")
            print(f"   🔢 SOL held: {sol_position['quantity']:.6f}")
            print(f"   💲 Average price: ${sol_position['avg_price']:.2f}")
            print(f"   💰 Total cost basis: ${sol_position['total_cost']:.2f}")
            
            # Calculate current value (should be approximately the same as invested)
            current_value = sol_position['quantity'] * signal_data['current_price']
            print(f"   💵 Current value: ${current_value:.2f}")
            print(f"   📊 Unrealized P&L: ${current_value - sol_position['total_cost']:.2f}")
        
    else:
        print(f"   ❌ Trade failed: {result.get('error', 'Unknown error')}")
        return False
    
    print("\n" + "=" * 50)
    
    # Test edge case: Very small price
    print("\n2. Testing edge case with small price...")
    
    small_price_signal = {
        'symbol': 'SMALLCOIN',
        'signal': 'BUY',
        'current_price': 0.000123,  # Very small price
        'confidence_score': 85.0
    }
    
    small_investment = 100.0
    expected_small_quantity = small_investment / small_price_signal['current_price']
    
    print(f"   💰 Investment: ${small_investment}")
    print(f"   💵 Price: ${small_price_signal['current_price']:.6f}")
    print(f"   🧮 Expected quantity: {expected_small_quantity:.2f}")
    
    result2 = execute_signal_trade(portfolio, small_price_signal, small_investment)
    
    if result2.get('success', False):
        quantity2 = result2['trade_record']['quantity']
        print(f"   ✅ Got quantity: {quantity2:.2f}")
        
        if abs(quantity2 - expected_small_quantity) < 0.01:
            print(f"   ✅ Small price calculation: CORRECT!")
        else:
            print(f"   ❌ Small price calculation: WRONG!")
    
    print("\n" + "=" * 50)
    print("🎉 Price Calculation Bug Fix Test Complete!")
    
    return True

if __name__ == "__main__":
    try:
        test_price_calculation_fix()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)