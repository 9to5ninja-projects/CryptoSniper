import pandas as pd
import glob
import os
from datetime import date, timedelta
from ml.signal_ml import MLSignalGenerator

class ModelRetrainer:
    def __init__(self):
        self.export_dir = "data/learning_exports"
        self.ml_generator = MLSignalGenerator()
    
    def retrain_with_recent_data(self, days_back=7):
        """Retrain model with last N days of actual trading data"""
        
        # Load recent trading data
        training_data = self._load_recent_training_data(days_back)
        
        if len(training_data) < 10:
            return {'success': False, 'reason': 'insufficient_data', 'records': len(training_data)}
        
        # Retrain the model
        results = self._retrain_model(training_data)
        
        return results
    
    def _load_recent_training_data(self, days_back):
        """Load CSV files from recent days"""
        all_data = []
        
        for i in range(days_back):
            target_date = date.today() - timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            
            csv_file = f"{self.export_dir}/ml_training_data_{date_str}.csv"
            
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df.to_dict('records')
        else:
            return []
    
    def _retrain_model(self, training_data):
        """Retrain ML model with actual trading outcomes"""
        
        # Convert trading results to ML training format
        ml_training_data = []
        
        for record in training_data:
            # Only include records where trades were actually executed
            if record.get('was_traded') and record.get('trade_success'):
                
                # Determine if the trade was profitable
                pnl = record.get('pnl', 0)
                successful_trade = pnl > 0 if pnl is not None else False
                
                ml_record = {
                    'symbol': record['symbol'],
                    'signal': 'BUY' if successful_trade else 'AVOID',  # Relabel based on actual outcome
                    'confidence_score': record['confidence_score'],
                    'current_price': record['current_price'],
                    'actual_outcome': 'profitable' if successful_trade else 'unprofitable'
                }
                ml_training_data.append(ml_record)
        
        # Retrain the model
        if len(ml_training_data) >= 5:
            results = self.ml_generator.train_ml_model(ml_training_data)
            return {
                'success': True,
                'training_records': len(ml_training_data),
                'model_performance': results
            }
        else:
            return {
                'success': False, 
                'reason': 'insufficient_profitable_trades',
                'records': len(ml_training_data)
            }