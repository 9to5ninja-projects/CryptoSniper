import json
import pandas as pd
from datetime import datetime, date
import os

class DailyExporter:
    def __init__(self):
        self.export_dir = "data/learning_exports"
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_daily_performance(self, signal_processor):
        """Export all trading data from today for tomorrow's training"""
        
        today = date.today().strftime("%Y-%m-%d")
        
        # Get all performance data
        performance_data = signal_processor.get_daily_performance_data()
        
        # Create comprehensive dataset for ML training
        training_data = self._prepare_training_data(performance_data)
        
        # Export in multiple formats
        exports = {}
        
        # 1. JSON export (complete data)
        json_file = f"{self.export_dir}/trading_data_{today}.json"
        with open(json_file, 'w') as f:
            json.dump(performance_data, f, indent=2)
        exports['json'] = json_file
        
        # 2. CSV export (ML training ready)
        csv_file = f"{self.export_dir}/ml_training_data_{today}.csv"
        training_df = pd.DataFrame(training_data)
        training_df.to_csv(csv_file, index=False)
        exports['csv'] = csv_file
        
        # 3. Performance summary
        summary_file = f"{self.export_dir}/performance_summary_{today}.json"
        summary = self._create_performance_summary(performance_data)
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        exports['summary'] = summary_file
        
        return exports
    
    def _prepare_training_data(self, performance_data):
        """Convert trading results into ML training format"""
        training_records = []
        
        for signal_record in performance_data['processed_signals']:
            signal = signal_record['signal']
            decision = signal_record['decision']
            trade_result = signal_record['trade_result']
            
            # Create training record
            record = {
                'symbol': signal.get('symbol'),
                'signal_type': signal.get('signal'),
                'confidence_score': signal.get('confidence_score'),
                'current_price': signal.get('current_price'),
                'was_traded': decision.get('should_trade', False),
                'trade_action': decision.get('action', 'none'),
                'trade_success': trade_result.get('success', False),
                'pnl': trade_result.get('pnl', 0) if 'pnl' in trade_result else None,
                'timestamp': signal_record['timestamp']
            }
            training_records.append(record)
        
        return training_records
    
    def _create_performance_summary(self, performance_data):
        """Create daily performance summary"""
        return {
            'date': date.today().isoformat(),
            'total_signals_processed': len(performance_data['processed_signals']),
            'total_trades_executed': performance_data['total_trades'],
            'winning_trades': performance_data['winning_trades'],
            'losing_trades': performance_data['losing_trades'],
            'win_rate': (performance_data['winning_trades'] / max(performance_data['total_trades'], 1)) * 100,
            'final_portfolio_value': performance_data['final_portfolio_value'],
            'daily_return': ((performance_data['final_portfolio_value'] - 10000) / 10000) * 100
        }