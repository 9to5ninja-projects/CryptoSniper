#!/usr/bin/env python3
"""
Solana Signal Generator with ML Enhancement
Combines rule-based signals with ML predictions
"""

import os
import sys
import logging
from typing import Dict, List, Optional
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ml.signal_ml import MLSignalGenerator

class SolanaSignalGenerator:
    """
    Enhanced Solana signal generator with ML capabilities
    """
    
    def __init__(self, enable_ml: bool = True):
        """
        Initialize signal generator
        
        Args:
            enable_ml: Whether to enable ML enhancement
        """
        self.logger = logging.getLogger(__name__)
        self.enable_ml = enable_ml
        self.ml_generator = None
        
        # Initialize ML generator if enabled
        if self.enable_ml:
            try:
                self.ml_generator = MLSignalGenerator()
                # Try to load existing model
                if not self.ml_generator.load_model():
                    self.logger.info("No existing ML model found - will train on first use")
            except Exception as e:
                self.logger.warning(f"ML initialization failed: {e}")
                self.enable_ml = False
        
        self.logger.info(f"SolanaSignalGenerator initialized (ML: {'enabled' if self.enable_ml else 'disabled'})")
    
    def generate_rule_based_signal(self, token_data: Dict) -> Dict:
        """
        Generate rule-based signal (existing logic)
        
        Args:
            token_data: Token market data
            
        Returns:
            Rule-based signal with confidence
        """
        try:
            # Extract key metrics
            price_change_24h = float(token_data.get('price_change_percentage_24h', 0))
            price_change_1h = float(token_data.get('price_change_percentage_1h', 0))
            volume_24h = float(token_data.get('total_volume', 0))
            market_cap = float(token_data.get('market_cap', 1))
            current_price = float(token_data.get('current_price', 0))
            
            # Calculate volume to market cap ratio
            volume_mcap_ratio = (volume_24h / market_cap * 100) if market_cap > 0 else 0
            
            # Calculate momentum score (existing logic from coingecko_api.py)
            momentum_score = 0
            
            # Price momentum (40% weight)
            if price_change_24h > 20:
                momentum_score += 40
            elif price_change_24h > 10:
                momentum_score += 30
            elif price_change_24h > 5:
                momentum_score += 20
            elif price_change_24h > 0:
                momentum_score += 10
            
            # Volume analysis (30% weight)
            if volume_mcap_ratio > 200:
                momentum_score += 30
            elif volume_mcap_ratio > 100:
                momentum_score += 25
            elif volume_mcap_ratio > 50:
                momentum_score += 15
            elif volume_mcap_ratio > 20:
                momentum_score += 10
            
            # Short-term momentum (20% weight)
            if price_change_1h > 5:
                momentum_score += 20
            elif price_change_1h > 2:
                momentum_score += 15
            elif price_change_1h > 0:
                momentum_score += 10
            
            # Market cap consideration (10% weight)
            if market_cap > 100000000:  # $100M+
                momentum_score += 10
            elif market_cap > 50000000:  # $50M+
                momentum_score += 8
            elif market_cap > 10000000:  # $10M+
                momentum_score += 5
            
            # Generate signal based on momentum score
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
            
            # Create signal object
            rule_signal = {
                'symbol': token_data.get('symbol', '').upper(),
                'name': token_data.get('name', ''),
                'signal': signal,
                'confidence_score': confidence,
                'momentum_score': momentum_score,
                'current_price': current_price,
                'price_change_1h': price_change_1h,
                'price_change_24h': price_change_24h,
                'volume_24h': volume_24h,
                'market_cap': market_cap,
                'volume_mcap_ratio': volume_mcap_ratio,
                'signal_type': 'rule_based'
            }
            
            return rule_signal
            
        except Exception as e:
            self.logger.error(f"Error in rule-based signal generation: {e}")
            return {
                'symbol': token_data.get('symbol', '').upper(),
                'name': token_data.get('name', ''),
                'signal': 'HOLD',
                'confidence_score': 30,
                'signal_type': 'rule_based',
                'error': str(e)
            }
    
    def enhance_signal_with_ml(self, rule_signal: Dict, token_data: Dict) -> Dict:
        """
        Enhance rule-based signal with ML predictions
        
        Args:
            rule_signal: Rule-based signal
            token_data: Original token data
            
        Returns:
            ML-enhanced signal
        """
        try:
            if not self.enable_ml or not self.ml_generator or not self.ml_generator.is_trained:
                # Return rule-based signal if ML not available
                rule_signal['signal_type'] = 'rule_based_only'
                return rule_signal
            
            # Get ML prediction
            ml_result = self.ml_generator.generate_ml_signal(token_data)
            
            if 'error' in ml_result:
                # ML failed, return rule-based signal
                rule_signal['signal_type'] = 'rule_based_only'
                rule_signal['ml_error'] = ml_result['error']
                return rule_signal
            
            # Extract ML results
            ml_signal = ml_result['ml_signal']
            ml_confidence = ml_result['ml_confidence']
            
            # Combine signals using weighted approach
            rule_signal_type = rule_signal['signal']
            rule_confidence = rule_signal['confidence_score']
            
            # Signal combination logic
            if rule_signal_type == ml_signal:
                # Signals agree - boost confidence
                combined_confidence = min(100, rule_confidence + (ml_confidence * 15))
                final_signal = rule_signal_type
                agreement = True
            elif ml_confidence > 0.8:
                # High ML confidence - use ML signal but reduce confidence
                combined_confidence = ml_confidence * 75
                final_signal = ml_signal
                agreement = False
            else:
                # Signals disagree with low ML confidence - use rule-based but reduce confidence
                combined_confidence = max(25, rule_confidence * 0.8)
                final_signal = rule_signal_type
                agreement = False
            
            # Create enhanced signal
            enhanced_signal = rule_signal.copy()
            enhanced_signal.update({
                'signal': final_signal,
                'confidence_score': int(combined_confidence),
                'signal_type': 'ml_enhanced',
                'ml_enhancement': {
                    'ml_signal': ml_signal,
                    'ml_confidence': ml_confidence,
                    'rule_signal': rule_signal_type,
                    'rule_confidence': rule_confidence,
                    'signals_agree': agreement,
                    'enhancement_applied': True
                }
            })
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"Error enhancing signal with ML: {e}")
            # Return original rule-based signal on error
            rule_signal['signal_type'] = 'rule_based_only'
            rule_signal['ml_error'] = str(e)
            return rule_signal
    
    def generate_signal(self, token_data: Dict) -> Dict:
        """
        Generate complete signal (rule-based + ML enhancement)
        
        Args:
            token_data: Token market data
            
        Returns:
            Enhanced signal
        """
        # Generate rule-based signal
        rule_signal = self.generate_rule_based_signal(token_data)
        
        # Enhance with ML if enabled
        if self.enable_ml:
            enhanced_signal = self.enhance_signal_with_ml(rule_signal, token_data)
            return enhanced_signal
        else:
            rule_signal['signal_type'] = 'rule_based_only'
            return rule_signal
    
    def generate_signals_batch(self, tokens_data: List[Dict]) -> List[Dict]:
        """
        Generate signals for multiple tokens
        
        Args:
            tokens_data: List of token market data
            
        Returns:
            List of enhanced signals
        """
        signals = []
        
        for token_data in tokens_data:
            try:
                signal = self.generate_signal(token_data)
                signals.append(signal)
            except Exception as e:
                self.logger.error(f"Error generating signal for {token_data.get('symbol', 'unknown')}: {e}")
                continue
        
        return signals
    
    def train_ml_model(self, historical_data: List[Dict]) -> Dict:
        """
        Train the ML model with historical data
        
        Args:
            historical_data: Historical signal data
            
        Returns:
            Training results
        """
        if not self.enable_ml or not self.ml_generator:
            return {'error': 'ML not enabled'}
        
        try:
            results = self.ml_generator.train_model(historical_data)
            if 'error' not in results:
                self.logger.info(f"ML model trained successfully. Accuracy: {results.get('test_accuracy', 0):.3f}")
            return results
        except Exception as e:
            self.logger.error(f"Error training ML model: {e}")
            return {'error': str(e)}
    
    def get_ml_status(self) -> Dict:
        """Get ML model status"""
        if not self.enable_ml or not self.ml_generator:
            return {'ml_enabled': False}
        
        return {
            'ml_enabled': True,
            'is_trained': self.ml_generator.is_trained,
            'feature_count': len(self.ml_generator.feature_names),
            'feature_names': self.ml_generator.feature_names.copy()
        }