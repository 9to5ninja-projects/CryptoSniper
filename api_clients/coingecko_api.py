import requests
import time
import pandas as pd
from typing import Dict, List, Optional
import logging
import os
import sys

# Add project root to path for ML integration
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from solana.signal_generator import SolanaSignalGenerator
    from trading.signal_processor import SignalProcessor
    ML_AVAILABLE = True
    TRADING_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    TRADING_AVAILABLE = False

class CoinGeckoAPI:
    """CoinGecko API client for Solana ecosystem tokens"""
    
    def __init__(self, api_key: Optional[str] = None, enable_ml: bool = True):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = api_key
        self.session = requests.Session()
        self.rate_limit_delay = 1.2  # Free tier: 50 calls/minute
        self.last_request_time = 0
        
        headers = {"accept": "application/json"}
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        self.session.headers.update(headers)
        
        # Initialize ML-enhanced signal generator
        self.signal_generator = None
        if ML_AVAILABLE and enable_ml:
            try:
                self.signal_generator = SolanaSignalGenerator(enable_ml=True)
                logging.info("ML-enhanced signal generation enabled")
            except Exception as e:
                logging.warning(f"ML signal generator initialization failed: {e}")
        
        # Initialize signal processor for auto-trading
        self.signal_processor = None
        if TRADING_AVAILABLE:
            try:
                self.signal_processor = SignalProcessor()
                logging.info("Signal processor for auto-trading initialized")
            except Exception as e:
                logging.warning(f"Signal processor initialization failed: {e}")
        else:
            logging.info("Using rule-based signal generation only")
    
    def process_signal_for_trading(self, signal_data):
        """Call this after every signal is generated"""
        if not self.signal_processor:
            return {'action': 'no_processor', 'reason': 'signal_processor_not_available'}
        
        try:
            trade_result = self.signal_processor.process_new_signal(signal_data)
            
            # Log trade results for monitoring
            if trade_result.get('action') in ['buy_executed', 'sell_executed']:
                logging.info(f"🤖 Auto-trade executed: {trade_result}")
            
            return trade_result
        except Exception as e:
            logging.error(f"Error processing signal for trading: {e}")
            return {'action': 'error', 'reason': str(e)}
    
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
        """Analyze tokens for sniper opportunities with ML enhancement"""
        analyzed_tokens = []
        
        # Use ML-enhanced signal generator if available
        if self.signal_generator:
            try:
                # Generate ML-enhanced signals for all tokens
                enhanced_signals = self.signal_generator.generate_signals_batch(tokens)
                
                for signal in enhanced_signals:
                    try:
                        # Find original token data
                        original_token = next((t for t in tokens if t.get('symbol', '').upper() == signal.get('symbol', '')), {})
                        
                        # CRITICAL: Process signal for trading immediately after generation
                        from datetime import datetime
                        trading_signal_data = {
                            'symbol': signal.get('symbol', '').upper(),
                            'signal': signal.get('signal', 'HOLD'),
                            'confidence_score': signal.get('confidence_score', 50),
                            'current_price': signal.get('current_price', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Process signal for auto-trading
                        trade_result = self.process_signal_for_trading(trading_signal_data)
                        
                        # Create analysis combining original data with enhanced signal
                        token_analysis = original_token.copy()
                        token_analysis.update({
                            'momentum_score': signal.get('momentum_score', 0),
                            'signal': signal.get('signal', 'HOLD'),
                            'confidence_score': signal.get('confidence_score', 50),
                            'volume_mcap_ratio': signal.get('volume_mcap_ratio', 0),
                            'signal_type': signal.get('signal_type', 'rule_based'),
                            'risk_level': self._assess_risk_level(signal.get('market_cap', 0)),
                            'trade_result': trade_result  # Add trade result to analysis
                        })
                        
                        # Add ML enhancement info if available
                        if 'ml_enhancement' in signal:
                            token_analysis['ml_enhancement'] = signal['ml_enhancement']
                        
                        analyzed_tokens.append(token_analysis)
                        
                    except Exception as e:
                        logging.error(f"Error processing enhanced signal for {signal.get('symbol', 'unknown')}: {e}")
                        continue
                        
            except Exception as e:
                logging.error(f"Error in ML-enhanced analysis: {e}")
                # Fall back to rule-based analysis
                return self._analyze_tokens_rule_based(tokens)
        else:
            # Use rule-based analysis
            return self._analyze_tokens_rule_based(tokens)
        
        df = pd.DataFrame(analyzed_tokens)
        return df.sort_values('confidence_score', ascending=False) if not df.empty else df
    
    def _analyze_tokens_rule_based(self, tokens: List[Dict]) -> pd.DataFrame:
        """Fallback rule-based analysis (original logic)"""
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
                
                # Signal generation
                if momentum_score >= 70:
                    signal = "STRONG BUY"
                    confidence = 85
                elif momentum_score >= 50:
                    signal = "BUY"
                    confidence = 70
                elif momentum_score >= 30:
                    signal = "WATCH"
                    confidence = 55
                else:
                    signal = "AVOID"
                    confidence = 40
                
                # CRITICAL: Process signal for trading immediately after generation
                from datetime import datetime
                trading_signal_data = {
                    'symbol': token.get('symbol', '').upper(),
                    'signal': signal,
                    'confidence_score': confidence,
                    'current_price': price,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Process signal for auto-trading
                trade_result = self.process_signal_for_trading(trading_signal_data)
                
                # Add analysis to token data
                token_analysis = token.copy()
                token_analysis.update({
                    'momentum_score': round(momentum_score, 1),
                    'risk_level': self._assess_risk_level(market_cap),
                    'signal': signal,
                    'confidence_score': confidence,
                    'volume_mcap_ratio': round(volume_to_mcap, 2),
                    'signal_type': 'rule_based',
                    'trade_result': trade_result  # Add trade result to analysis
                })
                
                analyzed_tokens.append(token_analysis)
                
            except Exception as e:
                logging.error(f"Error analyzing token {token.get('name', 'unknown')}: {e}")
                continue
        
        df = pd.DataFrame(analyzed_tokens)
        return df.sort_values('momentum_score', ascending=False) if not df.empty else df
    
    def _assess_risk_level(self, market_cap: float) -> str:
        """Assess risk level based on market cap"""
        if market_cap > 100000000:  # $100M+
            return "LOW"
        elif market_cap > 10000000:  # $10M+
            return "MEDIUM"
        else:
            return "HIGH"
    
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