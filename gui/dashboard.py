import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import pandas as pd
from datetime import datetime
import logging
import traceback

# Setup logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import our API clients
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api_clients.kraken_api import KrakenAPI
    from api_clients.coingecko_api import CoinGeckoAPI
    from api_clients.arbitrage_engine import ArbitrageEngine
    from api_clients.wallet_tracker import SolanaWalletAPI
    logger.info("✅ All API clients imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import API clients: {e}")
    sys.exit(1)

class DataUpdateThread(QThread):
    """Background thread for data updates to prevent UI freezing"""
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, kraken_api, coingecko_api, arbitrage_engine, wallet_api, wallet_address=""):
        super().__init__()
        self.kraken_api = kraken_api
        self.coingecko_api = coingecko_api
        self.arbitrage_engine = arbitrage_engine
        self.wallet_api = wallet_api
        self.wallet_address = wallet_address
        logger.info("🔄 DataUpdateThread initialized")
    
    def run(self):
        """Run data update in background"""
        try:
            logger.info("🔄 Starting background data update...")
            
            # Update Kraken data
            logger.info("📊 Fetching Kraken data...")
            kraken_df, raw_ticker_data = self.kraken_api.get_live_metrics()
            
            # Update arbitrage opportunities
            logger.info("🔄 Calculating arbitrage opportunities...")
            arbitrage_df = self.arbitrage_engine.find_triangular_opportunities(raw_ticker_data)
            
            # Update Solana data
            logger.info("🎯 Fetching Solana token data...")
            solana_df = self.coingecko_api.get_analyzed_solana_tokens(25)
            
            # Update wallet if address provided
            wallet_df = pd.DataFrame()
            if self.wallet_address:
                logger.info(f"👻 Updating wallet: {self.wallet_address[:8]}...")
                wallet_df = self.wallet_api.build_portfolio(self.wallet_address)
            
            # Emit results
            results = {
                'kraken_df': kraken_df,
                'raw_ticker_data': raw_ticker_data,
                'arbitrage_df': arbitrage_df,
                'solana_df': solana_df,
                'wallet_df': wallet_df,
                'timestamp': datetime.now()
            }
            
            logger.info("✅ Background data update completed successfully")
            self.data_updated.emit(results)
            
        except Exception as e:
            error_msg = f"Background update error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(error_msg)

class BasicTradingTable(QtWidgets.QTableWidget):
    """Enhanced table widget with better error handling and logging"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        logger.info("📊 BasicTradingTable initialized")
    
    def setup_table(self):
        """Configure table appearance with enhanced styling"""
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
        
        # Enhanced styling
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def populate_kraken_data(self, df: pd.DataFrame):
        """Populate table with Kraken data - enhanced with error handling"""
        try:
            if df.empty:
                logger.warning("⚠️ Empty Kraken DataFrame received")
                self.show_empty_message("No Kraken data available")
                return
                
            logger.info(f"📊 Populating Kraken table with {len(df)} rows")
            
            self.setRowCount(len(df))
            self.setColumnCount(len(df.columns))
            self.setHorizontalHeaderLabels(df.columns.tolist())
            
            for i, (_, row) in enumerate(df.iterrows()):
                for j, (col_name, value) in enumerate(row.items()):
                    # Handle NaN values
                    display_value = str(value) if pd.notna(value) else "N/A"
                    item = QtWidgets.QTableWidgetItem(display_value)
                    
                    # Enhanced color coding for strategies
                    if col_name == "Strategy":
                        if value == "SCALPING":
                            item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                            item.setForeground(QtGui.QColor(255, 255, 255))
                        elif value == "BREAKOUT":
                            item.setBackground(QtGui.QColor(255, 152, 0))  # Orange
                            item.setForeground(QtGui.QColor(255, 255, 255))
                        elif value == "GRID":
                            item.setBackground(QtGui.QColor(33, 150, 243))  # Blue
                            item.setForeground(QtGui.QColor(255, 255, 255))
                        elif value == "AVOID":
                            item.setBackground(QtGui.QColor(244, 67, 54))  # Red
                            item.setForeground(QtGui.QColor(255, 255, 255))
                    
                    self.setItem(i, j, item)
            
            logger.info("✅ Kraken table populated successfully")
            
        except Exception as e:
            logger.error(f"❌ Error populating Kraken table: {e}")
            self.show_empty_message(f"Error loading Kraken data: {str(e)}")
    
    def populate_solana_data(self, df: pd.DataFrame):
        """Populate table with Solana data - enhanced with better formatting"""
        try:
            if df.empty:
                logger.warning("⚠️ Empty Solana DataFrame received")
                self.show_empty_message("No Solana data available")
                return
                
            logger.info(f"🎯 Populating Solana table with {len(df)} rows")
            
            # Select display columns with fallbacks
            display_columns = ['name', 'symbol', 'current_price', 'price_change_24h', 'momentum_score', 'signal', 'risk_level']
            display_headers = ['Name', 'Symbol', 'Price (USD)', '24h Change %', 'Momentum', 'Signal', 'Risk']
            
            # Filter columns that actually exist in DataFrame
            available_columns = [col for col in display_columns if col in df.columns]
            available_headers = [display_headers[display_columns.index(col)] for col in available_columns]
            
            self.setRowCount(len(df))
            self.setColumnCount(len(available_columns))
            self.setHorizontalHeaderLabels(available_headers)
            
            for i, (_, row) in enumerate(df.iterrows()):
                for j, col in enumerate(available_columns):
                    value = row.get(col, "N/A")
                    
                    # Enhanced formatting
                    if col == 'current_price' and pd.notna(value):
                        try:
                            price_val = float(value)
                            display_value = f"${price_val:.6f}" if price_val < 0.01 else f"${price_val:.4f}"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    elif col == 'price_change_24h' and pd.notna(value):
                        try:
                            change_val = float(value)
                            display_value = f"{change_val:+.2f}%"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    elif col == 'momentum_score' and pd.notna(value):
                        try:
                            momentum_val = float(value)
                            display_value = f"{momentum_val:.1f}"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    else:
                        display_value = str(value) if pd.notna(value) else "N/A"
                    
                    item = QtWidgets.QTableWidgetItem(display_value)
                    
                    # Enhanced color coding for signals
                    if col == 'signal':
                        if value == 'STRONG BUY':
                            item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                            item.setForeground(QtGui.QColor(255, 255, 255))
                        elif value == 'BUY':
                            item.setBackground(QtGui.QColor(129, 199, 132))  # Light green
                        elif value == 'WATCH':
                            item.setBackground(QtGui.QColor(255, 235, 59))  # Yellow
                        elif value == 'AVOID':
                            item.setBackground(QtGui.QColor(244, 67, 54))  # Red
                            item.setForeground(QtGui.QColor(255, 255, 255))
                    
                    # Color coding for price changes
                    elif col == 'price_change_24h' and pd.notna(value):
                        try:
                            change_val = float(value)
                            if change_val > 5:
                                item.setForeground(QtGui.QColor(76, 175, 80))  # Green for >5%
                            elif change_val < -5:
                                item.setForeground(QtGui.QColor(244, 67, 54))  # Red for <-5%
                        except (ValueError, TypeError):
                            pass
                    
                    self.setItem(i, j, item)
            
            logger.info("✅ Solana table populated successfully")
            
        except Exception as e:
            logger.error(f"❌ Error populating Solana table: {e}")
            self.show_empty_message(f"Error loading Solana data: {str(e)}")
    
    def show_empty_message(self, message):
        """Show empty message in table"""
        self.setRowCount(1)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["Status"])
        item = QtWidgets.QTableWidgetItem(message)
        item.setBackground(QtGui.QColor(255, 248, 225))  # Light yellow
        self.setItem(0, 0, item)

class ArbitrageTable(QtWidgets.QTableWidget):
    """Enhanced arbitrage table with better error handling"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        logger.info("🔄 ArbitrageTable initialized")
    
    def setup_table(self):
        """Configure arbitrage table with enhanced styling"""
        font = QtGui.QFont("Consolas", 9)
        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        # Enhanced styling
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                padding: 10px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def populate_arbitrage_data(self, df: pd.DataFrame):
        """Populate table with arbitrage opportunities - enhanced"""
        try:
            if df.empty:
                logger.info("ℹ️ No arbitrage opportunities found (normal in efficient markets)")
                self.setRowCount(1)
                self.setColumnCount(1)
                self.setHorizontalHeaderLabels(["Arbitrage Status"])
                item = QtWidgets.QTableWidgetItem("No profitable arbitrage opportunities found (>0.3% profit threshold)")
                item.setBackground(QtGui.QColor(227, 242, 253))  # Light blue
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setItem(0, 0, item)
                return
            
            logger.info(f"🔄 Found {len(df)} arbitrage opportunities")
            
            # Enhanced display columns
            display_columns = ['path', 'profit_percent', 'profit_usd', 'risk_level', 'execution_quality']
            display_headers = ['Arbitrage Path', 'Profit %', 'Profit (USD)', 'Risk Level', 'Execution Quality']
            
            # Filter available columns
            available_columns = [col for col in display_columns if col in df.columns]
            available_headers = [display_headers[display_columns.index(col)] for col in available_columns]
            
            self.setRowCount(len(df))
            self.setColumnCount(len(available_columns))
            self.setHorizontalHeaderLabels(available_headers)
            
            for i, (_, row) in enumerate(df.iterrows()):
                for j, col in enumerate(available_columns):
                    value = row.get(col, "N/A")
                    
                    # Enhanced formatting
                    if col == 'profit_percent' and pd.notna(value):
                        try:
                            display_value = f"{float(value):.4f}%"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    elif col == 'profit_usd' and pd.notna(value):
                        try:
                            display_value = f"${float(value):.2f}"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    else:
                        display_value = str(value) if pd.notna(value) else "N/A"
                    
                    item = QtWidgets.QTableWidgetItem(display_value)
                    
                    # Enhanced color coding
                    if col == 'profit_percent' and pd.notna(value):
                        try:
                            profit_val = float(value)
                            if profit_val >= 1.0:  # >1% profit
                                item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                                item.setForeground(QtGui.QColor(255, 255, 255))
                            elif profit_val >= 0.5:  # >0.5% profit
                                item.setBackground(QtGui.QColor(129, 199, 132))  # Light green
                        except (ValueError, TypeError):
                            pass
                    
                    elif col == 'risk_level':
                        if value == 'LOW':
                            item.setBackground(QtGui.QColor(129, 199, 132))  # Light green
                        elif value == 'MEDIUM':
                            item.setBackground(QtGui.QColor(255, 235, 59))  # Yellow
                        elif value == 'HIGH':
                            item.setBackground(QtGui.QColor(239, 154, 154))  # Light red
                    
                    elif col == 'execution_quality':
                        if value == 'EXCELLENT':
                            item.setBackground(QtGui.QColor(76, 175, 80))  # Green
                            item.setForeground(QtGui.QColor(255, 255, 255))
                        elif value == 'GOOD':
                            item.setBackground(QtGui.QColor(129, 199, 132))  # Light green
                        elif value in ['FAIR', 'POOR']:
                            item.setBackground(QtGui.QColor(239, 154, 154))  # Light red
                    
                    self.setItem(i, j, item)
            
            # Sort by profit percentage (highest first)
            if 'profit_percent' in available_columns:
                profit_col = available_columns.index('profit_percent')
                self.sortItems(profit_col, QtCore.Qt.SortOrder.DescendingOrder)
            
            logger.info("✅ Arbitrage table populated successfully")
            
        except Exception as e:
            logger.error(f"❌ Error populating arbitrage table: {e}")
            self.setRowCount(1)
            self.setColumnCount(1)
            self.setHorizontalHeaderLabels(["Error"])
            item = QtWidgets.QTableWidgetItem(f"Error loading arbitrage data: {str(e)}")
            item.setBackground(QtGui.QColor(255, 235, 238))  # Light red
            self.setItem(0, 0, item)

class WalletTable(QtWidgets.QTableWidget):
    """Enhanced wallet table with better portfolio display"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        logger.info("👻 WalletTable initialized")
    
    def setup_table(self):
        """Configure wallet table with enhanced styling"""
        font = QtGui.QFont("Consolas", 9)
        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        # Enhanced styling
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f3e5f5;
                padding: 10px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def populate_wallet_data(self, df: pd.DataFrame):
        """Populate table with wallet portfolio data - enhanced"""
        try:
            if df.empty:
                logger.info("ℹ️ No wallet data to display")
                self.setRowCount(1)
                self.setColumnCount(1)
                self.setHorizontalHeaderLabels(["Wallet Status"])
                item = QtWidgets.QTableWidgetItem("Enter wallet address to view portfolio")
                item.setBackground(QtGui.QColor(243, 229, 245))  # Light purple
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setItem(0, 0, item)
                return
            
            logger.info(f"👻 Populating wallet table with {len(df)} tokens")
            
            # Enhanced display columns
            display_columns = ['Symbol', 'Name', 'Balance', 'Price', 'Value', 'Type']
            display_headers = ['Symbol', 'Token Name', 'Balance', 'Price (USD)', 'Value (USD)', 'Type']
            
            # Filter available columns
            available_columns = [col for col in display_columns if col in df.columns]
            available_headers = [display_headers[display_columns.index(col)] for col in available_columns]
            
            self.setRowCount(len(df))
            self.setColumnCount(len(available_columns))
            self.setHorizontalHeaderLabels(available_headers)
            
            for i, (_, row) in enumerate(df.iterrows()):
                for j, col in enumerate(available_columns):
                    value = row.get(col, "N/A")
                    
                    # Enhanced formatting
                    if col == 'Balance' and pd.notna(value):
                        try:
                            balance_val = float(value)
                            symbol = row.get('Symbol', '')
                            if symbol == 'SOL':
                                display_value = f"{balance_val:.4f}"
                            else:
                                display_value = f"{balance_val:.6f}" if balance_val < 1 else f"{balance_val:.2f}"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    elif col == 'Price' and pd.notna(value):
                        try:
                            price_val = float(value)
                            display_value = f"${price_val:.6f}" if price_val < 0.01 else f"${price_val:.4f}"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    elif col == 'Value' and pd.notna(value):
                        try:
                            value_val = float(value)
                            if value_val >= 1000000:
                                display_value = f"${value_val/1000000:.2f}M"
                            elif value_val >= 1000:
                                display_value = f"${value_val/1000:.1f}K"
                            else:
                                display_value = f"${value_val:.2f}"
                        except (ValueError, TypeError):
                            display_value = "N/A"
                    else:
                        display_value = str(value) if pd.notna(value) else "N/A"
                    
                    item = QtWidgets.QTableWidgetItem(display_value)
                    
                    # Enhanced color coding
                    if col == 'Type':
                        if value == 'Native':
                            item.setBackground(QtGui.QColor(129, 199, 132))  # Light green for SOL
                        else:
                            item.setBackground(QtGui.QColor(187, 222, 251))  # Light blue for SPL
                    
                    elif col == 'Value' and pd.notna(value):
                        try:
                            value_val = float(value)
                            if value_val > 100000:  # > $100K
                                item.setBackground(QtGui.QColor(255, 215, 0, 100))  # Gold highlight
                            elif value_val > 10000:  # > $10K
                                item.setBackground(QtGui.QColor(129, 199, 132))  # Light green
                            elif value_val > 1000:  # > $1K
                                item.setBackground(QtGui.QColor(255, 248, 225))  # Light yellow
                        except (ValueError, TypeError):
                            pass
                    
                    self.setItem(i, j, item)
            
            # Sort by value (highest first)
            if 'Value' in available_columns:
                value_column = available_columns.index('Value')
                self.sortItems(value_column, QtCore.Qt.SortOrder.DescendingOrder)
            
            logger.info("✅ Wallet table populated successfully")
            
        except Exception as e:
            logger.error(f"❌ Error populating wallet table: {e}")
            self.setRowCount(1)
            self.setColumnCount(1)
            self.setHorizontalHeaderLabels(["Error"])
            item = QtWidgets.QTableWidgetItem(f"Error loading wallet data: {str(e)}")
            item.setBackground(QtGui.QColor(255, 235, 238))  # Light red
            self.setItem(0, 0, item)

class CryptoSniperDashboard(QtWidgets.QMainWindow):
    """Enhanced main dashboard window with better error handling and logging"""
    
    def __init__(self):
        super().__init__()
        logger.info("🚀 Initializing Crypto Sniper Dashboard...")
        
        # Initialize API clients with error handling
        try:
            self.kraken_api = KrakenAPI()
            logger.info("✅ Kraken API initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kraken API: {e}")
            self.kraken_api = None
        
        try:
            self.coingecko_api = CoinGeckoAPI()
            logger.info("✅ CoinGecko API initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CoinGecko API: {e}")
            self.coingecko_api = None
        
        try:
            self.arbitrage_engine = ArbitrageEngine(min_profit=0.3)
            logger.info("✅ Arbitrage Engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Arbitrage Engine: {e}")
            self.arbitrage_engine = None
        
        try:
            self.wallet_api = SolanaWalletAPI()
            logger.info("✅ Solana Wallet API initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Solana Wallet API: {e}")
            self.wallet_api = None
        
        # Data storage
        self.kraken_df = pd.DataFrame()
        self.solana_df = pd.DataFrame()
        self.arbitrage_df = pd.DataFrame()
        self.wallet_df = pd.DataFrame()
        self.raw_ticker_data = {}
        self.current_wallet_address = ""
        
        # Background update thread
        self.update_thread = None
        self.is_updating = False
        
        self.setup_ui()
        self.setup_timer()
        
        # Load initial data
        logger.info("🔄 Loading initial data...")
        self.update_all_data()
    
    def setup_ui(self):
        """Setup the enhanced user interface"""
        self.setWindowTitle("Crypto Sniper Dashboard - Multi-Chain Trading Intelligence v2.0")
        self.setGeometry(100, 100, 1400, 900)  # Larger window
        
        # Set application icon (if available)
        try:
            self.setWindowIcon(QtGui.QIcon("icon.png"))
        except:
            pass
        
        # Central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Header
        self.create_header(layout)
        
        # Tab widget with enhanced styling
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #2196f3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #e3f2fd;
            }
        """)

        # Enhanced Kraken tab
        kraken_widget = QtWidgets.QWidget()
        kraken_layout = QtWidgets.QVBoxLayout()
        
        kraken_info = QtWidgets.QLabel("📈 Kraken Markets - Live trading pairs with volatility analysis and strategy recommendations")
        kraken_info.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                color: #2e7d32;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
                border-left: 4px solid #4caf50;
                font-weight: bold;
            }
        """)
        kraken_layout.addWidget(kraken_info)
        
        self.kraken_table = BasicTradingTable()
        kraken_layout.addWidget(self.kraken_table)
        kraken_widget.setLayout(kraken_layout)
        self.tab_widget.addTab(kraken_widget, "📈 Kraken Markets")

        # Enhanced Arbitrage tab
        arbitrage_widget = QtWidgets.QWidget()
        arbitrage_layout = QtWidgets.QVBoxLayout()

        arb_info = QtWidgets.QLabel("🔄 Triangular Arbitrage Scanner - Detects A→B→C→A profit opportunities (>0.3% after fees)")
        arb_info.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                color: #1565c0;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
                border-left: 4px solid #2196f3;
                font-weight: bold;
            }
        """)
        arb_info.setWordWrap(True)
        arbitrage_layout.addWidget(arb_info)

        self.arbitrage_table = ArbitrageTable()
        arbitrage_layout.addWidget(self.arbitrage_table)
        arbitrage_widget.setLayout(arbitrage_layout)
        self.tab_widget.addTab(arbitrage_widget, "🔄 Arbitrage Scanner")

        # Enhanced Solana tab
        solana_widget = QtWidgets.QWidget()
        solana_layout = QtWidgets.QVBoxLayout()
        
        solana_info = QtWidgets.QLabel("🎯 Solana Sniper - AI-powered token analysis with momentum scoring and signal generation")
        solana_info.setStyleSheet("""
            QLabel {
                background-color: #f3e5f5;
                color: #7b1fa2;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
                border-left: 4px solid #9c27b0;
                font-weight: bold;
            }
        """)
        solana_layout.addWidget(solana_info)
        
        self.solana_table = BasicTradingTable()
        solana_layout.addWidget(self.solana_table)
        solana_widget.setLayout(solana_layout)
        self.tab_widget.addTab(solana_widget, "🎯 Solana Sniper")

        # Enhanced Wallet tab
        wallet_widget = QtWidgets.QWidget()
        wallet_layout = QtWidgets.QVBoxLayout()

        # Wallet address input with better styling
        wallet_input_frame = QtWidgets.QFrame()
        wallet_input_frame.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        wallet_input_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        wallet_input_layout = QtWidgets.QHBoxLayout(wallet_input_frame)
        
        wallet_label = QtWidgets.QLabel("👻 Phantom Address:")
        wallet_label.setStyleSheet("font-weight: bold; color: #7b1fa2;")
        wallet_input_layout.addWidget(wallet_label)

        self.wallet_address_input = QtWidgets.QLineEdit()
        self.wallet_address_input.setPlaceholderText("Enter your Phantom wallet public address (e.g., 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM)")
        self.wallet_address_input.setFont(QtGui.QFont("Consolas", 10))
        self.wallet_address_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #9c27b0;
            }
        """)
        wallet_input_layout.addWidget(self.wallet_address_input)

        self.load_wallet_btn = QtWidgets.QPushButton("📊 Load Portfolio")
        self.load_wallet_btn.clicked.connect(self.load_wallet_portfolio)
        self.load_wallet_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { 
                background-color: #7b1fa2; 
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
                color: #757575;
            }
        """)
        wallet_input_layout.addWidget(self.load_wallet_btn)
        
        wallet_layout.addWidget(wallet_input_frame)

        # Wallet info panel
        wallet_info = QtWidgets.QLabel("👻 Phantom Wallet Tracker - Enter your public address to view SOL and SPL token balances with real-time USD values")
        wallet_info.setStyleSheet("""
            QLabel {
                background-color: #f3e5f5;
                color: #7b1fa2;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
                border-left: 4px solid #9c27b0;
                font-weight: bold;
            }
        """)
        wallet_info.setWordWrap(True)
        wallet_layout.addWidget(wallet_info)

        self.wallet_table = WalletTable()
        wallet_layout.addWidget(self.wallet_table)
        wallet_widget.setLayout(wallet_layout)
        self.tab_widget.addTab(wallet_widget, "👻 Phantom Wallet")

        layout.addWidget(self.tab_widget)
        
        # Footer
        self.create_footer(layout)
        
        logger.info("✅ UI setup completed")
    
    def create_header(self, layout):
        """Create enhanced header section"""
        header_frame = QtWidgets.QFrame()
        header_frame.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        
        # Status label with better styling
        self.status_label = QtWidgets.QLabel("🚀 Initializing Crypto Sniper Dashboard v2.0...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
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
                font-size: 11px;
            }
            QPushButton:hover { 
                background-color: #45a049; 
            }
            QPushButton:disabled {
                background-color: #81c784;
                color: #f5f5f5;
            }
        """)
        button_layout.addWidget(self.refresh_btn)
        
        # Auto-refresh toggle
        self.auto_refresh_btn = QtWidgets.QPushButton("⏸️ Pause Auto-Refresh")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { 
                background-color: #f57c00; 
            }
            QPushButton:checked {
                background-color: #f44336;
            }
        """)
        button_layout.addWidget(self.auto_refresh_btn)
        
        # Settings button
        self.settings_btn = QtWidgets.QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #607d8b;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { 
                background-color: #546e7a; 
            }
        """)
        button_layout.addWidget(self.settings_btn)
        
        header_layout.addLayout(button_layout)
        layout.addWidget(header_frame)
    
    def create_footer(self, layout):
        """Create enhanced footer section"""
        footer_frame = QtWidgets.QFrame()
        footer_frame.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        
        footer_layout = QtWidgets.QHBoxLayout(footer_frame)
        
        self.footer_label = QtWidgets.QLabel("Dashboard ready for multi-chain trading intelligence...")
        self.footer_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                font-size: 11px;
                color: #424242;
            }
        """)
        footer_layout.addWidget(self.footer_label)
        
        # Connection status indicators
        self.connection_status = QtWidgets.QLabel("🔴 APIs: Connecting...")
        self.connection_status.setStyleSheet("""
            QLabel {
                padding: 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        footer_layout.addWidget(self.connection_status)
        
        layout.addWidget(footer_frame)
    
    def setup_timer(self):
        """Setup enhanced auto-refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_data)
        self.timer.start(90000)  # 90 seconds - more reasonable interval
        self.auto_refresh_enabled = True
        logger.info("⏰ Auto-refresh timer set to 90 seconds")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality"""
        if self.auto_refresh_enabled:
            self.timer.stop()
            self.auto_refresh_enabled = False
            self.auto_refresh_btn.setText("▶️ Resume Auto-Refresh")
            logger.info("⏸️ Auto-refresh paused")
        else:
            self.timer.start(90000)
            self.auto_refresh_enabled = True
            self.auto_refresh_btn.setText("⏸️ Pause Auto-Refresh")
            logger.info("▶️ Auto-refresh resumed")
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Refresh interval setting
        refresh_layout = QtWidgets.QHBoxLayout()
        refresh_layout.addWidget(QtWidgets.QLabel("Auto-refresh interval (seconds):"))
        
        self.refresh_spin = QtWidgets.QSpinBox()
        self.refresh_spin.setRange(30, 600)  # 30 seconds to 10 minutes
        self.refresh_spin.setValue(90)
        self.refresh_spin.setSuffix(" sec")
        refresh_layout.addWidget(self.refresh_spin)
        
        layout.addLayout(refresh_layout)
        
        # Logging level
        log_layout = QtWidgets.QHBoxLayout()
        log_layout.addWidget(QtWidgets.QLabel("Logging level:"))
        
        self.log_combo = QtWidgets.QComboBox()
        self.log_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_combo.setCurrentText("INFO")
        log_layout.addWidget(self.log_combo)
        
        layout.addLayout(log_layout)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        apply_btn = QtWidgets.QPushButton("Apply")
        apply_btn.clicked.connect(lambda: self.apply_settings(dialog))
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def apply_settings(self, dialog):
        """Apply settings changes"""
        try:
            # Update refresh interval
            new_interval = self.refresh_spin.value() * 1000  # Convert to milliseconds
            if self.auto_refresh_enabled:
                self.timer.start(new_interval)
            
            # Update logging level
            log_level = self.log_combo.currentText()
            logging.getLogger().setLevel(getattr(logging, log_level))
            
            logger.info(f"⚙️ Settings updated: refresh={self.refresh_spin.value()}s, log_level={log_level}")
            dialog.accept()
            
        except Exception as e:
            logger.error(f"❌ Failed to apply settings: {e}")
            QtWidgets.QMessageBox.critical(self, "Settings Error", f"Failed to apply settings:\n{str(e)}")
    
    def manual_refresh(self):
        """Enhanced manual refresh with user feedback"""
        if self.is_updating:
            logger.warning("⚠️ Update already in progress, skipping manual refresh")
            return
        
        logger.info("🔄 Manual refresh triggered")
        self.update_all_data()
    
    def load_wallet_portfolio(self):
        """Enhanced wallet loading with better error handling"""
        try:
            wallet_address = self.wallet_address_input.text().strip()
            if not wallet_address:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a wallet address")
                return
            
            if not self.wallet_api:
                QtWidgets.QMessageBox.critical(self, "API Error", "Wallet API not available")
                return
            
            logger.info(f"👻 Loading wallet portfolio for: {wallet_address[:8]}...")
            
            if not self.wallet_api.validate_wallet_address(wallet_address):
                QtWidgets.QMessageBox.warning(self, "Invalid Address", 
                    "Please enter a valid Solana wallet address\n(44 characters, base58 encoded)")
                return
            
            self.current_wallet_address = wallet_address
            self.load_wallet_btn.setEnabled(False)
            self.load_wallet_btn.setText("🔄 Loading...")
            
            # Update status
            self.status_label.setText(f"👻 Loading wallet portfolio...")
            
            # Load portfolio in background thread
            self.wallet_update_thread = DataUpdateThread(
                self.kraken_api, self.coingecko_api, 
                self.arbitrage_engine, self.wallet_api, 
                wallet_address
            )
            self.wallet_update_thread.data_updated.connect(self.handle_wallet_update)
            self.wallet_update_thread.error_occurred.connect(self.handle_wallet_error)
            self.wallet_update_thread.start()
            
        except Exception as e:
            error_msg = f"Failed to load wallet: {str(e)}"
            logger.error(f"❌ {error_msg}")
            QtWidgets.QMessageBox.critical(self, "Wallet Error", error_msg)
            self.load_wallet_btn.setEnabled(True)
            self.load_wallet_btn.setText("📊 Load Portfolio")
    
    def handle_wallet_update(self, results):
        """Handle wallet update results"""
        try:
            self.wallet_df = results.get('wallet_df', pd.DataFrame())
            self.wallet_table.populate_wallet_data(self.wallet_df)
            
            # Update status
            if not self.wallet_df.empty:
                total_value = self.wallet_df['Value'].sum() if 'Value' in self.wallet_df.columns else 0
                token_count = len(self.wallet_df)
                self.status_label.setText(f"✅ Wallet loaded: {token_count} tokens, ${total_value:.2f} total value")
                logger.info(f"✅ Wallet portfolio loaded: {token_count} tokens, ${total_value:.2f}")
            else:
                self.status_label.setText("⚠️ Wallet loaded but no tokens found")
                logger.warning("⚠️ Wallet loaded but no tokens found")
            
        except Exception as e:
            logger.error(f"❌ Error handling wallet update: {e}")
        finally:
            self.load_wallet_btn.setEnabled(True)
            self.load_wallet_btn.setText("📊 Load Portfolio")
    
    def handle_wallet_error(self, error_msg):
        """Handle wallet update errors"""
        logger.error(f"❌ Wallet update error: {error_msg}")
        QtWidgets.QMessageBox.critical(self, "Wallet Error", error_msg)
        self.load_wallet_btn.setEnabled(True)
        self.load_wallet_btn.setText("📊 Load Portfolio")
        self.status_label.setText("❌ Failed to load wallet")
    
    def update_all_data(self):
        """Enhanced data update with background threading"""
        if self.is_updating:
            logger.warning("⚠️ Update already in progress")
            return
        
        # Check if APIs are available
        available_apis = sum([
            bool(self.kraken_api),
            bool(self.coingecko_api), 
            bool(self.arbitrage_engine),
            bool(self.wallet_api)
        ])
        
        if available_apis == 0:
            error_msg = "No API clients available"
            logger.error(f"❌ {error_msg}")
            self.status_label.setText(f"❌ {error_msg}")
            return
        
        try:
            self.is_updating = True
            self.status_label.setText("🔄 Fetching live market data...")
            self.refresh_btn.setEnabled(False)
            
            # Start background update
            self.update_thread = DataUpdateThread(
                self.kraken_api, self.coingecko_api, 
                self.arbitrage_engine, self.wallet_api, 
                self.current_wallet_address
            )
            self.update_thread.data_updated.connect(self.handle_data_update)
            self.update_thread.error_occurred.connect(self.handle_update_error)
            self.update_thread.finished.connect(self.update_finished)
            self.update_thread.start()
            
            logger.info("🔄 Background data update started")
            
        except Exception as e:
            error_msg = f"Failed to start update: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.status_label.setText(f"❌ {error_msg}")
            self.is_updating = False
            self.refresh_btn.setEnabled(True)
    
    def handle_data_update(self, results):
        """Handle successful data update"""
        try:
            timestamp = results.get('timestamp', datetime.now())
            
            # Update data
            self.kraken_df = results.get('kraken_df', pd.DataFrame())
            self.raw_ticker_data = results.get('raw_ticker_data', {})
            self.arbitrage_df = results.get('arbitrage_df', pd.DataFrame())
            self.solana_df = results.get('solana_df', pd.DataFrame())
            if results.get('wallet_df') is not None and not results['wallet_df'].empty:
                self.wallet_df = results['wallet_df']
            
            # Update tables
            self.kraken_table.populate_kraken_data(self.kraken_df)
            self.arbitrage_table.populate_arbitrage_data(self.arbitrage_df)
            self.solana_table.populate_solana_data(self.solana_df)
            self.wallet_table.populate_wallet_data(self.wallet_df)
            
            # Update status
            time_str = timestamp.strftime('%H:%M:%S')
            kraken_count = len(self.kraken_df)
            solana_count = len(self.solana_df)
            arbitrage_count = len(self.arbitrage_df)
            
            wallet_status = f", {len(self.wallet_df)} wallet tokens" if not self.wallet_df.empty else ""
            
            self.status_label.setText(
                f"✅ Updated: {kraken_count} Kraken pairs, {arbitrage_count} arbitrage ops, "
                f"{solana_count} Solana tokens{wallet_status} at {time_str}"
            )
            
            # Update connection status
            api_status = []
            if self.kraken_api: api_status.append("Kraken")
            if self.coingecko_api: api_status.append("CoinGecko") 
            if self.arbitrage_engine: api_status.append("Arbitrage")
            if self.wallet_api: api_status.append("Wallet")
            
            self.connection_status.setText(f"🟢 APIs: {', '.join(api_status)}")
            
            # Update footer with intelligence
            try:
                strong_buys = len(self.solana_df[self.solana_df['signal'] == 'STRONG BUY']) if not self.solana_df.empty else 0
                max_arbitrage = self.arbitrage_df['profit_percent'].max() if not self.arbitrage_df.empty else 0
                wallet_value = self.wallet_df['Value'].sum() if not self.wallet_df.empty and 'Value' in self.wallet_df.columns else 0
                
                wallet_text = f" | Portfolio: ${wallet_value:.2f}" if wallet_value > 0 else ""
                
                self.footer_label.setText(
                    f"📊 Intelligence: {strong_buys} strong buys | "
                    f"Best arbitrage: {max_arbitrage:.3f}%{wallet_text} | Last update: {time_str}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Footer update error: {e}")
            
            logger.info(f"✅ Data update completed successfully at {time_str}")
            
        except Exception as e:
            error_msg = f"Error handling data update: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.status_label.setText(f"❌ {error_msg}")
    
    def handle_update_error(self, error_msg):
        """Handle update errors"""
        logger.error(f"❌ Update error: {error_msg}")
        self.status_label.setText(f"❌ Error updating data: {error_msg}")
        self.connection_status.setText("🔴 APIs: Update failed")
    
    def update_finished(self):
        """Handle update thread completion"""
        self.is_updating = False
        self.refresh_btn.setEnabled(True)
        logger.info("🏁 Update thread finished")
    
    def closeEvent(self, event):
        """Handle application close"""
        logger.info("🛑 Application closing...")
        
        # Stop timers
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        
        # Wait for background threads
        if self.update_thread and self.update_thread.isRunning():
            self.update_thread.quit()
            self.update_thread.wait(3000)  # Wait up to 3 seconds
        
        logger.info("✅ Application closed cleanly")
        event.accept()

def main():
    """Enhanced main application entry point"""
    try:
        logger.info("🚀 Starting Crypto Sniper Dashboard v2.0")
        
        app = QtWidgets.QApplication(sys.argv)
        app.setApplicationName("Crypto Sniper Dashboard v2.0")
        app.setApplicationVersion("2.0.0")
        
        # Set application style
        app.setStyle('Fusion')  # Modern look
        
        # Create and show dashboard
        dashboard = CryptoSniperDashboard()
        dashboard.show()
        
        logger.info("✅ Dashboard started successfully")
        
        # Run application
        exit_code = app.exec()
        logger.info(f"🏁 Application exited with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"💥 Fatal error starting application: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()