# Crypto Sniper Dashboard

Professional multi-chain trading intelligence platform with real-time analytics across Kraken and Solana ecosystems.

## Features

### Kraken Analytics
- Real-time volatility analysis with strategy recommendations
- Triangular arbitrage detection with profit calculations
- Professional risk/reward scoring (0-100 scale)
- Live market data with 10-second refresh cycles

### Solana Ecosystem Sniper  
- Meme coin momentum tracking via CoinGecko API
- Signal generation (Strong Buy, Buy, Watch, Avoid)
- Interactive Plotly charts with multi-timeframe analysis
- Real-time opportunity detection

### Phantom Wallet Integration
- Live portfolio monitoring via Solana RPC
- SOL + SPL token balance tracking
- Auto-refresh capabilities (30s to 5min intervals)
- Portfolio valuation with USD pricing

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/CryptoSniperDashboard.git
cd CryptoSniperDashboard

# Create virtual environment
python -m venv crypto_env
source crypto_env/bin/activate  # Windows: crypto_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## Project Structure

```
CryptoSniperDashboard/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration management
├── kraken/
│   ├── __init__.py
│   ├── api_client.py      # Kraken API integration
│   ├── volatility_analyzer.py
│   └── arbitrage_detector.py
├── solana/
│   ├── __init__.py
│   ├── coingecko_client.py
│   ├── phantom_integration.py
│   └── signal_generator.py
├── dashboard/
│   ├── __init__.py
│   ├── streamlit_app.py   # Main dashboard
│   └── components/        # UI components
├── data/
│   ├── exports/           # CSV exports
│   └── logs/             # Application logs
└── utils/
    ├── __init__.py
    └── helpers.py        # Utility functions
```

## Configuration

Create a .env file in the project root:

```env
# Kraken API (optional for public data)
KRAKEN_API_KEY=your_api_key
KRAKEN_SECRET=your_secret

# Solana RPC
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# CoinGecko API (optional, has rate limits without key)
COINGECKO_API_KEY=your_api_key

# Dashboard settings
REFRESH_INTERVAL=10
AUTO_REFRESH=true
```

## Usage

1. Start the dashboard:
   ```bash
   python main.py
   ```

2. Open your browser to http://localhost:8501

3. Navigate between tabs:
   - **Kraken Analytics**: Real-time market analysis
   - **Solana Sniper**: Meme coin tracking
   - **Portfolio**: Phantom wallet monitoring

## License

MIT License - see LICENSE file for details.