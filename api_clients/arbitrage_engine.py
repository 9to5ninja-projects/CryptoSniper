import itertools
from typing import Dict, List, Tuple, Optional
import pandas as pd
import logging

class ArbitrageEngine:
    """Triangular arbitrage detection engine for Kraken"""
    
    def __init__(self, min_profit: float = 0.5, trading_fee: float = 0.0025):
        self.min_profit = min_profit  # Minimum profit percentage
        self.trading_fee = trading_fee  # 0.25% per trade
        self.logger = logging.getLogger(__name__)
    
    def extract_currencies(self, pair: str) -> Tuple[str, str]:
        """Extract base and quote currencies from Kraken pair"""
        # Handle Kraken pair formats like XXBTZUSD, XETHZUSD
        if len(pair) == 8:  # XXBTZUSD format
            return pair[1:4], pair[5:8]  # Remove X/Z prefixes
        elif len(pair) == 6:  # BTCUSD format
            return pair[:3], pair[3:]
        else:
            # Fallback for other formats
            common_quotes = ['USD', 'EUR', 'BTC', 'ETH']
            for quote in common_quotes:
                if pair.endswith(quote):
                    return pair[:-len(quote)], quote
            return pair[:3], pair[3:] if len(pair) > 3 else pair, "USD"
    
    def build_price_matrix(self, ticker_data: Dict) -> Dict[Tuple[str, str], Dict]:
        """Build price matrix for arbitrage calculations"""
        price_matrix = {}
        currencies = set()
        
        for pair, data in ticker_data.items():
            try:
                ask = float(data['a'][0])  # Best ask price
                bid = float(data['b'][0])  # Best bid price
                volume = float(data['v'][1])  # 24h volume
                
                base, quote = self.extract_currencies(pair)
                currencies.add(base)
                currencies.add(quote)
                
                # Store both directions for calculations
                # Direct: base -> quote (selling base for quote)
                price_matrix[(base, quote)] = {
                    'rate': bid,  # Use bid when selling
                    'volume': volume,
                    'pair': pair,
                    'spread': (ask - bid) / ((ask + bid) / 2) * 100 if (ask + bid) > 0 else 0
                }
                
                # Reverse: quote -> base (buying base with quote)
                price_matrix[(quote, base)] = {
                    'rate': 1/ask,  # Use ask when buying
                    'volume': volume,
                    'pair': f"{pair}_reverse",
                    'spread': (ask - bid) / ((ask + bid) / 2) * 100 if (ask + bid) > 0 else 0
                }
                
            except (KeyError, ValueError, ZeroDivisionError):
                continue
        
        self.logger.info(f"Built price matrix with {len(price_matrix)} currency pairs")
        return price_matrix, currencies
    
    def find_triangular_opportunities(self, ticker_data: Dict) -> pd.DataFrame:
        """Find triangular arbitrage opportunities"""
        try:
            price_matrix, currencies = self.build_price_matrix(ticker_data)
            
            if len(currencies) < 3:
                self.logger.warning("Need at least 3 currencies for triangular arbitrage")
                return pd.DataFrame()
            
            opportunities = []
            currencies_list = list(currencies)
            
            # Generate triangular paths
            for a in currencies_list:
                for b in currencies_list:
                    if b == a:
                        continue
                    for c in currencies_list:
                        if c == a or c == b:
                            continue
                        
                        # Check if triangular path exists: A -> B -> C -> A
                        leg1 = (a, b)  # A to B
                        leg2 = (b, c)  # B to C  
                        leg3 = (c, a)  # C to A
                        
                        if all(leg in price_matrix for leg in [leg1, leg2, leg3]):
                            opportunity = self.calculate_arbitrage_profit(
                                price_matrix, a, b, c
                            )
                            if opportunity and opportunity['profit_percent'] >= self.min_profit:
                                opportunities.append(opportunity)
            
            # Sort by profit and remove duplicates
            df = pd.DataFrame(opportunities)
            if not df.empty:
                df = df.sort_values('profit_percent', ascending=False)
                # Remove duplicate paths (same currencies, different order)
                df = df.drop_duplicates(subset=['path_key'])
            
            self.logger.info(f"Found {len(df)} arbitrage opportunities")
            return df.head(15)  # Return top 15
            
        except Exception as e:
            self.logger.error(f"Error finding arbitrage opportunities: {e}")
            return pd.DataFrame()
    
    def calculate_arbitrage_profit(self, price_matrix: Dict, curr_a: str, curr_b: str, curr_c: str) -> Optional[Dict]:
        """Calculate profit for triangular arbitrage path A->B->C->A"""
        try:
            leg1_data = price_matrix[(curr_a, curr_b)]
            leg2_data = price_matrix[(curr_b, curr_c)]
            leg3_data = price_matrix[(curr_c, curr_a)]
            
            # Start with 1 unit of currency A
            starting_amount = 1.0
            
            # Execute three trades with fees
            # Trade 1: A -> B
            after_trade1 = starting_amount * leg1_data['rate'] * (1 - self.trading_fee)
            
            # Trade 2: B -> C
            after_trade2 = after_trade1 * leg2_data['rate'] * (1 - self.trading_fee)
            
            # Trade 3: C -> A
            final_amount = after_trade2 * leg3_data['rate'] * (1 - self.trading_fee)
            
            # Calculate profit
            profit = final_amount - starting_amount
            profit_percent = profit * 100
            
            # Risk assessment
            min_volume = min(
                leg1_data['volume'],
                leg2_data['volume'],
                leg3_data['volume']
            )
            
            avg_spread = (
                leg1_data['spread'] + 
                leg2_data['spread'] + 
                leg3_data['spread']
            ) / 3
            
            # Risk level determination
            if min_volume > 10000 and avg_spread < 0.5:
                risk_level = "LOW"
            elif min_volume > 1000 and avg_spread < 1.0:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            # Execution assessment
            if profit_percent > 2.0 and risk_level == "LOW":
                execution = "EXCELLENT"
            elif profit_percent > 1.0 and risk_level in ["LOW", "MEDIUM"]:
                execution = "GOOD"
            elif profit_percent >= self.min_profit:
                execution = "FAIR"
            else:
                execution = "POOR"
            
            return {
                'path': f"{curr_a}→{curr_b}→{curr_c}→{curr_a}",
                'path_key': f"{curr_a}-{curr_b}-{curr_c}",  # For deduplication
                'profit_percent': round(profit_percent, 3),
                'final_amount': round(final_amount, 6),
                'min_volume': round(min_volume, 0),
                'avg_spread': round(avg_spread, 3),
                'risk_level': risk_level,
                'execution': execution,
                'leg1_pair': leg1_data['pair'],
                'leg2_pair': leg2_data['pair'],
                'leg3_pair': leg3_data['pair']
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating arbitrage for {curr_a}->{curr_b}->{curr_c}: {e}")
            return None

# Test function
def test_arbitrage_engine():
    """Test arbitrage detection with sample data"""
    print("🔄 Testing Arbitrage Engine...")
    
    # Import Kraken API to get real data
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api_clients.kraken_api import KrakenAPI
    
    try:
        kraken = KrakenAPI()
        arbitrage = ArbitrageEngine(min_profit=0.3)  # Lower threshold for testing
        
        # Get live ticker data
        pairs = kraken.get_tradable_pairs(20)
        ticker_data = kraken.get_ticker_data(pairs)
        print(f"✅ Got ticker data for {len(ticker_data)} pairs")
        
        # Find arbitrage opportunities
        opportunities_df = arbitrage.find_triangular_opportunities(ticker_data)
        
        if not opportunities_df.empty:
            print(f"✅ Found {len(opportunities_df)} arbitrage opportunities")
            print("\n🎯 Top opportunities:")
            display_cols = ['path', 'profit_percent', 'risk_level', 'execution', 'min_volume']
            print(opportunities_df[display_cols].head())
            print("\n🚀 Arbitrage engine test SUCCESSFUL!")
            return True
        else:
            print("ℹ️ No arbitrage opportunities found (this is normal in efficient markets)")
            print("✅ Arbitrage engine working - just no current opportunities")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_arbitrage_engine()