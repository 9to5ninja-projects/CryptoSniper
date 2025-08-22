import requests
import time
import pandas as pd
from typing import Dict, List, Optional
import logging

class CoinGeckoAPI:
    """CoinGecko API client for Solana ecosystem tokens"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = api_key
        self.session = requests.Session()
        self.rate_limit_delay = 1.2  # Free tier: 50 calls/minute
        self.last_request_time = 0
        
        headers = {"accept": "application/json"}
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        self.session.headers.update(headers)
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make rate-limited request"""
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"CoinGecko API error for {endpoint}: {e}")
            return {}
    
    def get_solana_tokens(self, limit: int = 30) -> List[Dict]:
        """Get Solana ecosystem tokens with CoinGecko IDs"""
        try:
            data = self._make_request(
                "coins/markets",
                params={
                    'vs_currency': 'usd',
                    'category': 'solana-ecosystem',
                    'order': 'volume_desc',
                    'per_page': limit,
                    'page': 1,
                    'sparkline': False,
                    'price_change_percentage': '1h,24h'
                }
            )
            
            if data:
                formatted_tokens = []
                for token in data:
                    if not token.get('current_price') or not token.get('total_volume'):
                        continue
                    
                    formatted_tokens.append({
                        'id': token.get('id'),  # CoinGecko ID for charts
                        'name': token.get('name', 'Unknown'),
                        'symbol': token.get('symbol', '').upper(),
                        'current_price': token.get('current_price', 0),
                        'price_change_1h': token.get('price_change_percentage_1h', 0),
                        'price_change_24h': token.get('price_change_percentage_24h', 0),
                        'total_volume': token.get('total_volume', 0),
                        'market_cap': token.get('market_cap', 0),
                        'market_cap_rank': token.get('market_cap_rank', 999),
                        'image': token.get('image', ''),
                        'ath': token.get('ath', 0),
                        'atl': token.get('atl', 0)
                    })
                
                logging.info(f"Retrieved {len(formatted_tokens)} Solana tokens")
                return formatted_tokens
            
            return []
            
        except Exception as e:
            logging.error(f"Error fetching Solana tokens: {e}")
            return []
    
    def analyze_sniper_opportunities(self, tokens: List[Dict]) -> pd.DataFrame:
        """Analyze tokens for sniping potential"""
        analyzed_tokens = []
        
        for token in tokens:
            try:
                price = token.get('current_price', 0)
                volume_24h = token.get('total_volume', 0)
                market_cap = token.get('market_cap', 0)
                price_change_1h = token.get('price_change_1h', 0)
                price_change_24h = token.get('price_change_24h', 0)
                
                # Calculate volume to market cap ratio
                volume_to_mcap = (volume_24h / market_cap * 100) if market_cap > 0 else 0
                
                # Momentum scoring (0-100)
                momentum_score = 0
                
                # 1-hour momentum (max 30 points)
                if price_change_1h > 10:
                    momentum_score += 30
                elif price_change_1h > 5:
                    momentum_score += 20
                elif price_change_1h > 0:
                    momentum_score += 10
                
                # 24-hour momentum (max 40 points)
                if price_change_24h > 50:
                    momentum_score += 40
                elif price_change_24h > 20:
                    momentum_score += 30
                elif price_change_24h > 10:
                    momentum_score += 20
                elif price_change_24h > 0:
                    momentum_score += 10
                
                # Volume activity (max 30 points)
                if volume_to_mcap > 100:
                    momentum_score += 30
                elif volume_to_mcap > 50:
                    momentum_score += 20
                elif volume_to_mcap > 20:
                    momentum_score += 10
                
                # Risk assessment
                if market_cap > 100000000:  # $100M+
                    risk_level = "LOW"
                elif market_cap > 10000000:  # $10M+
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"
                
                # Signal generation
                if momentum_score >= 70:
                    signal = "STRONG BUY"
                elif momentum_score >= 50:
                    signal = "BUY"
                elif momentum_score >= 30:
                    signal = "WATCH"
                else:
                    signal = "AVOID"
                
                # Add analysis to token data
                token_analysis = token.copy()
                token_analysis.update({
                    'momentum_score': round(momentum_score, 1),
                    'risk_level': risk_level,
                    'signal': signal,
                    'volume_mcap_ratio': round(volume_to_mcap, 2)
                })
                
                analyzed_tokens.append(token_analysis)
                
            except Exception as e:
                logging.error(f"Error analyzing token {token.get('name', 'unknown')}: {e}")
                continue
        
        df = pd.DataFrame(analyzed_tokens)
        return df.sort_values('momentum_score', ascending=False) if not df.empty else df
    
    def get_analyzed_solana_tokens(self, limit: int = 25) -> pd.DataFrame:
        """Get Solana tokens with sniper analysis"""
        tokens = self.get_solana_tokens(limit)
        if tokens:
            return self.analyze_sniper_opportunities(tokens)
        return pd.DataFrame()

# Test function
def test_coingecko_api():
    print("🎯 Testing CoinGecko API...")
    
    coingecko = CoinGeckoAPI()
    
    try:
        # Test getting Solana tokens
        tokens = coingecko.get_solana_tokens(10)
        print(f"✅ Found {len(tokens)} Solana tokens")
        
        if tokens:
            # Test analysis
            analyzed_df = coingecko.analyze_sniper_opportunities(tokens)
            print(f"✅ Analyzed {len(analyzed_df)} tokens for sniping potential")
            
            if not analyzed_df.empty:
                print("\n🎯 Top Solana opportunities:")
                display_cols = ['name', 'symbol', 'current_price', 'price_change_24h', 'momentum_score', 'signal', 'risk_level']
                print(analyzed_df[display_cols].head())
                
                strong_buys = len(analyzed_df[analyzed_df['signal'] == 'STRONG BUY'])
                print(f"\n🚀 Found {strong_buys} STRONG BUY signals!")
                print("\n✅ CoinGecko API test SUCCESSFUL!")
                return True
            else:
                print("❌ No analysis data generated")
                return False
        else:
            print("❌ No Solana tokens retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_coingecko_api()