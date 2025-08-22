#!/usr/bin/env python3
"""
ML Signal Enhancement
Basic machine learning capabilities for crypto signal generation using scikit-learn
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import logging
import joblib
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class MLSignalGenerator:
    """
    Machine Learning Signal Generator using Random Forest
    Enhances existing rule-based signals with ML predictions
    """
    
    def __init__(self):
        """Initialize ML Signal Generator"""
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.feature_names = []
        self.logger = logging.getLogger(__name__)
        
        # Model persistence paths
        self.model_dir = os.path.dirname(__file__)
        self.model_path = os.path.join(self.model_dir, 'trained_model.joblib')
        self.scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        self.encoder_path = os.path.join(self.model_dir, 'encoder.joblib')
        
        self.logger.info("MLSignalGenerator initialized")
    
    def prepare_features(self, price_data: Dict) -> np.ndarray:
        """
        Convert price data to ML features
        
        Args:
            price_data: Dictionary containing price and volume data
            
        Returns:
            Feature matrix as numpy array
        """
        try:
            features = {}
            
            # Extract basic data with defaults
            current_price = float(price_data.get('current_price', 0))
            price_change_1h = float(price_data.get('price_change_1h', 0))
            price_change_24h = float(price_data.get('price_change_24h', 0))
            volume_24h = float(price_data.get('volume_24h', 0))
            market_cap = float(price_data.get('market_cap', 1))
            
            # Price momentum features (5, 15, 30 minute approximations)
            features['momentum_5min'] = price_change_1h / 12  # Approximate 5min from 1h
            features['momentum_15min'] = price_change_1h / 4   # Approximate 15min from 1h
            features['momentum_30min'] = price_change_1h / 2   # Approximate 30min from 1h
            features['momentum_1h'] = price_change_1h
            features['momentum_24h'] = price_change_24h
            
            # Volume ratios
            volume_mcap_ratio = (volume_24h / market_cap * 100) if market_cap > 0 else 0
            features['volume_mcap_ratio'] = volume_mcap_ratio
            features['volume_24h_log'] = np.log1p(volume_24h)
            features['market_cap_log'] = np.log1p(market_cap)
            
            # Simple technical indicators
            # RSI proxy based on price changes
            features['rsi_proxy'] = self._calculate_rsi_proxy(price_change_24h)
            
            # Moving average proxies
            features['ma_signal_short'] = 1 if price_change_1h > 0 else -1
            features['ma_signal_long'] = 1 if price_change_24h > 0 else -1
            features['ma_crossover'] = features['ma_signal_short'] - features['ma_signal_long']
            
            # Volatility measures
            features['volatility_1h'] = abs(price_change_1h)
            features['volatility_24h'] = abs(price_change_24h)
            features['volatility_ratio'] = features['volatility_1h'] / max(features['volatility_24h'], 0.1)
            
            # Price level features
            features['price_level'] = np.log1p(current_price)
            features['price_momentum_strength'] = abs(price_change_24h)
            
            # Market condition indicators
            features['bullish_momentum'] = 1 if (price_change_1h > 0 and price_change_24h > 5) else 0
            features['bearish_momentum'] = 1 if (price_change_1h < 0 and price_change_24h < -5) else 0
            features['high_volume'] = 1 if volume_mcap_ratio > 100 else 0
            
            # Store feature names for consistency
            if not self.feature_names:
                self.feature_names = list(features.keys())
            
            # Convert to array in consistent order
            feature_array = np.array([features.get(name, 0) for name in self.feature_names])
            
            return feature_array.reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            # Return zero features as fallback
            if self.feature_names:
                return np.zeros((1, len(self.feature_names)))
            else:
                return np.zeros((1, 20))  # Default feature count
    
    def _calculate_rsi_proxy(self, price_change_24h: float) -> float:
        """Calculate RSI proxy from 24h price change"""
        if price_change_24h > 15:
            return 80  # Overbought
        elif price_change_24h > 10:
            return 70
        elif price_change_24h > 5:
            return 60
        elif price_change_24h > 0:
            return 55
        elif price_change_24h > -5:
            return 45
        elif price_change_24h > -10:
            return 30
        else:
            return 20  # Oversold
    
    def train_model(self, historical_data: List[Dict]) -> Dict:
        """
        Train the Random Forest model
        
        Args:
            historical_data: List of historical price/signal data
            
        Returns:
            Training results and metrics
        """
        try:
            if len(historical_data) < 10:
                raise ValueError("Need at least 10 historical data points for training")
            
            self.logger.info(f"Training model on {len(historical_data)} data points")
            
            # Prepare features and labels
            X_list = []
            y_list = []
            
            for data_point in historical_data:
                try:
                    # Extract features
                    features = self.prepare_features(data_point)
                    X_list.append(features.flatten())
                    
                    # Extract label (signal)
                    signal = data_point.get('signal', 'HOLD')
                    y_list.append(signal)
                    
                except Exception as e:
                    self.logger.warning(f"Skipping data point due to error: {e}")
                    continue
            
            if len(X_list) < 5:
                raise ValueError("Not enough valid data points after preprocessing")
            
            # Convert to arrays
            X = np.array(X_list)
            y = np.array(y_list)
            
            # Encode labels
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_encoded, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            results = {
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'feature_count': len(self.feature_names),
                'signal_classes': list(self.label_encoder.classes_)
            }
            
            self.logger.info(f"Model training completed. Test accuracy: {test_score:.3f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return {'error': str(e)}
    
    def generate_ml_signal(self, current_data: Dict) -> Dict:
        """
        Generate ML-enhanced signal
        
        Args:
            current_data: Current price/volume data
            
        Returns:
            Signal with ML confidence and features
        """
        try:
            if not self.is_trained:
                return {
                    'ml_signal': 'HOLD',
                    'ml_confidence': 0.0,
                    'error': 'Model not trained'
                }
            
            # Prepare features
            features = self.prepare_features(current_data)
            features_scaled = self.scaler.transform(features)
            
            # Get prediction and probabilities
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Convert prediction back to signal
            ml_signal = self.label_encoder.inverse_transform([prediction])[0]
            
            # Calculate confidence (max probability)
            ml_confidence = float(np.max(probabilities))
            
            result = {
                'ml_signal': ml_signal,
                'ml_confidence': ml_confidence,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating ML signal: {e}")
            return {
                'ml_signal': 'HOLD',
                'ml_confidence': 0.0,
                'error': str(e)
            }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance rankings
        
        Returns:
            Dictionary of feature names and their importance scores
        """
        try:
            if not self.is_trained:
                return {}
            
            importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))
            
            # Sort by importance
            sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
            return sorted_importance
            
        except Exception as e:
            self.logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def _save_model(self):
        """Save trained model and preprocessors"""
        try:
            if self.model and self.is_trained:
                joblib.dump(self.model, self.model_path)
                joblib.dump(self.scaler, self.scaler_path)
                joblib.dump(self.label_encoder, self.encoder_path)
                
                # Save feature names
                feature_path = os.path.join(self.model_dir, 'feature_names.joblib')
                joblib.dump(self.feature_names, feature_path)
                
                self.logger.info("Model saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load trained model and preprocessors"""
        try:
            if (os.path.exists(self.model_path) and 
                os.path.exists(self.scaler_path) and 
                os.path.exists(self.encoder_path)):
                
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.label_encoder = joblib.load(self.encoder_path)
                
                # Load feature names
                feature_path = os.path.join(self.model_dir, 'feature_names.joblib')
                if os.path.exists(feature_path):
                    self.feature_names = joblib.load(feature_path)
                
                self.is_trained = True
                self.logger.info("Model loaded successfully")
                return True
                
        except Exception as e:
            self.logger.warning(f"Could not load existing model: {e}")
            return False