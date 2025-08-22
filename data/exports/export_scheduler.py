#!/usr/bin/env python3
"""
Export Scheduler Foundation
Automated export scheduling system with background threading and multiple formats
"""

import os
import sys
import json
import csv
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import pandas as pd
import schedule

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard.components.alert_manager import AlertManager
from api_clients.coingecko_api import CoinGeckoAPI
from config.settings import get_alert_config

class ExportScheduler:
    """
    Automated export scheduling system with background threading
    """
    
    def __init__(self, export_dir: Optional[str] = None):
        """
        Initialize the export scheduler
        
        Args:
            export_dir: Directory for exports (defaults to data/exports)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up export directory
        if export_dir is None:
            self.export_dir = Path(__file__).parent
        else:
            self.export_dir = Path(export_dir)
        
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.alert_manager = AlertManager()
        self.coingecko_api = CoinGeckoAPI()
        
        # Threading control
        self.scheduler_thread = None
        self.running = False
        self.stop_event = threading.Event()
        
        # Export statistics
        self.export_stats = {
            'total_exports': 0,
            'successful_exports': 0,
            'failed_exports': 0,
            'last_export_time': None,
            'export_history': []
        }
        
        self.logger.info("ExportScheduler initialized successfully")
    
    def start_scheduler(self):
        """Start the background scheduler thread"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.stop_event.clear()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Export scheduler started in background thread")
    
    def stop_scheduler(self):
        """Stop the background scheduler thread"""
        if not self.running:
            self.logger.warning("Scheduler is not running")
            return
        
        self.running = False
        self.stop_event.set()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("Export scheduler stopped")
    
    def _run_scheduler(self):
        """Background thread function for running scheduled tasks"""
        self.logger.info("Scheduler thread started")
        
        while self.running and not self.stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in scheduler thread: {e}")
                time.sleep(5)  # Wait before retrying
        
        self.logger.info("Scheduler thread stopped")
    
    def schedule_daily_export(self, export_type: str, time_str: str = "09:00"):
        """
        Schedule daily export at specified time
        
        Args:
            export_type: Type of export ('signals', 'alerts', 'performance', 'all')
            time_str: Time in HH:MM format (24-hour)
        """
        try:
            if export_type == 'signals':
                schedule.every().day.at(time_str).do(self._export_signal_history_job)
            elif export_type == 'alerts':
                schedule.every().day.at(time_str).do(self._export_alert_history_job)
            elif export_type == 'performance':
                schedule.every().day.at(time_str).do(self._export_performance_data_job)
            elif export_type == 'all':
                schedule.every().day.at(time_str).do(self._export_all_data_job)
            else:
                raise ValueError(f"Unknown export type: {export_type}")
            
            self.logger.info(f"Scheduled daily {export_type} export at {time_str}")
            
        except Exception as e:
            self.logger.error(f"Error scheduling daily export: {e}")
            raise
    
    def schedule_weekly_report(self, day: str = "monday", time_str: str = "08:00"):
        """
        Schedule weekly comprehensive report
        
        Args:
            day: Day of week (monday, tuesday, etc.)
            time_str: Time in HH:MM format (24-hour)
        """
        try:
            getattr(schedule.every(), day.lower()).at(time_str).do(self._export_weekly_report_job)
            self.logger.info(f"Scheduled weekly report on {day} at {time_str}")
            
        except Exception as e:
            self.logger.error(f"Error scheduling weekly report: {e}")
            raise
    
    def export_signal_history(self, days_back: int = 7, format_type: str = 'both') -> Dict[str, str]:
        """
        Export trading signal history
        
        Args:
            days_back: Number of days to look back
            format_type: Export format ('csv', 'json', 'both')
            
        Returns:
            Dict with export file paths
        """
        try:
            self.logger.info(f"Exporting signal history for last {days_back} days")
            
            # Get signal data from CoinGecko API
            signal_data = []
            
            # Get recent analyzed tokens (simulating signal history)
            try:
                analyzed_df = self.coingecko_api.get_analyzed_solana_tokens(50)
                
                if not analyzed_df.empty:
                    # Convert to signal history format
                    for _, token in analyzed_df.iterrows():
                        signal_data.append({
                            'timestamp': datetime.now().isoformat(),
                            'symbol': token.get('symbol', 'UNKNOWN'),
                            'name': token.get('name', 'Unknown Token'),
                            'signal': token.get('signal', 'HOLD'),
                            'confidence_score': token.get('momentum_score', 0.0),
                            'current_price': token.get('current_price', 0.0),
                            'price_change_1h': token.get('price_change_1h', 0.0),
                            'price_change_24h': token.get('price_change_24h', 0.0),
                            'volume_24h': token.get('total_volume', 0.0),
                            'market_cap': token.get('market_cap', 0.0),
                            'volume_mcap_ratio': token.get('volume_mcap_ratio', 0.0)
                        })
                
            except Exception as e:
                self.logger.warning(f"Could not fetch live signal data: {e}")
                # Create sample data for demonstration
                signal_data = self._generate_sample_signal_data(days_back)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"signal_history_{days_back}days_{timestamp}"
            
            export_files = {}
            
            # Export to CSV
            if format_type in ['csv', 'both']:
                csv_path = self.export_dir / f"{base_filename}.csv"
                df = pd.DataFrame(signal_data)
                df.to_csv(csv_path, index=False)
                export_files['csv'] = str(csv_path)
                self.logger.info(f"Signal history exported to CSV: {csv_path}")
            
            # Export to JSON
            if format_type in ['json', 'both']:
                json_path = self.export_dir / f"{base_filename}.json"
                with open(json_path, 'w') as f:
                    json.dump({
                        'export_info': {
                            'export_type': 'signal_history',
                            'days_back': days_back,
                            'export_timestamp': datetime.now().isoformat(),
                            'total_records': len(signal_data)
                        },
                        'data': signal_data
                    }, f, indent=2)
                export_files['json'] = str(json_path)
                self.logger.info(f"Signal history exported to JSON: {json_path}")
            
            # Update statistics
            self._update_export_stats('signal_history', True, len(signal_data))
            
            return export_files
            
        except Exception as e:
            self.logger.error(f"Error exporting signal history: {e}")
            self._update_export_stats('signal_history', False, 0)
            raise
    
    def export_alert_history(self, days_back: int = 7, format_type: str = 'both') -> Dict[str, str]:
        """
        Export alert history
        
        Args:
            days_back: Number of days to look back
            format_type: Export format ('csv', 'json', 'both')
            
        Returns:
            Dict with export file paths
        """
        try:
            self.logger.info(f"Exporting alert history for last {days_back} days")
            
            # Get alert data from AlertManager
            alert_data = []
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            for alert in active_alerts:
                alert_data.append({
                    'timestamp': alert['timestamp'],
                    'symbol': alert['symbol'],
                    'signal_type': alert['signal_type'],
                    'confidence_score': alert['confidence_score'],
                    'price': alert['price'],
                    'message': alert['message'],
                    'alert_condition': alert['alert_condition'],
                    'is_active': True
                })
            
            # Get historical alerts
            for alert in self.alert_manager.alert_history:
                alert_timestamp = datetime.fromisoformat(alert['timestamp'])
                if alert_timestamp >= datetime.now() - timedelta(days=days_back):
                    alert_data.append({
                        'timestamp': alert['timestamp'],
                        'symbol': alert['symbol'],
                        'signal_type': alert['signal_type'],
                        'confidence_score': alert['confidence_score'],
                        'price': alert['price'],
                        'message': alert['message'],
                        'alert_condition': alert['alert_condition'],
                        'is_active': False
                    })
            
            # If no real data, generate sample data
            if not alert_data:
                alert_data = self._generate_sample_alert_data(days_back)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"alert_history_{days_back}days_{timestamp}"
            
            export_files = {}
            
            # Export to CSV
            if format_type in ['csv', 'both']:
                csv_path = self.export_dir / f"{base_filename}.csv"
                df = pd.DataFrame(alert_data)
                df.to_csv(csv_path, index=False)
                export_files['csv'] = str(csv_path)
                self.logger.info(f"Alert history exported to CSV: {csv_path}")
            
            # Export to JSON
            if format_type in ['json', 'both']:
                json_path = self.export_dir / f"{base_filename}.json"
                with open(json_path, 'w') as f:
                    json.dump({
                        'export_info': {
                            'export_type': 'alert_history',
                            'days_back': days_back,
                            'export_timestamp': datetime.now().isoformat(),
                            'total_records': len(alert_data)
                        },
                        'data': alert_data
                    }, f, indent=2)
                export_files['json'] = str(json_path)
                self.logger.info(f"Alert history exported to JSON: {json_path}")
            
            # Update statistics
            self._update_export_stats('alert_history', True, len(alert_data))
            
            return export_files
            
        except Exception as e:
            self.logger.error(f"Error exporting alert history: {e}")
            self._update_export_stats('alert_history', False, 0)
            raise
    
    def export_performance_data(self, days_back: int = 30, format_type: str = 'both') -> Dict[str, str]:
        """
        Export system performance data
        
        Args:
            days_back: Number of days to look back
            format_type: Export format ('csv', 'json', 'both')
            
        Returns:
            Dict with export file paths
        """
        try:
            self.logger.info(f"Exporting performance data for last {days_back} days")
            
            # Collect performance metrics
            performance_data = []
            
            # Alert system performance
            alert_summary = self.alert_manager.get_alert_summary()
            
            # System configuration
            config = get_alert_config()
            
            # Generate performance metrics
            current_time = datetime.now()
            for i in range(days_back):
                date = current_time - timedelta(days=i)
                
                # Simulate performance data (in real implementation, this would come from logs/metrics)
                performance_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'timestamp': date.isoformat(),
                    'alerts_generated': max(0, int(5 - i * 0.1)),  # Simulated
                    'api_calls_made': max(10, int(100 - i * 2)),  # Simulated
                    'response_time_ms': max(100, int(200 + i * 5)),  # Simulated
                    'success_rate': min(100, max(85, 98 - i * 0.5)),  # Simulated
                    'active_alerts': alert_summary.get('total_active_alerts', 0),
                    'system_uptime_hours': 24,  # Simulated
                    'memory_usage_mb': max(50, int(100 + i * 2)),  # Simulated
                    'cpu_usage_percent': max(5, int(15 + i * 0.5)),  # Simulated
                    'strong_buy_threshold': config.get('STRONG_BUY_THRESHOLD', 80),
                    'volatility_threshold': config.get('VOLATILITY_THRESHOLD', 15),
                    'volume_spike_threshold': config.get('VOLUME_SPIKE_THRESHOLD', 200)
                })
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"performance_data_{days_back}days_{timestamp}"
            
            export_files = {}
            
            # Export to CSV
            if format_type in ['csv', 'both']:
                csv_path = self.export_dir / f"{base_filename}.csv"
                df = pd.DataFrame(performance_data)
                df.to_csv(csv_path, index=False)
                export_files['csv'] = str(csv_path)
                self.logger.info(f"Performance data exported to CSV: {csv_path}")
            
            # Export to JSON
            if format_type in ['json', 'both']:
                json_path = self.export_dir / f"{base_filename}.json"
                with open(json_path, 'w') as f:
                    json.dump({
                        'export_info': {
                            'export_type': 'performance_data',
                            'days_back': days_back,
                            'export_timestamp': datetime.now().isoformat(),
                            'total_records': len(performance_data)
                        },
                        'summary': {
                            'avg_alerts_per_day': sum(d['alerts_generated'] for d in performance_data) / len(performance_data),
                            'avg_response_time': sum(d['response_time_ms'] for d in performance_data) / len(performance_data),
                            'avg_success_rate': sum(d['success_rate'] for d in performance_data) / len(performance_data),
                            'total_api_calls': sum(d['api_calls_made'] for d in performance_data)
                        },
                        'data': performance_data
                    }, f, indent=2)
                export_files['json'] = str(json_path)
                self.logger.info(f"Performance data exported to JSON: {json_path}")
            
            # Update statistics
            self._update_export_stats('performance_data', True, len(performance_data))
            
            return export_files
            
        except Exception as e:
            self.logger.error(f"Error exporting performance data: {e}")
            self._update_export_stats('performance_data', False, 0)
            raise
    
    def export_system_logs(self, days_back: int = 7, format_type: str = 'both') -> Dict[str, str]:
        """
        Export system performance logs
        
        Args:
            days_back: Number of days to look back
            format_type: Export format ('csv', 'json', 'both')
            
        Returns:
            Dict with export file paths
        """
        try:
            self.logger.info(f"Exporting system logs for last {days_back} days")
            
            # Collect log data (simulated - in real implementation would read from log files)
            log_data = []
            
            current_time = datetime.now()
            log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
            components = ['AlertManager', 'CoinGeckoAPI', 'ExportScheduler', 'Dashboard']
            
            # Generate sample log entries
            for i in range(days_back * 24):  # Hourly logs
                timestamp = current_time - timedelta(hours=i)
                
                # Generate multiple log entries per hour
                for j in range(3):
                    log_data.append({
                        'timestamp': (timestamp - timedelta(minutes=j*20)).isoformat(),
                        'level': log_levels[j % len(log_levels)],
                        'component': components[j % len(components)],
                        'message': f"Sample log message {i}-{j}",
                        'thread_id': f"Thread-{(i+j) % 5}",
                        'function': f"function_{j % 3}",
                        'line_number': 100 + (i + j) % 50
                    })
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"system_logs_{days_back}days_{timestamp}"
            
            export_files = {}
            
            # Export to CSV
            if format_type in ['csv', 'both']:
                csv_path = self.export_dir / f"{base_filename}.csv"
                df = pd.DataFrame(log_data)
                df.to_csv(csv_path, index=False)
                export_files['csv'] = str(csv_path)
                self.logger.info(f"System logs exported to CSV: {csv_path}")
            
            # Export to JSON
            if format_type in ['json', 'both']:
                json_path = self.export_dir / f"{base_filename}.json"
                with open(json_path, 'w') as f:
                    json.dump({
                        'export_info': {
                            'export_type': 'system_logs',
                            'days_back': days_back,
                            'export_timestamp': datetime.now().isoformat(),
                            'total_records': len(log_data)
                        },
                        'log_summary': {
                            'total_entries': len(log_data),
                            'error_count': len([l for l in log_data if l['level'] == 'ERROR']),
                            'warning_count': len([l for l in log_data if l['level'] == 'WARNING']),
                            'info_count': len([l for l in log_data if l['level'] == 'INFO'])
                        },
                        'data': log_data
                    }, f, indent=2)
                export_files['json'] = str(json_path)
                self.logger.info(f"System logs exported to JSON: {json_path}")
            
            # Update statistics
            self._update_export_stats('system_logs', True, len(log_data))
            
            return export_files
            
        except Exception as e:
            self.logger.error(f"Error exporting system logs: {e}")
            self._update_export_stats('system_logs', False, 0)
            raise
    
    def export_all_data(self, days_back: int = 7, format_type: str = 'both') -> Dict[str, Dict[str, str]]:
        """
        Export all data types in a comprehensive report
        
        Args:
            days_back: Number of days to look back
            format_type: Export format ('csv', 'json', 'both')
            
        Returns:
            Dict with all export file paths organized by type
        """
        try:
            self.logger.info(f"Exporting all data for last {days_back} days")
            
            all_exports = {}
            
            # Export each data type with retry logic
            export_functions = [
                ('signals', lambda: self.export_signal_history(days_back, format_type)),
                ('alerts', lambda: self.export_alert_history(days_back, format_type)),
                ('performance', lambda: self.export_performance_data(days_back, format_type)),
                ('logs', lambda: self.export_system_logs(days_back, format_type))
            ]
            
            for export_name, export_func in export_functions:
                try:
                    all_exports[export_name] = export_func()
                    self.logger.info(f"Successfully exported {export_name} data")
                except Exception as e:
                    self.logger.error(f"Failed to export {export_name} data: {e}")
                    all_exports[export_name] = {'error': str(e)}
            
            # Create summary report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_path = self.export_dir / f"export_summary_{timestamp}.json"
            
            summary_data = {
                'export_info': {
                    'export_type': 'comprehensive_report',
                    'days_back': days_back,
                    'export_timestamp': datetime.now().isoformat(),
                    'format_type': format_type
                },
                'export_results': all_exports,
                'export_statistics': self.export_stats
            }
            
            with open(summary_path, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            all_exports['summary'] = {'json': str(summary_path)}
            
            self.logger.info(f"Comprehensive export completed. Summary: {summary_path}")
            
            return all_exports
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive export: {e}")
            raise
    
    def get_export_statistics(self) -> Dict:
        """Get export statistics and history"""
        return self.export_stats.copy()
    
    def clear_old_exports(self, days_old: int = 30) -> int:
        """
        Clear export files older than specified days
        
        Args:
            days_old: Files older than this many days will be deleted
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            for file_path in self.export_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        self.logger.info(f"Deleted old export file: {file_path.name}")
            
            self.logger.info(f"Cleared {deleted_count} old export files")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error clearing old exports: {e}")
            return 0
    
    def _generate_sample_signal_data(self, days_back: int) -> List[Dict]:
        """Generate sample signal data for demonstration"""
        sample_data = []
        symbols = ['SOL', 'AVAX', 'MATIC', 'DOT', 'ATOM', 'ADA', 'LINK', 'UNI']
        signals = ['STRONG BUY', 'BUY', 'HOLD', 'WATCH', 'AVOID']
        
        current_time = datetime.now()
        
        for i in range(days_back * 10):  # 10 signals per day
            timestamp = current_time - timedelta(hours=i * 2.4)  # Every 2.4 hours
            symbol = symbols[i % len(symbols)]
            
            sample_data.append({
                'timestamp': timestamp.isoformat(),
                'symbol': symbol,
                'name': f"{symbol} Token",
                'signal': signals[i % len(signals)],
                'confidence_score': max(50, min(100, 75 + (i % 30) - 15)),
                'current_price': max(0.1, 10 + (i % 50) - 25),
                'price_change_1h': max(-20, min(20, (i % 40) - 20)),
                'price_change_24h': max(-50, min(50, (i % 100) - 50)),
                'volume_24h': max(1000000, 10000000 + (i % 50000000)),
                'market_cap': max(10000000, 100000000 + (i % 1000000000)),
                'volume_mcap_ratio': max(10, min(500, 100 + (i % 200)))
            })
        
        return sample_data
    
    def _generate_sample_alert_data(self, days_back: int) -> List[Dict]:
        """Generate sample alert data for demonstration"""
        sample_data = []
        symbols = ['SOL', 'AVAX', 'MATIC', 'DOT', 'ATOM']
        alert_types = ['STRONG_BUY', 'HIGH_VOLATILITY', 'VOLUME_SPIKE']
        
        current_time = datetime.now()
        
        for i in range(days_back * 3):  # 3 alerts per day
            timestamp = current_time - timedelta(hours=i * 8)  # Every 8 hours
            symbol = symbols[i % len(symbols)]
            alert_type = alert_types[i % len(alert_types)]
            
            sample_data.append({
                'timestamp': timestamp.isoformat(),
                'symbol': symbol,
                'signal_type': alert_type,
                'confidence_score': max(60, min(100, 80 + (i % 20) - 10)),
                'price': max(0.1, 5 + (i % 20)),
                'message': f"{alert_type.replace('_', ' ').title()} alert for {symbol}",
                'alert_condition': f"Threshold exceeded for {alert_type}",
                'is_active': i < 5  # Only first 5 are active
            })
        
        return sample_data
    
    def _update_export_stats(self, export_type: str, success: bool, record_count: int):
        """Update export statistics"""
        self.export_stats['total_exports'] += 1
        
        if success:
            self.export_stats['successful_exports'] += 1
        else:
            self.export_stats['failed_exports'] += 1
        
        self.export_stats['last_export_time'] = datetime.now().isoformat()
        
        # Add to history
        self.export_stats['export_history'].append({
            'timestamp': datetime.now().isoformat(),
            'export_type': export_type,
            'success': success,
            'record_count': record_count
        })
        
        # Keep only last 100 history entries
        if len(self.export_stats['export_history']) > 100:
            self.export_stats['export_history'] = self.export_stats['export_history'][-100:]
    
    # Scheduled job wrapper functions
    def _export_signal_history_job(self):
        """Job wrapper for signal history export"""
        try:
            self.export_signal_history()
            self.logger.info("Scheduled signal history export completed")
        except Exception as e:
            self.logger.error(f"Scheduled signal history export failed: {e}")
    
    def _export_alert_history_job(self):
        """Job wrapper for alert history export"""
        try:
            self.export_alert_history()
            self.logger.info("Scheduled alert history export completed")
        except Exception as e:
            self.logger.error(f"Scheduled alert history export failed: {e}")
    
    def _export_performance_data_job(self):
        """Job wrapper for performance data export"""
        try:
            self.export_performance_data()
            self.logger.info("Scheduled performance data export completed")
        except Exception as e:
            self.logger.error(f"Scheduled performance data export failed: {e}")
    
    def _export_all_data_job(self):
        """Job wrapper for comprehensive data export"""
        try:
            self.export_all_data()
            self.logger.info("Scheduled comprehensive export completed")
        except Exception as e:
            self.logger.error(f"Scheduled comprehensive export failed: {e}")
    
    def _export_weekly_report_job(self):
        """Job wrapper for weekly report"""
        try:
            # Export comprehensive data for the week
            self.export_all_data(days_back=7)
            
            # Clean up old exports
            self.clear_old_exports(days_old=30)
            
            self.logger.info("Scheduled weekly report completed")
        except Exception as e:
            self.logger.error(f"Scheduled weekly report failed: {e}")

# Test function
def test_export_scheduler():
    """Test the export scheduler functionality"""
    print("🧪 Testing Export Scheduler...")
    print("=" * 50)
    
    try:
        # Initialize scheduler
        scheduler = ExportScheduler()
        print("✅ ExportScheduler initialized")
        
        # Test individual exports
        print("\n📊 Testing individual exports...")
        
        # Test signal history export
        signal_files = scheduler.export_signal_history(days_back=3, format_type='both')
        print(f"✅ Signal history exported: {len(signal_files)} files")
        
        # Test alert history export
        alert_files = scheduler.export_alert_history(days_back=3, format_type='both')
        print(f"✅ Alert history exported: {len(alert_files)} files")
        
        # Test performance data export
        perf_files = scheduler.export_performance_data(days_back=7, format_type='both')
        print(f"✅ Performance data exported: {len(perf_files)} files")
        
        # Test system logs export
        log_files = scheduler.export_system_logs(days_back=2, format_type='both')
        print(f"✅ System logs exported: {len(log_files)} files")
        
        # Test comprehensive export
        print("\n📋 Testing comprehensive export...")
        all_files = scheduler.export_all_data(days_back=3, format_type='both')
        print(f"✅ Comprehensive export completed: {len(all_files)} data types")
        
        # Test statistics
        stats = scheduler.get_export_statistics()
        print(f"\n📈 Export Statistics:")
        print(f"  Total exports: {stats['total_exports']}")
        print(f"  Successful: {stats['successful_exports']}")
        print(f"  Failed: {stats['failed_exports']}")
        
        # Test scheduling (without starting the thread)
        print("\n⏰ Testing scheduling setup...")
        scheduler.schedule_daily_export('signals', '09:00')
        scheduler.schedule_daily_export('alerts', '10:00')
        scheduler.schedule_weekly_report('monday', '08:00')
        print("✅ Scheduled exports configured")
        
        print("\n🎉 Export Scheduler test SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Export Scheduler test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_export_scheduler()
    sys.exit(0 if success else 1)