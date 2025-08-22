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
from api_clients.arbitrage_engine import ArbitrageEngine

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

class ArbitrageTable(QtWidgets.QTableWidget):
    """Specialized table for arbitrage opportunities"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
    
    def setup_table(self):
        """Configure arbitrage table"""
        font = QtGui.QFont("Consolas", 9)
        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
    
    def populate_arbitrage_data(self, df: pd.DataFrame):
        """Populate table with arbitrage opportunities"""
        if df.empty:
            # Show "no opportunities" message
            self.setRowCount(1)
            self.setColumnCount(1)
            self.setHorizontalHeaderLabels(["Status"])
            item = QtWidgets.QTableWidgetItem("No arbitrage opportunities found (normal in efficient markets)")
            item.setBackground(QtGui.QColor(240, 248, 255))  # Light blue
            self.setItem(0, 0, item)
            return
        
        # Display columns for arbitrage data
        display_columns = ['path', 'profit_percent', 'risk_level', 'execution', 'min_volume', 'avg_spread']
        display_headers = ['Arbitrage Path', 'Profit %', 'Risk Level', 'Execution', 'Min Volume', 'Avg Spread %']
        
        self.setRowCount(len(df))
        self.setColumnCount(len(display_columns))
        self.setHorizontalHeaderLabels(display_headers)
        
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col in enumerate(display_columns):
                if col in row:
                    value = row[col]
                    
                    # Format display values
                    if col == 'profit_percent':
                        display_value = f"{value:.3f}%"
                    elif col == 'min_volume':
                        display_value = f"{value:,.0f}"
                    elif col == 'avg_spread':
                        display_value = f"{value:.3f}%"
                    else:
                        display_value = str(value)
                    
                    item = QtWidgets.QTableWidgetItem(display_value)
                    
                    # Color coding for risk and execution
                    if col == 'risk_level':
                        if value == 'LOW':
                            item.setBackground(QtGui.QColor(144, 238, 144))  # Light green
                        elif value == 'MEDIUM':
                            item.setBackground(QtGui.QColor(255, 255, 224))  # Light yellow
                        else:  # HIGH
                            item.setBackground(QtGui.QColor(255, 182, 193))  # Light red
                    
                    elif col == 'execution':
                        if value == 'EXCELLENT':
                            item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                            item.setForeground(QtGui.QColor(255, 255, 255))  # White text
                        elif value == 'GOOD':
                            item.setBackground(QtGui.QColor(144, 238, 144))  # Light green
                        elif value == 'FAIR':
                            item.setBackground(QtGui.QColor(255, 255, 224))  # Light yellow
                    
                    elif col == 'profit_percent':
                        profit_val = float(value)
                        if profit_val >= 2.0:
                            item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                            item.setForeground(QtGui.QColor(255, 255, 255))  # White text
                        elif profit_val >= 1.0:
                            item.setBackground(QtGui.QColor(144, 238, 144))  # Light green
                    
                    self.setItem(i, j, item)

class CryptoSniperDashboard(QtWidgets.QMainWindow):
    """Main dashboard window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize API clients
        self.kraken_api = KrakenAPI()
        self.coingecko_api = CoinGeckoAPI()
        self.arbitrage_engine = ArbitrageEngine(min_profit=0.3)  # Add this line
        
        # Data storage
        self.kraken_df = pd.DataFrame()
        self.solana_df = pd.DataFrame()
        self.arbitrage_df = pd.DataFrame()  # Add this line
        self.raw_ticker_data = {}  # Add this line
        
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

        # Arbitrage tab - ADD THIS NEW TAB
        arbitrage_widget = QtWidgets.QWidget()
        arbitrage_layout = QtWidgets.QVBoxLayout()

        # Arbitrage info panel
        arb_info = QtWidgets.QLabel("🔄 Triangular Arbitrage Scanner - Detects A→B→C→A profit opportunities (>0.3% after fees)")
        arb_info.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                color: #2e7d32;
                padding: 10px;
                border-radius: 5px;
                font-size: 11px;
                border-left: 4px solid #4caf50;
            }
        """)
        arb_info.setWordWrap(True)
        arbitrage_layout.addWidget(arb_info)

        self.arbitrage_table = ArbitrageTable()
        arbitrage_layout.addWidget(self.arbitrage_table)

        arbitrage_widget.setLayout(arbitrage_layout)
        self.tab_widget.addTab(arbitrage_widget, "🔄 Arbitrage Scanner")

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
            self.kraken_df, self.raw_ticker_data = self.kraken_api.get_live_metrics()  # Store raw data
            self.kraken_table.populate_kraken_data(self.kraken_df)
            
            # Update arbitrage opportunities
            self.arbitrage_df = self.arbitrage_engine.find_triangular_opportunities(self.raw_ticker_data)
            self.arbitrage_table.populate_arbitrage_data(self.arbitrage_df)
            
            # Update Solana data
            self.solana_df = self.coingecko_api.get_analyzed_solana_tokens(25)
            self.solana_table.populate_solana_data(self.solana_df)
            
            # Update status
            timestamp = datetime.now().strftime('%H:%M:%S')
            kraken_count = len(self.kraken_df)
            solana_count = len(self.solana_df)
            arbitrage_count = len(self.arbitrage_df)
            
            self.status_label.setText(f"✅ Updated: {kraken_count} Kraken pairs, {arbitrage_count} arbitrage ops, {solana_count} Solana tokens at {timestamp}")
            
            # Update footer
            strong_buys = len(self.solana_df[self.solana_df['signal'] == 'STRONG BUY']) if not self.solana_df.empty else 0
            max_arbitrage = self.arbitrage_df['profit_percent'].max() if not self.arbitrage_df.empty else 0
            
            self.footer_label.setText(f"📊 Intelligence: {strong_buys} strong buys | Best arbitrage: {max_arbitrage:.3f}% | Last update: {timestamp}")
            
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