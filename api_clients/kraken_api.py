import requests
import time
import pandas as pd
from typing import Dict, List
import logging

class KrakenAPI:
    """Kraken API client for live market data"""
    
    def __init__(self):
        self.base_url = "https://api.kraken.com/0/public"
        self.session = requests.Session()
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make rate-limited request to Kraken"""
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('error'):
                logging.error(f"Kraken API error: {data['error']}")
                return {}
            
            return data.get('result', {})
            
        except Exception as e:
            logging.error(f"Kraken API request failed: {e}")
            return {}
    
    def get_tradable_pairs(self, limit: int = 25) -> List[str]:
        """Get major tradable pairs"""
        try:
            data = self._make_request("AssetPairs")
            if not data:
                return []
            
            pairs = []
            for pair_name, pair_info in data.items():
                if pair_info.get('status') == 'online' and pair_info.get('wsname'):
                    pairs.append(pair_name)
            
            return pairs[:limit]
            
        except Exception as e:
            logging.error(f"Error fetching pairs: {e}")
            return []
    
    def get_ticker_data(self, pairs: List[str]) -> Dict:
        """Get ticker data for multiple pairs"""
        try:
            if not pairs:
                return {}
            
            pairs_str = ','.join(pairs)
            data = self._make_request("Ticker", {"pair": pairs_str})
            return data if data else {}
            
        except Exception as e:
            logging.error(f"Error fetching ticker data: {e}")
            return {}
    
    def calculate_metrics(self, ticker_data: Dict) -> pd.DataFrame:
        """Calculate trading metrics"""
        metrics = []
        
        for pair, data in ticker_data.items():
            try:
                ask = float(data['a'][0])
                bid = float(data['b'][0])
                last = float(data['c'][0])
                volume = float(data['v'][1])
                high = float(data['h'][1])
                low = float(data['l'][1])
                trades = int(data['t'][1])
                
                # Calculate metrics
                mean_price = (high + low) / 2
                volatility = (high - low) / mean_price * 100 if mean_price > 0 else 0
                spread = (ask - bid) / ((ask + bid) / 2) * 100 if (ask + bid) > 0 else 0
                
                # Risk/reward score
                vol_score = min(volatility * 5, 40)
                volume_score = min(volume / 1000 * 20, 30)
                spread_score = max(0, 30 - spread * 20)
                total_score = vol_score + volume_score + spread_score
                
                # Strategy
                if total_score < 25:
                    strategy = "AVOID"
                elif volatility > 8 and spread < 0.3:
                    strategy = "SCALPING"
                elif 3 < volatility < 12:
                    strategy = "GRID"
                elif volatility > 12:
                    strategy = "BREAKOUT"
                else:
                    strategy = "MONITOR"
                
                metrics.append({
                    "Pair": pair,
                    "Price": f"${last:.4f}",
                    "Volatility_%": round(volatility, 2),
                    "Spread_%": round(spread, 4),
                    "Volume_24h": f"{volume:,.0f}",
                    "Score": round(total_score, 1),
                    "Strategy": strategy
                })
                
            except (KeyError, ValueError, ZeroDivisionError):
                continue
        
        df = pd.DataFrame(metrics)
        return df.sort_values('Score', ascending=False) if not df.empty else df
    
    def get_live_metrics(self):
        """Get complete live metrics"""
        pairs = self.get_tradable_pairs()
        ticker_data = self.get_ticker_data(pairs)
        metrics_df = self.calculate_metrics(ticker_data)
        return metrics_df, ticker_data

# Test function
def test_kraken_api():
    print("🚀 Testing Kraken API...")
    
    kraken = KrakenAPI()
    
    try:
        pairs = kraken.get_tradable_pairs(5)
        print(f"✅ Found {len(pairs)} pairs: {pairs}")
        
        if pairs:
            ticker_data = kraken.get_ticker_data(pairs)
            print(f"✅ Got ticker data for {len(ticker_data)} pairs")
            
            metrics_df = kraken.calculate_metrics(ticker_data)
            print(f"✅ Calculated metrics for {len(metrics_df)} pairs")
            
            if not metrics_df.empty:
                print("\n📊 Sample metrics:")
                print(metrics_df[['Pair', 'Price', 'Volatility_%', 'Score', 'Strategy']].head())
                print("\n🎯 Kraken API test SUCCESSFUL!")
                return True
            else:
                print("❌ No metrics calculated")
                return False
        else:
            print("❌ No pairs retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_kraken_api()