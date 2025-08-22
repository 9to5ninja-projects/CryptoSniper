import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QTimer
import pandas as pd
from datetime import datetime

# Import our API clients
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_clients.kraken_api import KrakenAPI
from api_clients.coingecko_api import CoinGeckoAPI

class BasicTradingTable(QtWidgets.QTableWidget):
    """Basic table widget for displaying trading data"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
    
    def setup_table(self):
        """Configure table appearance"""
        # Set font
        font = QtGui.QFont("Consolas", 9)
        self.setFont(font)
        
        # Configure behavior
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        # Configure headers
        header = self.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
    
    def populate_kraken_data(self, df: pd.DataFrame):
        """Populate table with Kraken data"""
        if df.empty:
            return
            
        self.setRowCount(len(df))
        self.setColumnCount(len(df.columns))
        self.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, (_, row) in enumerate(df.iterrows()):
            for j, (col_name, value) in enumerate(row.items()):
                item = QtWidgets.QTableWidgetItem(str(value))
                
                # Basic color coding for strategies
                if col_name == "Strategy":
                    if value == "SCALPING":
                        item.setBackground(QtGui.QColor(144, 238, 144))  # Light green
                    elif value == "BREAKOUT":
                        item.setBackground(QtGui.QColor(255, 218, 185))  # Light orange
                    elif value == "GRID":
                        item.setBackground(QtGui.QColor(173, 216, 230))  # Light blue
                    elif value == "AVOID":
                        item.setBackground(QtGui.QColor(255, 182, 193))  # Light red
                
                self.setItem(i, j, item)
    
    def populate_solana_data(self, df: pd.DataFrame):
        """Populate table with Solana data"""
        if df.empty:
            return
            
        # Select display columns
        display_columns = ['name', 'symbol', 'current_price', 'price_change_24h', 'momentum_score', 'signal', 'risk_level']
        display_headers = ['Name', 'Symbol', 'Price (USD)', '24h %', 'Momentum', 'Signal', 'Risk']
        
        self.setRowCount(len(df))
        self.setColumnCount(len(display_columns))
        self.setHorizontalHeaderLabels(display_headers)
        
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col in enumerate(display_columns):
                if col in row:
                    value = row[col]
                    
                    # Format display values
                    if col == 'current_price':
                        display_value = f"${value:.6f}" if value < 0.01 else f"${value:.4f}"
                    elif col == 'price_change_24h':
                        display_value = f"{value:.2f}%" if isinstance(value, (int, float)) else "0.00%"
                    else:
                        display_value = str(value)
                    
                    item = QtWidgets.QTableWidgetItem(display_value)
                    
                    # Basic color coding for signals
                    if col == 'signal':
                        if value == 'STRONG BUY':
                            item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                            item.setForeground(QtGui.QColor(255, 255, 255))  # White text
                        elif value == 'BUY':
                            item.setBackground(QtGui.QColor(144, 238, 144))  # Light green
                        elif value == 'WATCH':
                            item.setBackground(QtGui.QColor(255, 255, 224))  # Light yellow
                        elif value == 'AVOID':
                            item.setBackground(QtGui.QColor(255, 182, 193))  # Light red
                    
                    self.setItem(i, j, item)

class CryptoSniperDashboard(QtWidgets.QMainWindow):
    """Main dashboard window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize API clients
        self.kraken_api = KrakenAPI()
        self.coingecko_api = CoinGeckoAPI()
        
        # Data storage
        self.kraken_df = pd.DataFrame()
        self.solana_df = pd.DataFrame()
        
        self.setup_ui()
        self.setup_timer()
        
        # Load initial data
        self.update_all_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Crypto Sniper Dashboard - Multi-Chain Trading Intelligence")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Header
        self.create_header(layout)
        
        # Tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        
        # Kraken tab
        self.kraken_table = BasicTradingTable()
        self.tab_widget.addTab(self.kraken_table, "📈 Kraken Markets")
        
        # Solana tab
        self.solana_table = BasicTradingTable()
        self.tab_widget.addTab(self.solana_table, "🎯 Solana Sniper")
        
        layout.addWidget(self.tab_widget)
        
        # Footer
        self.create_footer(layout)
    
    def create_header(self, layout):
        """Create header section"""
        header_layout = QtWidgets.QHBoxLayout()
        
        # Status label
        self.status_label = QtWidgets.QLabel("🚀 Initializing Crypto Sniper Dashboard...")
        self.status_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4facfe, stop:1 #00f2fe);
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        # Manual refresh button
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh All")
        self.refresh_btn.clicked.connect(self.manual_refresh)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
    
    def create_footer(self, layout):
        """Create footer section"""
        self.footer_label = QtWidgets.QLabel("Dashboard ready for multi-chain trading intelligence...")
        self.footer_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.footer_label)
    
    def setup_timer(self):
        """Setup auto-refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_data)
        self.timer.start(60000)  # 60 seconds
    
    def manual_refresh(self):
        """Manual refresh button handler"""
        self.update_all_data()
    
    def update_all_data(self):
        """Update all market data"""
        try:
            self.status_label.setText("🔄 Fetching live market data...")
            self.refresh_btn.setEnabled(False)
            
            # Update Kraken data
            self.kraken_df, _ = self.kraken_api.get_live_metrics()
            self.kraken_table.populate_kraken_data(self.kraken_df)
            
            # Update Solana data
            self.solana_df = self.coingecko_api.get_analyzed_solana_tokens(25)
            self.solana_table.populate_solana_data(self.solana_df)
            
            # Update status
            timestamp = datetime.now().strftime('%H:%M:%S')
            kraken_count = len(self.kraken_df)
            solana_count = len(self.solana_df)
            self.status_label.setText(f"✅ Updated: {kraken_count} Kraken pairs, {solana_count} Solana tokens at {timestamp}")
            
            # Update footer
            if not self.solana_df.empty:
                strong_buys = len(self.solana_df[self.solana_df['signal'] == 'STRONG BUY'])
                self.footer_label.setText(f"📊 Market Intelligence: {strong_buys} strong buy signals detected | Last update: {timestamp}")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error updating data: {str(e)}")
        finally:
            self.refresh_btn.setEnabled(True)

def main():
    """Main application entry point"""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Crypto Sniper Dashboard")
    
    # Create and show dashboard
    dashboard = CryptoSniperDashboard()
    dashboard.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()