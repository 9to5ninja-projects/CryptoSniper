# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# Import our components
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api_clients.coingecko_api import CoinGeckoAPI
from dashboard.components.alert_manager import AlertManager
from config.settings import get_alert_config, get_config_summary
from data.exports.export_scheduler import ExportScheduler
from trading.paper_trading import create_virtual_portfolio, execute_signal_trade
from trading.signal_integration import create_auto_trading_engine

# Page configuration
st.set_page_config(
    page_title="Crypto Sniper Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'alert_manager' not in st.session_state:
    st.session_state.alert_manager = AlertManager()
if 'coingecko_api' not in st.session_state:
    st.session_state.coingecko_api = CoinGeckoAPI()
if 'export_scheduler' not in st.session_state:
    st.session_state.export_scheduler = ExportScheduler()
if 'last_alert_check' not in st.session_state:
    st.session_state.last_alert_check = None
if 'virtual_portfolio' not in st.session_state:
    st.session_state.virtual_portfolio = create_virtual_portfolio(10000.0)
if 'auto_trading_engine' not in st.session_state:
    st.session_state.auto_trading_engine = create_auto_trading_engine(
        st.session_state.virtual_portfolio,
        st.session_state.alert_manager,
        st.session_state.coingecko_api
    )

# Get alert configuration
alert_config = get_alert_config()

def get_alert_color(alert_type: str) -> str:
    """Get color for alert type"""
    color_map = {
        'STRONG_BUY': '#00ff00',      # Green - Opportunity
        'HIGH_VOLATILITY': '#ff6600', # Orange - Warning  
        'VOLUME_SPIKE': '#ffff00',    # Yellow - Warning
        'BUY': '#90EE90',             # Light Green
        'WATCH': '#FFA500',           # Orange
        'AVOID': '#ff0000'            # Red - Critical
    }
    return color_map.get(alert_type, '#808080')  # Default gray

def format_alert_message(alert: Dict) -> str:
    """Format alert message for display"""
    symbol = alert['symbol']
    alert_type = alert['signal_type']
    confidence = alert['confidence_score']
    timestamp = datetime.fromisoformat(alert['timestamp'])
    
    # Format timestamp
    time_ago = datetime.now() - timestamp
    if time_ago.seconds < 60:
        time_str = "Just now"
    elif time_ago.seconds < 3600:
        time_str = f"{time_ago.seconds // 60}m ago"
    else:
        time_str = f"{time_ago.seconds // 3600}h ago"
    
    return f"**{symbol}** - {alert_type.replace('_', ' ').title()} ({confidence:.1f}%) - {time_str}"

def generate_test_alerts():
    """Generate sample alerts for testing dashboard functionality"""
    # Clear existing alerts first
    st.session_state.alert_manager.clear_all_alerts()
    
    # Sample test data for different alert types
    test_data_sets = [
        {
            'symbol': 'SOL',
            'name': 'Solana',
            'current_price': 98.75,
            'signal': 'STRONG BUY',
            'momentum_score': 92.5,
            'price_change_1h': 8.2,
            'price_change_24h': 15.8,
            'volume_mcap_ratio': 180.0,
            'market_cap': 45000000000,
            'volume_24h': 8100000000
        },
        {
            'symbol': 'AVAX',
            'name': 'Avalanche',
            'current_price': 45.20,
            'signal': 'BUY',
            'momentum_score': 65.0,
            'price_change_1h': 22.1,  # High volatility
            'price_change_24h': 28.5,
            'volume_mcap_ratio': 140.0,
            'market_cap': 15000000000,
            'volume_24h': 2100000000
        },
        {
            'symbol': 'MATIC',
            'name': 'Polygon',
            'current_price': 0.92,
            'signal': 'WATCH',
            'momentum_score': 70.0,
            'price_change_1h': 6.5,
            'price_change_24h': 12.3,
            'volume_mcap_ratio': 280.0,  # Volume spike
            'market_cap': 8000000000,
            'volume_24h': 22400000000
        },
        {
            'symbol': 'DOT',
            'name': 'Polkadot',
            'current_price': 7.45,
            'signal': 'STRONG BUY',
            'momentum_score': 87.3,
            'price_change_1h': 12.8,
            'price_change_24h': 18.9,
            'volume_mcap_ratio': 160.0,
            'market_cap': 9000000000,
            'volume_24h': 1440000000
        },
        {
            'symbol': 'ATOM',
            'name': 'Cosmos',
            'current_price': 12.30,
            'signal': 'BUY',
            'momentum_score': 75.0,
            'price_change_1h': 18.9,  # High volatility
            'price_change_24h': 22.1,
            'volume_mcap_ratio': 190.0,
            'market_cap': 3500000000,
            'volume_24h': 665000000
        }
    ]
    
    # Process each test data set to create alerts
    created_count = 0
    for test_data in test_data_sets:
        alert = st.session_state.alert_manager.process_token_data(test_data)
        if alert:
            created_count += 1
    
    # Show success message
    if created_count > 0:
        st.success(f"✅ Generated {created_count} test alerts!")
    else:
        st.warning("⚠️ No test alerts were created. Check threshold settings.")

def display_alert_sidebar():
    """Display alerts in sidebar"""
    st.sidebar.markdown("---")
    
    # Get active alerts
    active_alerts = st.session_state.alert_manager.get_active_alerts()
    alert_count = len(active_alerts)
    
    # Sidebar header with alert count
    if alert_count > 0:
        st.sidebar.markdown(f"## 🚨 Active Alerts ({alert_count})")
    else:
        st.sidebar.markdown("## 🚨 Active Alerts")
    
    # Alert controls
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if st.button("Clear All", help="Clear all active alerts"):
            for alert in active_alerts:
                st.session_state.alert_manager.remove_alert(alert['id'])
            st.rerun()
    
    with col2:
        if st.button("Test Alerts", help="Generate sample alerts for testing"):
            generate_test_alerts()
            st.rerun()
    
    with col3:
        alerts_enabled = st.checkbox(
            "Enable", 
            value=st.session_state.alert_manager.alerts_enabled,
            help="Enable/disable alert generation"
        )
        if alerts_enabled != st.session_state.alert_manager.alerts_enabled:
            st.session_state.alert_manager.enable_alerts(alerts_enabled)
    
    # Threshold controls
    st.sidebar.markdown("### Alert Thresholds")
    
    # Strong Buy threshold
    strong_buy_threshold = st.sidebar.slider(
        "Strong Buy Confidence",
        min_value=50,
        max_value=100,
        value=int(st.session_state.alert_manager.strong_buy_confidence_threshold),
        step=5,
        help="Minimum confidence score for Strong Buy alerts",
        key="strong_buy_slider"
    )
    if strong_buy_threshold != st.session_state.alert_manager.strong_buy_confidence_threshold:
        st.session_state.alert_manager.update_threshold('STRONG_BUY', strong_buy_threshold)
    
    # Volatility threshold
    volatility_threshold = st.sidebar.slider(
        "High Volatility %",
        min_value=5,
        max_value=50,
        value=int(st.session_state.alert_manager.high_volatility_threshold),
        step=5,
        help="Minimum price change % for volatility alerts",
        key="volatility_slider"
    )
    if volatility_threshold != st.session_state.alert_manager.high_volatility_threshold:
        st.session_state.alert_manager.update_threshold('VOLATILITY', volatility_threshold)
    
    # Volume threshold
    volume_threshold = st.sidebar.slider(
        "Volume Spike %",
        min_value=100,
        max_value=500,
        value=int(st.session_state.alert_manager.volume_spike_threshold),
        step=50,
        help="Minimum volume/mcap ratio for volume spike alerts",
        key="volume_slider"
    )
    if volume_threshold != st.session_state.alert_manager.volume_spike_threshold:
        st.session_state.alert_manager.update_threshold('VOLUME_SPIKE', volume_threshold)
    
    # Configuration controls
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Reset Config", help="Reset all thresholds to defaults"):
            from config.settings import reset_alert_config
            if reset_alert_config():
                st.session_state.alert_manager.reload_config()
                st.success("Configuration reset to defaults!")
                st.rerun()
    
    with col2:
        if st.button("Reload Config", help="Reload configuration from file"):
            if st.session_state.alert_manager.reload_config():
                st.success("Configuration reloaded!")
                st.rerun()
    
    # Display active alerts
    if active_alerts:
        st.sidebar.markdown("### Current Alerts")
        
        for alert in active_alerts[:10]:  # Show max 10 alerts
            alert_color = get_alert_color(alert['signal_type'])
            
            with st.sidebar.container():
                st.markdown(
                    f"""
                    <div style="
                        border-left: 4px solid {alert_color};
                        padding: 8px;
                        margin: 4px 0;
                        background-color: rgba(255,255,255,0.05);
                        border-radius: 4px;
                    ">
                        {format_alert_message(alert)}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        if len(active_alerts) > 10:
            st.sidebar.markdown(f"*... and {len(active_alerts) - 10} more alerts*")
    else:
        st.sidebar.markdown("*No active alerts*")

def display_alert_banner():
    """Display most recent alert as notification banner"""
    active_alerts = st.session_state.alert_manager.get_active_alerts()
    
    if active_alerts:
        latest_alert = active_alerts[0]  # Most recent alert
        alert_color = get_alert_color(latest_alert['signal_type'])
        
        # Create notification banner
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, {alert_color}22, {alert_color}11);
                border: 1px solid {alert_color};
                border-radius: 8px;
                padding: 12px;
                margin: 10px 0;
                text-align: center;
            ">
                <strong>🚨 LATEST ALERT:</strong> {format_alert_message(latest_alert)}
            </div>
            """,
            unsafe_allow_html=True
        )

def check_for_new_alerts():
    """Check for new alerts if enabled"""
    if not st.session_state.alert_manager.alerts_enabled:
        return
    
    current_time = datetime.now()
    
    # Check if enough time has passed since last check (avoid too frequent API calls)
    if (st.session_state.last_alert_check is None or 
        current_time - st.session_state.last_alert_check > timedelta(minutes=2)):
        
        try:
            # Scan for new alerts
            new_alerts = st.session_state.alert_manager.scan_for_alerts(limit=20)
            st.session_state.last_alert_check = current_time
            
            # Show success message if new alerts found
            if new_alerts:
                st.success(f"🚨 Found {len(new_alerts)} new alerts!")
                
        except Exception as e:
            st.error(f"Error checking for alerts: {e}")

def display_token_analysis():
    """Display main token analysis table"""
    st.markdown("## 🎯 Solana Token Analysis")
    
    try:
        # Get analyzed tokens
        with st.spinner("Loading Solana token data..."):
            analyzed_df = st.session_state.coingecko_api.get_analyzed_solana_tokens(limit=30)
        
        if analyzed_df.empty:
            st.warning("No token data available")
            return
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            strong_buys = len(analyzed_df[analyzed_df['signal'] == 'STRONG BUY'])
            st.metric("Strong Buy Signals", strong_buys)
        
        with col2:
            avg_momentum = analyzed_df['momentum_score'].mean()
            st.metric("Avg Momentum Score", f"{avg_momentum:.1f}")
        
        with col3:
            high_vol_tokens = len(analyzed_df[abs(analyzed_df['price_change_1h']) > 10])
            st.metric("High Volatility (>10%)", high_vol_tokens)
        
        with col4:
            active_alerts = len(st.session_state.alert_manager.get_active_alerts())
            st.metric("Active Alerts", active_alerts)
        
        # Display data table
        display_columns = [
            'name', 'symbol', 'current_price', 'price_change_1h', 
            'price_change_24h', 'momentum_score', 'signal', 'risk_level'
        ]
        
        # Format the dataframe for display
        display_df = analyzed_df[display_columns].copy()
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.6f}")
        display_df['price_change_1h'] = display_df['price_change_1h'].apply(lambda x: f"{x:+.2f}%")
        display_df['price_change_24h'] = display_df['price_change_24h'].apply(lambda x: f"{x:+.2f}%")
        display_df['momentum_score'] = display_df['momentum_score'].apply(lambda x: f"{x:.1f}")
        
        # Color code the signals
        def color_signal(val):
            colors = {
                'STRONG BUY': 'background-color: #90EE90',
                'BUY': 'background-color: #98FB98', 
                'WATCH': 'background-color: #FFE4B5',
                'AVOID': 'background-color: #FFB6C1'
            }
            return colors.get(val, '')
        
        # Apply styling
        styled_df = display_df.style.applymap(color_signal, subset=['signal'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=400
        )
        
        # Top opportunities chart
        st.markdown("### Top Opportunities by Momentum Score")
        
        top_10 = analyzed_df.nlargest(10, 'momentum_score')
        
        fig = px.bar(
            top_10,
            x='symbol',
            y='momentum_score',
            color='signal',
            title="Top 10 Tokens by Momentum Score",
            color_discrete_map={
                'STRONG BUY': '#00ff00',
                'BUY': '#90EE90',
                'WATCH': '#FFA500',
                'AVOID': '#ff0000'
            }
        )
        
        fig.update_layout(
            xaxis_title="Token Symbol",
            yaxis_title="Momentum Score",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading token data: {e}")

def display_alert_analytics():
    """Display alert analytics and history"""
    st.markdown("## Alert Analytics")
    
    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "History", "Configuration", "Testing"])
    
    with tab1:
        # Get alert summary
        summary = st.session_state.alert_manager.get_alert_summary()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Alert Summary")
            st.json(summary)
        
        with col2:
            st.markdown("### Current Configuration")
            current_config = st.session_state.alert_manager.get_current_config()
            
            # Display key settings
            st.metric("Alerts Enabled", "Yes" if current_config['alerts_enabled'] else "No")
            st.metric("Strong Buy Threshold", f"{current_config['strong_buy_threshold']:.0f}%")
            st.metric("Volatility Threshold", f"{current_config['volatility_threshold']:.0f}%")
            st.metric("Volume Spike Threshold", f"{current_config['volume_spike_threshold']:.0f}%")
    
    with tab2:
        st.markdown("### Alert History")
        
        # Get recent alerts from history
        alert_history = st.session_state.alert_manager.alert_history[-20:]  # Last 20 alerts
        
        if alert_history:
            st.markdown("#### Recent Alerts with Paper Trading")
            
            for i, alert in enumerate(alert_history):
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{alert.symbol}**")
                    
                    with col2:
                        signal_color = get_alert_color(alert.signal_type)
                        st.markdown(f"<span style='color: {signal_color}'>{alert.signal_type.replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                    
                    with col3:
                        st.write(f"{alert.confidence_score:.1f}%")
                    
                    with col4:
                        st.write(alert.timestamp.strftime("%H:%M"))
                    
                    with col5:
                        # Paper trade button for buy signals
                        if alert.signal_type in ['STRONG_BUY', 'BUY'] and alert.is_active:
                            if st.button("📈 Paper Trade", key=f"trade_buy_{alert.id}_{i}", help="Execute paper trade for this signal"):
                                # Create signal data for paper trading
                                signal_data = {
                                    'symbol': alert.symbol,
                                    'signal': alert.signal_type,
                                    'current_price': getattr(alert, 'current_price', 1.0),  # Default price if not available
                                    'confidence_score': alert.confidence_score
                                }
                                
                                # Get position size from session state or use default
                                position_size = st.session_state.get('default_position_size', 500)
                                
                                # Execute the trade
                                result = execute_signal_trade(st.session_state.virtual_portfolio, signal_data, position_size)
                                
                                if result.get('success', False):
                                    st.success(f"✅ Paper trade executed: {signal_data['symbol']} - ${position_size}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Trade failed: {result.get('error', 'Unknown error')}")
                        
                        # Paper trade button for sell signals
                        elif alert.signal_type in ['AVOID', 'SELL'] and alert.is_active:
                            if st.button("📉 Paper Sell", key=f"trade_sell_{alert.id}_{i}", help="Execute paper sell for this signal"):
                                # Create signal data for paper trading
                                signal_data = {
                                    'symbol': alert.symbol,
                                    'signal': alert.signal_type,
                                    'current_price': getattr(alert, 'current_price', 1.0),
                                    'confidence_score': alert.confidence_score
                                }
                                
                                # Get position size from session state or use default
                                position_size = st.session_state.get('default_position_size', 500)
                                
                                # Execute the trade
                                result = execute_signal_trade(st.session_state.virtual_portfolio, signal_data, position_size)
                                
                                if result.get('success', False):
                                    st.success(f"✅ Paper sell executed: {signal_data['symbol']}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Trade failed: {result.get('error', 'Unknown error')}")
                        else:
                            st.write("-")
                    
                    with col6:
                        status = "🟢 Active" if alert.is_active else "🔴 Inactive"
                        st.write(status)
                    
                    st.markdown("---")
            
            # Also show traditional table view
            st.markdown("#### Alert History Table")
            history_data = []
            for alert in alert_history:
                history_data.append({
                    'Symbol': alert.symbol,
                    'Type': alert.signal_type.replace('_', ' ').title(),
                    'Confidence': f"{alert.confidence_score:.1f}%",
                    'Time': alert.timestamp.strftime("%H:%M:%S"),
                    'Active': "Yes" if alert.is_active else "No"
                })
            
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No alert history available")
    
    with tab3:
        st.markdown("### Configuration Details")
        
        # Display full configuration
        config_summary = get_config_summary()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Current Settings")
            st.json(config_summary['alert_settings'])
        
        with col2:
            st.markdown("#### System Information")
            st.write(f"**Config File Exists:** {config_summary['config_file_exists']}")
            st.write(f"**Config File Path:** `{config_summary['config_file_path']}`")
            
            st.markdown("#### Environment Overrides")
            env_overrides = config_summary['environment_overrides']
            active_overrides = {k: v for k, v in env_overrides.items() if v is not None}
            
            if active_overrides:
                st.json(active_overrides)
            else:
                st.info("No environment variable overrides active")
        
        # Configuration actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Config", help="Download current configuration"):
                config_json = st.session_state.alert_manager.get_current_config()
                st.download_button(
                    label="Download config.json",
                    data=pd.Series(config_json).to_json(indent=2),
                    file_name="alert_config.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Validate Config", help="Check configuration for issues"):
                from config.settings import validate_config
                validation = validate_config()
                
                if validation['valid']:
                    st.success("✅ Configuration is valid!")
                else:
                    st.error("❌ Configuration issues found:")
                    for issue in validation['issues']:
                        st.write(f"- {issue}")
        
        with col3:
            if st.button("Reset All", help="Reset all settings to defaults", type="secondary"):
                from config.settings import reset_alert_config
                if reset_alert_config():
                    st.session_state.alert_manager.reload_config()
                    st.success("All settings reset to defaults!")
                    st.rerun()
                else:
                    st.error("Failed to reset configuration")
    
    with tab4:
        st.markdown("### Alert System Testing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Quick Tests")
            
            if st.button("🧪 Run Integration Tests", help="Run comprehensive alert system tests"):
                with st.spinner("Running integration tests..."):
                    try:
                        # Import and run the test suite
                        import subprocess
                        result = subprocess.run(
                            ["python", "test_alerts.py"], 
                            capture_output=True, 
                            text=True,
                            cwd=project_root
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ All integration tests passed!")
                            with st.expander("Test Output"):
                                st.code(result.stdout)
                        else:
                            st.error("❌ Some tests failed!")
                            with st.expander("Test Output"):
                                st.code(result.stdout)
                                if result.stderr:
                                    st.code(result.stderr)
                    except Exception as e:
                        st.error(f"Error running tests: {e}")
            
            if st.button("🎭 Generate Demo Alerts", help="Create sample alerts for demonstration"):
                generate_test_alerts()
                st.success("Demo alerts generated! Check the sidebar.")
            
            if st.button("🔄 Test Live Market Scan", help="Test alert generation with live market data"):
                with st.spinner("Scanning live market data..."):
                    try:
                        new_alerts = st.session_state.alert_manager.scan_for_alerts(limit=10)
                        if new_alerts:
                            st.success(f"✅ Created {len(new_alerts)} alerts from live market data!")
                            for alert in new_alerts[:3]:  # Show first 3
                                st.write(f"- **{alert.symbol}**: {alert.signal_type} ({alert.confidence_score:.1f}%)")
                        else:
                            st.info("No alerts generated from current market conditions")
                    except Exception as e:
                        st.error(f"Error during market scan: {e}")
        
        with col2:
            st.markdown("#### Test Results")
            
            # Display current alert statistics
            active_alerts = st.session_state.alert_manager.get_active_alerts()
            alert_history = st.session_state.alert_manager.alert_history
            
            st.metric("Active Alerts", len(active_alerts))
            st.metric("Total Alert History", len(alert_history))
            
            if active_alerts:
                st.markdown("**Recent Alert Types:**")
                alert_types = {}
                for alert in active_alerts:
                    alert_type = alert['signal_type']
                    alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
                
                for alert_type, count in alert_types.items():
                    st.write(f"- {alert_type.replace('_', ' ').title()}: {count}")
            
            # Test threshold sensitivity
            st.markdown("---")
            st.markdown("#### Threshold Testing")
            
            current_config = st.session_state.alert_manager.get_current_config()
            st.write(f"**Current Thresholds:**")
            st.write(f"- Strong Buy: {current_config['strong_buy_threshold']:.0f}%")
            st.write(f"- Volatility: {current_config['volatility_threshold']:.0f}%")
            st.write(f"- Volume Spike: {current_config['volume_spike_threshold']:.0f}%")
            
            if st.button("Test Threshold Sensitivity", help="Test how threshold changes affect alert generation"):
                with st.spinner("Testing threshold sensitivity..."):
                    # Test with current thresholds
                    generate_test_alerts()
                    alerts_normal = len(st.session_state.alert_manager.get_active_alerts())
                    
                    # Test with lower thresholds
                    st.session_state.alert_manager.clear_all_alerts()
                    original_thresholds = (
                        st.session_state.alert_manager.strong_buy_confidence_threshold,
                        st.session_state.alert_manager.high_volatility_threshold,
                        st.session_state.alert_manager.volume_spike_threshold
                    )
                    
                    # Temporarily lower thresholds
                    st.session_state.alert_manager.strong_buy_confidence_threshold = 60
                    st.session_state.alert_manager.high_volatility_threshold = 10
                    st.session_state.alert_manager.volume_spike_threshold = 150
                    
                    generate_test_alerts()
                    alerts_lower = len(st.session_state.alert_manager.get_active_alerts())
                    
                    # Restore original thresholds
                    st.session_state.alert_manager.strong_buy_confidence_threshold = original_thresholds[0]
                    st.session_state.alert_manager.high_volatility_threshold = original_thresholds[1]
                    st.session_state.alert_manager.volume_spike_threshold = original_thresholds[2]
                    
                    st.success(f"Threshold sensitivity test complete!")
                    st.write(f"- Normal thresholds: {alerts_normal} alerts")
                    st.write(f"- Lower thresholds: {alerts_lower} alerts")
                    st.write(f"- Sensitivity: {alerts_lower - alerts_normal} additional alerts with lower thresholds")

def display_export_management():
    """Display export management interface"""
    st.markdown("## Data Export & Scheduling")
    
    # Create tabs for different export functions
    export_tab1, export_tab2, export_tab3 = st.tabs(["Manual Export", "Scheduled Export", "Export History"])
    
    with export_tab1:
        st.markdown("### Manual Data Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Export Options")
            
            # Export type selection
            export_type = st.selectbox(
                "Select Data Type",
                ["Signal History", "Alert History", "Performance Data", "System Logs", "All Data"],
                help="Choose what type of data to export"
            )
            
            # Time range selection
            days_back = st.slider(
                "Days to Include",
                min_value=1,
                max_value=30,
                value=7,
                help="Number of days of historical data to include"
            )
            
            # Format selection
            format_type = st.selectbox(
                "Export Format",
                ["Both (CSV + JSON)", "CSV Only", "JSON Only"],
                help="Choose export file format"
            )
            
            # Convert format selection to scheduler format
            format_map = {
                "Both (CSV + JSON)": "both",
                "CSV Only": "csv", 
                "JSON Only": "json"
            }
            selected_format = format_map[format_type]
            
            # Export button
            if st.button("🚀 Export Data", type="primary"):
                with st.spinner(f"Exporting {export_type.lower()}..."):
                    try:
                        if export_type == "Signal History":
                            files = st.session_state.export_scheduler.export_signal_history(days_back, selected_format)
                        elif export_type == "Alert History":
                            files = st.session_state.export_scheduler.export_alert_history(days_back, selected_format)
                        elif export_type == "Performance Data":
                            files = st.session_state.export_scheduler.export_performance_data(days_back, selected_format)
                        elif export_type == "System Logs":
                            files = st.session_state.export_scheduler.export_system_logs(days_back, selected_format)
                        elif export_type == "All Data":
                            files = st.session_state.export_scheduler.export_all_data(days_back, selected_format)
                        
                        st.success(f"✅ {export_type} exported successfully!")
                        
                        # Display file paths
                        if isinstance(files, dict):
                            if 'csv' in files or 'json' in files:
                                st.markdown("**Generated Files:**")
                                for format_key, file_path in files.items():
                                    if format_key in ['csv', 'json']:
                                        st.code(file_path)
                            else:
                                # Handle comprehensive export format
                                st.markdown("**Generated Files:**")
                                for data_type, type_files in files.items():
                                    if isinstance(type_files, dict) and 'csv' in type_files:
                                        st.markdown(f"*{data_type.title()}:*")
                                        for fmt, path in type_files.items():
                                            if fmt in ['csv', 'json']:
                                                st.code(path)
                        
                    except Exception as e:
                        st.error(f"❌ Export failed: {str(e)}")
        
        with col2:
            st.markdown("#### Export Statistics")
            
            # Get and display export statistics
            stats = st.session_state.export_scheduler.get_export_statistics()
            
            col2a, col2b, col2c = st.columns(3)
            with col2a:
                st.metric("Total Exports", stats['total_exports'])
            with col2b:
                st.metric("Successful", stats['successful_exports'])
            with col2c:
                st.metric("Failed", stats['failed_exports'])
            
            # Success rate
            if stats['total_exports'] > 0:
                success_rate = (stats['successful_exports'] / stats['total_exports']) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Last export time
            if stats['last_export_time']:
                last_export = datetime.fromisoformat(stats['last_export_time'])
                time_ago = datetime.now() - last_export
                if time_ago.seconds < 60:
                    time_str = "Just now"
                elif time_ago.seconds < 3600:
                    time_str = f"{time_ago.seconds // 60}m ago"
                else:
                    time_str = f"{time_ago.seconds // 3600}h ago"
                st.metric("Last Export", time_str)
            
            # File cleanup
            st.markdown("---")
            st.markdown("#### File Management")
            
            cleanup_days = st.slider(
                "Delete files older than (days)",
                min_value=7,
                max_value=90,
                value=30,
                help="Files older than this will be deleted"
            )
            
            if st.button("🗑️ Clean Old Files"):
                deleted_count = st.session_state.export_scheduler.clear_old_exports(cleanup_days)
                if deleted_count > 0:
                    st.success(f"✅ Deleted {deleted_count} old export files")
                else:
                    st.info("ℹ️ No old files to delete")
    
    with export_tab2:
        st.markdown("### Scheduled Export Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Schedule New Export")
            
            # Schedule type
            schedule_type = st.selectbox(
                "Schedule Type",
                ["Daily Export", "Weekly Report"],
                help="Choose scheduling frequency"
            )
            
            if schedule_type == "Daily Export":
                # Daily export options
                daily_export_type = st.selectbox(
                    "Export Data Type",
                    ["signals", "alerts", "performance", "all"],
                    help="Type of data to export daily"
                )
                
                daily_time = st.time_input(
                    "Export Time",
                    value=datetime.strptime("09:00", "%H:%M").time(),
                    help="Time of day to run the export"
                )
                
                if st.button("📅 Schedule Daily Export"):
                    try:
                        time_str = daily_time.strftime("%H:%M")
                        st.session_state.export_scheduler.schedule_daily_export(daily_export_type, time_str)
                        st.success(f"✅ Scheduled daily {daily_export_type} export at {time_str}")
                    except Exception as e:
                        st.error(f"❌ Failed to schedule export: {str(e)}")
            
            else:  # Weekly Report
                weekly_day = st.selectbox(
                    "Day of Week",
                    ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                    help="Day of the week to run the report"
                )
                
                weekly_time = st.time_input(
                    "Report Time",
                    value=datetime.strptime("08:00", "%H:%M").time(),
                    help="Time of day to run the weekly report"
                )
                
                if st.button("📊 Schedule Weekly Report"):
                    try:
                        time_str = weekly_time.strftime("%H:%M")
                        st.session_state.export_scheduler.schedule_weekly_report(weekly_day, time_str)
                        st.success(f"✅ Scheduled weekly report on {weekly_day} at {time_str}")
                    except Exception as e:
                        st.error(f"❌ Failed to schedule report: {str(e)}")
        
        with col2:
            st.markdown("#### Scheduler Control")
            
            # Scheduler status
            if hasattr(st.session_state.export_scheduler, 'running') and st.session_state.export_scheduler.running:
                st.success("🟢 Scheduler is running")
                
                if st.button("⏹️ Stop Scheduler"):
                    st.session_state.export_scheduler.stop_scheduler()
                    st.success("Scheduler stopped")
                    st.rerun()
            else:
                st.info("🔴 Scheduler is stopped")
                
                if st.button("▶️ Start Scheduler"):
                    st.session_state.export_scheduler.start_scheduler()
                    st.success("Scheduler started")
                    st.rerun()
            
            # Current schedules (would need to be implemented in scheduler)
            st.markdown("---")
            st.markdown("#### Active Schedules")
            st.info("📋 Schedule management UI would show active scheduled tasks here")
            
            # Quick actions
            st.markdown("---")
            st.markdown("#### Quick Actions")
            
            if st.button("🧪 Test Export"):
                with st.spinner("Running test export..."):
                    try:
                        files = st.session_state.export_scheduler.export_signal_history(1, 'json')
                        st.success("✅ Test export completed successfully!")
                    except Exception as e:
                        st.error(f"❌ Test export failed: {str(e)}")
    
    with export_tab3:
        st.markdown("### Export History")
        
        # Display export history
        stats = st.session_state.export_scheduler.get_export_statistics()
        
        if stats['export_history']:
            # Create DataFrame from export history
            history_df = pd.DataFrame(stats['export_history'])
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            history_df = history_df.sort_values('timestamp', ascending=False)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Exports", len(history_df))
            
            with col2:
                successful = len(history_df[history_df['success'] == True])
                st.metric("Successful", successful)
            
            with col3:
                failed = len(history_df[history_df['success'] == False])
                st.metric("Failed", failed)
            
            with col4:
                total_records = history_df['record_count'].sum()
                st.metric("Total Records", f"{total_records:,}")
            
            # Export history table
            st.markdown("#### Recent Export History")
            
            # Format the display
            display_df = history_df.copy()
            display_df['Status'] = display_df['success'].apply(lambda x: '✅ Success' if x else '❌ Failed')
            display_df['Export Type'] = display_df['export_type'].str.replace('_', ' ').str.title()
            display_df['Timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_df['Records'] = display_df['record_count'].apply(lambda x: f"{x:,}")
            
            # Display table
            st.dataframe(
                display_df[['Timestamp', 'Export Type', 'Status', 'Records']],
                use_container_width=True,
                hide_index=True
            )
            
            # Export type distribution chart
            if len(history_df) > 1:
                st.markdown("#### Export Type Distribution")
                
                type_counts = history_df['export_type'].value_counts()
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Export Types Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("📋 No export history available yet. Run some exports to see history here.")

def display_portfolio_tracker():
    """Display portfolio/wallet tracking interface"""
    st.markdown("## 💼 Portfolio Tracker")
    st.markdown("Track your Solana wallet balances and portfolio value")
    
    try:
        # Import wallet API
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from api_clients.wallet_tracker import SolanaWalletAPI
        
        # Initialize wallet API
        if 'wallet_api' not in st.session_state:
            st.session_state.wallet_api = SolanaWalletAPI()
        
        wallet_api = st.session_state.wallet_api
        
        # Wallet Connection Section
        st.markdown("### 🔗 Wallet Connection")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Wallet address input
            wallet_address = st.text_input(
                "Enter Solana Wallet Address",
                placeholder="e.g., 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                help="Enter your Solana wallet public address to track portfolio"
            )
            
            # Store wallet address in session state
            if wallet_address:
                st.session_state.wallet_address = wallet_address
        
        with col2:
            st.markdown("#### Quick Actions")
            if st.button("🔄 Refresh Portfolio"):
                if 'portfolio_data' in st.session_state:
                    del st.session_state.portfolio_data
                st.rerun()
            
            if st.button("🗑️ Clear Wallet"):
                if 'wallet_address' in st.session_state:
                    del st.session_state.wallet_address
                if 'portfolio_data' in st.session_state:
                    del st.session_state.portfolio_data
                st.rerun()
        
        # Validate wallet address
        if wallet_address:
            is_valid = wallet_api.validate_wallet_address(wallet_address)
            
            if is_valid:
                st.success(f"✅ Valid wallet address: `{wallet_address[:8]}...{wallet_address[-8:]}`")
                
                # Portfolio Overview Section
                st.markdown("### 📊 Portfolio Overview")
                
                # Load portfolio data
                if st.button("📈 Load Portfolio", type="primary") or 'portfolio_data' in st.session_state:
                    
                    if 'portfolio_data' not in st.session_state:
                        with st.spinner("Loading portfolio data..."):
                            try:
                                portfolio_df = wallet_api.build_portfolio(wallet_address)
                                st.session_state.portfolio_data = portfolio_df
                            except Exception as e:
                                st.error(f"❌ Error loading portfolio: {e}")
                                return
                    
                    portfolio_df = st.session_state.portfolio_data
                    
                    if not portfolio_df.empty:
                        # Portfolio Summary
                        total_value = portfolio_df['Value'].sum()
                        sol_balance = portfolio_df[portfolio_df['Symbol'] == 'SOL']['Balance'].iloc[0] if 'SOL' in portfolio_df['Symbol'].values else 0
                        token_count = len(portfolio_df) - 1  # Exclude SOL
                        
                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("💰 Total Value", f"${total_value:.2f}")
                        
                        with col2:
                            st.metric("🟣 SOL Balance", f"{sol_balance:.4f} SOL")
                        
                        with col3:
                            st.metric("🪙 Token Count", f"{token_count} tokens")
                        
                        with col4:
                            sol_price = wallet_api.get_sol_price()
                            st.metric("📈 SOL Price", f"${sol_price:.2f}")
                        
                        # Portfolio Breakdown
                        st.markdown("### 💎 Portfolio Breakdown")
                        
                        # Format the dataframe for display
                        display_df = portfolio_df.copy()
                        display_df['Balance'] = display_df['Balance'].apply(lambda x: f"{x:.6f}")
                        display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.4f}")
                        display_df['Value'] = display_df['Value'].apply(lambda x: f"${x:.2f}")
                        
                        # Display portfolio table
                        st.dataframe(
                            display_df[['Symbol', 'Name', 'Balance', 'Price', 'Value', 'Type']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Portfolio Allocation Chart
                        if len(portfolio_df) > 1:
                            st.markdown("### 📊 Portfolio Allocation")
                            
                            # Create pie chart data
                            chart_data = portfolio_df[['Symbol', 'Value']].copy()
                            chart_data = chart_data[chart_data['Value'] > 0]
                            
                            if not chart_data.empty:
                                # Use Streamlit's built-in chart
                                st.bar_chart(chart_data.set_index('Symbol')['Value'])
                        
                        # Wallet Activity Section
                        st.markdown("### 🔍 Wallet Information")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Wallet Address:**")
                            st.code(wallet_address, language="text")
                            
                            st.markdown("**Network:**")
                            st.info("🌐 Solana Mainnet")
                        
                        with col2:
                            st.markdown("**Last Updated:**")
                            from datetime import datetime
                            st.info(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            st.markdown("**Data Source:**")
                            st.info("🔗 Solana RPC + CoinGecko")
                        
                        # Additional Features
                        with st.expander("🔧 Advanced Features"):
                            st.markdown("**Coming Soon:**")
                            st.write("- 📈 Historical portfolio tracking")
                            st.write("- 🚨 Balance change alerts")
                            st.write("- 💱 Token price tracking")
                            st.write("- 📊 Performance analytics")
                            st.write("- 🔄 Auto-refresh intervals")
                    
                    else:
                        st.warning("⚠️ No portfolio data found for this wallet address")
                        st.info("💡 This could mean:")
                        st.write("- The wallet has no SOL or token balances")
                        st.write("- The wallet address is new/unused")
                        st.write("- There was an issue connecting to Solana RPC")
            
            else:
                st.error("❌ Invalid Solana wallet address format")
                st.info("💡 Solana addresses are 32-44 characters long and base58 encoded")
        
        else:
            # Welcome section when no wallet is connected
            st.markdown("### 👋 Welcome to Portfolio Tracker")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                **Track your Solana portfolio in real-time:**
                
                🔗 **Connect Your Wallet**
                - Enter your Solana wallet public address
                - View SOL and SPL token balances
                - See total portfolio value in USD
                
                📊 **Portfolio Analytics**
                - Real-time balance tracking
                - Token allocation breakdown
                - Price and value calculations
                
                🔄 **Live Updates**
                - Refresh portfolio data anytime
                - Connect to Solana mainnet RPC
                - Get latest token prices
                """)
            
            with col2:
                st.markdown("#### 🔒 Privacy & Security")
                st.info("""
                **Your wallet is safe:**
                - Only public address needed
                - Read-only access
                - No private keys required
                - No transaction capabilities
                """)
                
                st.markdown("#### 📝 Example Address")
                st.code("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", language="text")
                st.caption("*Sample public address for testing*")
    
    except ImportError as e:
        st.error(f"❌ Wallet tracking components not available: {e}")
        st.info("💡 Check wallet_tracker.py configuration")
    except Exception as e:
        st.error(f"❌ Error loading portfolio interface: {e}")
        st.info("🔧 Check wallet system configuration and try again")

def display_ml_training():
    """Display ML training interface"""
    st.markdown("## 🤖 ML Signal Enhancement")
    st.markdown("Train and manage machine learning models for enhanced signal generation")
    
    try:
        # Import ML components
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from solana.signal_generator import SolanaSignalGenerator
        from data.exports.export_scheduler import ExportScheduler
        
        # Initialize ML generator
        if 'ml_generator' not in st.session_state:
            st.session_state.ml_generator = SolanaSignalGenerator(enable_ml=True)
        
        ml_gen = st.session_state.ml_generator
        
        # ML Status Section
        st.markdown("### 📊 ML Model Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ml_status = ml_gen.get_ml_status()
            if ml_status.get('ml_enabled', False):
                st.success("✅ ML Enabled")
            else:
                st.error("❌ ML Disabled")
        
        with col2:
            if ml_status.get('is_trained', False):
                st.success("✅ Model Trained")
            else:
                st.warning("⚠️ Model Not Trained")
        
        with col3:
            feature_count = ml_status.get('feature_count', 0)
            st.info(f"📈 Features: {feature_count}")
        
        # Training Section
        st.markdown("### 🎯 Model Training")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Training Data")
            
            # Training data source selection
            data_source = st.selectbox(
                "Select Training Data Source",
                ["Generate Sample Data", "Use Export History", "Upload CSV"],
                help="Choose where to get training data from"
            )
            
            if data_source == "Generate Sample Data":
                sample_size = st.slider("Sample Size", 20, 200, 50, help="Number of sample data points to generate")
                
                if st.button("🚀 Train Model with Sample Data", type="primary"):
                    with st.spinner("Generating sample data and training model..."):
                        try:
                            # Generate sample training data
                            training_data = generate_sample_training_data(sample_size)
                            
                            # Train model
                            results = ml_gen.train_ml_model(training_data)
                            
                            if 'error' in results:
                                st.error(f"❌ Training failed: {results['error']}")
                            else:
                                st.success("✅ Model trained successfully!")
                                
                                # Display results
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Training Samples", results.get('training_samples', 0))
                                    st.metric("Train Accuracy", f"{results.get('train_accuracy', 0):.3f}")
                                with col_b:
                                    st.metric("Test Samples", results.get('test_samples', 0))
                                    st.metric("Test Accuracy", f"{results.get('test_accuracy', 0):.3f}")
                                
                                st.info(f"Signal Classes: {', '.join(results.get('signal_classes', []))}")
                                
                        except Exception as e:
                            st.error(f"❌ Training error: {e}")
            
            elif data_source == "Use Export History":
                st.info("📋 This feature will use historical export data for training")
                if st.button("🚀 Train with Export History"):
                    st.warning("⚠️ Export history training not yet implemented")
            
            elif data_source == "Upload CSV":
                uploaded_file = st.file_uploader("Upload Training Data CSV", type=['csv'])
                if uploaded_file and st.button("🚀 Train with Uploaded Data"):
                    st.warning("⚠️ CSV upload training not yet implemented")
        
        with col2:
            st.markdown("#### Quick Actions")
            
            if st.button("🔄 Refresh Status"):
                st.rerun()
            
            if st.button("🗑️ Reset Model"):
                if 'ml_generator' in st.session_state:
                    del st.session_state.ml_generator
                st.success("Model reset! Refresh to reinitialize.")
        
        # Model Performance Section
        if ml_status.get('is_trained', False):
            st.markdown("### 📈 Model Performance")
            
            # Feature Importance
            importance = ml_gen.ml_generator.get_feature_importance() if ml_gen.ml_generator else {}
            
            if importance:
                st.markdown("#### 🎯 Feature Importance")
                
                # Create importance chart
                import pandas as pd
                importance_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Importance'])
                importance_df = importance_df.head(10)  # Top 10 features
                
                st.bar_chart(importance_df.set_index('Feature'))
                
                # Feature importance table
                with st.expander("📊 Detailed Feature Importance"):
                    st.dataframe(importance_df, use_container_width=True)
            
            # Test Signal Generation
            st.markdown("#### 🧪 Test Signal Generation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Test Data Input**")
                test_price = st.number_input("Current Price", value=1.50, min_value=0.01)
                test_change_1h = st.number_input("1h Change %", value=2.5, min_value=-50.0, max_value=50.0)
                test_change_24h = st.number_input("24h Change %", value=8.3, min_value=-50.0, max_value=50.0)
                test_volume = st.number_input("24h Volume", value=1000000, min_value=1000)
                test_mcap = st.number_input("Market Cap", value=50000000, min_value=100000)
            
            with col2:
                if st.button("🎯 Generate Test Signal"):
                    test_data = {
                        'current_price': test_price,
                        'price_change_1h': test_change_1h,
                        'price_change_24h': test_change_24h,
                        'volume_24h': test_volume,
                        'market_cap': test_mcap,
                        'symbol': 'TEST',
                        'name': 'Test Token'
                    }
                    
                    signal = ml_gen.generate_signal(test_data)
                    
                    st.markdown("**Generated Signal:**")
                    st.success(f"🎯 Signal: **{signal.get('signal', 'N/A')}**")
                    st.info(f"📊 Confidence: **{signal.get('confidence_score', 0)}%**")
                    st.info(f"🔧 Type: **{signal.get('signal_type', 'N/A')}**")
                    
                    if 'ml_enhancement' in signal and signal['ml_enhancement']:
                        ml_info = signal['ml_enhancement']
                        st.markdown("**ML Enhancement Details:**")
                        st.write(f"- ML Signal: {ml_info.get('ml_signal', 'N/A')}")
                        st.write(f"- ML Confidence: {ml_info.get('ml_confidence', 0):.3f}")
                        st.write(f"- Rule Signal: {ml_info.get('rule_signal', 'N/A')}")
                        st.write(f"- Signals Agree: {ml_info.get('signals_agree', False)}")
        
        else:
            st.info("🎯 Train a model to see performance metrics and test signal generation")
    
    except ImportError as e:
        st.error(f"❌ ML components not available: {e}")
        st.info("💡 Install scikit-learn to enable ML features: `pip install scikit-learn`")
    except Exception as e:
        st.error(f"❌ Error loading ML interface: {e}")
        st.info("🔧 Check ML system configuration and try again")

def generate_sample_training_data(num_samples=50):
    """Generate sample training data for ML training"""
    import random
    from datetime import datetime, timedelta
    
    training_data = []
    
    for i in range(num_samples):
        # Generate realistic crypto data
        price_change_24h = random.uniform(-20, 20)
        price_change_1h = random.uniform(-5, 5)
        volume_24h = random.uniform(100000, 10000000)
        market_cap = random.uniform(1000000, 1000000000)
        current_price = random.uniform(0.01, 100)
        
        # Simple rule-based signal assignment for training
        if price_change_24h > 10:
            signal = 'BUY'
        elif price_change_24h < -10:
            signal = 'AVOID'
        elif abs(price_change_24h) < 3:
            signal = 'HOLD'
        else:
            signal = 'WATCH'
        
        data_point = {
            'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
            'symbol': f'TOKEN{i}',
            'signal': signal,
            'current_price': current_price,
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'volume_24h': volume_24h,
            'market_cap': market_cap
        }
        
        training_data.append(data_point)
    
    return training_data

def display_paper_trading():
    """Display paper trading interface"""
    st.markdown("## 📈 Paper Trading Portfolio")
    
    portfolio = st.session_state.virtual_portfolio
    
    # Get current prices for portfolio calculation
    try:
        with st.spinner("Loading current prices..."):
            analyzed_df = st.session_state.coingecko_api.get_analyzed_solana_tokens(limit=50)
        
        # Create price dictionary from analyzed tokens
        current_prices = {}
        if not analyzed_df.empty:
            for _, row in analyzed_df.iterrows():
                current_prices[row['symbol']] = row['current_price']
    except Exception as e:
        st.error(f"Error loading current prices: {e}")
        current_prices = {}
    
    # Get portfolio summary
    portfolio_summary = portfolio.get_portfolio_summary(current_prices)
    performance = portfolio_summary['performance_metrics']
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Portfolio Value", 
            f"${performance['current_portfolio_value']:,.2f}",
            f"{performance['total_return_percentage']:+.2f}%"
        )
    
    with col2:
        st.metric(
            "Cash Balance", 
            f"${performance['cash_balance']:,.2f}"
        )
    
    with col3:
        st.metric(
            "Total Trades", 
            performance['total_trades'],
            f"Win Rate: {performance['win_rate']:.1f}%"
        )
    
    with col4:
        unrealized_pnl = performance.get('unrealized_pnl', 0)
        st.metric(
            "Unrealized P&L", 
            f"${unrealized_pnl:+,.2f}",
            f"Positions: {performance['positions_count']}"
        )
    
    # Create tabs for different views
    ptab1, ptab2, ptab3, ptab4, ptab5 = st.tabs(["Positions", "Trade History", "Performance", "Settings", "Auto-Trading"])
    
    with ptab1:
        st.markdown("### Current Positions")
        
        position_details = portfolio_summary['position_details']
        if position_details:
            # Create DataFrame for positions
            positions_df = pd.DataFrame(position_details)
            
            # Format for display
            display_positions = positions_df.copy()
            display_positions['avg_price'] = display_positions['avg_price'].apply(lambda x: f"${x:.6f}")
            display_positions['current_price'] = display_positions['current_price'].apply(lambda x: f"${x:.6f}")
            display_positions['market_value'] = display_positions['market_value'].apply(lambda x: f"${x:,.2f}")
            display_positions['total_cost'] = display_positions['total_cost'].apply(lambda x: f"${x:,.2f}")
            display_positions['unrealized_pnl'] = display_positions['unrealized_pnl'].apply(lambda x: f"${x:+,.2f}")
            display_positions['unrealized_pnl_percentage'] = display_positions['unrealized_pnl_percentage'].apply(lambda x: f"{x:+.2f}%")
            display_positions['quantity'] = display_positions['quantity'].apply(lambda x: f"{x:.4f}")
            
            st.dataframe(display_positions, use_container_width=True)
        else:
            st.info("No open positions")
    
    with ptab2:
        st.markdown("### Recent Trades")
        
        recent_trades = portfolio_summary['recent_trades']
        if recent_trades:
            # Create DataFrame for trades
            trades_data = []
            for trade in recent_trades:
                trade_data = {
                    'Time': datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S'),
                    'Symbol': trade['symbol'],
                    'Side': trade['side'],
                    'Quantity': f"{trade['quantity']:.4f}",
                    'Price': f"${trade['price']:.6f}",
                    'Value': f"${trade['total_value']:,.2f}"
                }
                
                # Add P&L for sell trades
                if trade['side'] == 'SELL' and 'pnl' in trade:
                    trade_data['P&L'] = f"${trade['pnl']:+,.2f}"
                    trade_data['P&L %'] = f"{trade['pnl_percentage']:+.2f}%"
                else:
                    trade_data['P&L'] = "-"
                    trade_data['P&L %'] = "-"
                
                trades_data.append(trade_data)
            
            trades_df = pd.DataFrame(trades_data)
            st.dataframe(trades_df, use_container_width=True)
        else:
            st.info("No trades executed yet")
    
    with ptab3:
        st.markdown("### Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Returns")
            st.metric("Total Return", f"{performance['total_return_percentage']:+.2f}%")
            st.metric("Realized P&L", f"${performance.get('total_realized_pnl', 0):+,.2f}")
            st.metric("Unrealized P&L", f"${performance.get('unrealized_pnl', 0):+,.2f}")
        
        with col2:
            st.markdown("#### Risk Metrics")
            st.metric("Max Drawdown", f"{performance.get('max_drawdown', 0):.2f}%")
            st.metric("Sharpe Ratio", f"{performance.get('sharpe_ratio', 0):.2f}")
            st.metric("Win Rate", f"{performance['win_rate']:.1f}%")
        
        # Performance chart (if we have portfolio history)
        if len(portfolio.portfolio_history) > 1:
            st.markdown("#### Portfolio Value Over Time")
            
            history_data = []
            for entry in portfolio.portfolio_history:
                history_data.append({
                    'timestamp': datetime.fromisoformat(entry['timestamp']),
                    'value': entry['value']
                })
            
            history_df = pd.DataFrame(history_data)
            
            fig = px.line(
                history_df, 
                x='timestamp', 
                y='value',
                title='Portfolio Value Over Time',
                labels={'value': 'Portfolio Value ($)', 'timestamp': 'Time'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with ptab4:
        st.markdown("### Portfolio Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Portfolio Actions")
            
            if st.button("💾 Save Portfolio State", help="Save current portfolio to file"):
                if portfolio.save_portfolio_state():
                    st.success("Portfolio state saved successfully!")
                else:
                    st.error("Failed to save portfolio state")
            
            if st.button("🔄 Load Portfolio State", help="Load portfolio from file"):
                if portfolio.load_portfolio_state():
                    st.success("Portfolio state loaded successfully!")
                    st.rerun()
                else:
                    st.warning("No saved portfolio state found")
            
            if st.button("🗑️ Reset Portfolio", help="Reset portfolio to starting balance", type="secondary"):
                if st.button("⚠️ Confirm Reset", help="This will clear all positions and trades"):
                    st.session_state.virtual_portfolio = create_virtual_portfolio(10000.0)
                    st.success("Portfolio reset to $10,000 starting balance")
                    st.rerun()
        
        with col2:
            st.markdown("#### Trading Settings")
            
            # Default position size setting
            default_position_size = st.number_input(
                "Default Position Size ($)",
                min_value=100,
                max_value=5000,
                value=500,
                step=100,
                help="Default USD amount for paper trades"
            )
            
            # Store in session state
            st.session_state.default_position_size = default_position_size
            
            st.markdown("#### Portfolio Information")
            st.write(f"**Starting Balance:** ${portfolio.starting_balance:,.2f}")
            st.write(f"**Total Trades:** {portfolio.total_trades}")
            st.write(f"**Winning Trades:** {portfolio.winning_trades}")
            st.write(f"**Losing Trades:** {portfolio.losing_trades}")
    
    with ptab5:
        st.markdown("### Automated Paper Trading")
        
        auto_engine = st.session_state.auto_trading_engine
        status = auto_engine.get_status()
        
        # Status overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_text = "🟢 Active" if status['enabled'] else "🔴 Inactive"
            st.metric("Auto-Trading Status", status_text)
        
        with col2:
            st.metric("Auto-Trades Executed", status['auto_trades_executed'])
        
        with col3:
            st.metric("Current Positions", f"{status['current_positions']}/{status['max_positions']}")
        
        with col4:
            st.metric("Min Confidence", f"{status['min_confidence_threshold']:.0f}%")
        
        st.markdown("---")
        
        # Control panel
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Auto-Trading Controls")
            
            if not status['enabled']:
                if st.button("🚀 Start Auto-Trading", help="Start automated paper trading"):
                    if auto_engine.start_monitoring():
                        st.success("Auto-trading started!")
                        st.rerun()
                    else:
                        st.error("Failed to start auto-trading")
            else:
                if st.button("⏹️ Stop Auto-Trading", help="Stop automated paper trading"):
                    auto_engine.stop_monitoring()
                    st.success("Auto-trading stopped!")
                    st.rerun()
            
            if st.button("🧹 Clear Alert Cache", help="Clear processed alerts cache"):
                auto_engine.clear_processed_alerts()
                st.success("Alert cache cleared!")
            
            # Manual trade execution
            st.markdown("#### Manual Signal Trading")
            
            if st.button("🔍 Scan & Trade High-Confidence Signals", help="Manually scan for and execute high-confidence trades"):
                with st.spinner("Scanning for high-confidence signals..."):
                    try:
                        # Get active alerts
                        active_alerts = st.session_state.alert_manager.get_active_alerts()
                        high_conf_alerts = [
                            alert for alert in active_alerts 
                            if alert['confidence_score'] >= status['min_confidence_threshold']
                            and alert['signal_type'] in ['STRONG_BUY', 'BUY']
                        ]
                        
                        if high_conf_alerts:
                            trades_executed = 0
                            for alert in high_conf_alerts[:3]:  # Limit to 3 trades
                                # Get current price
                                try:
                                    analyzed_df = st.session_state.coingecko_api.get_analyzed_solana_tokens(limit=50)
                                    if not analyzed_df.empty:
                                        symbol_data = analyzed_df[analyzed_df['symbol'] == alert['symbol']]
                                        if not symbol_data.empty:
                                            current_price = float(symbol_data.iloc[0]['current_price'])
                                            
                                            signal_data = {
                                                'symbol': alert['symbol'],
                                                'signal': alert['signal_type'],
                                                'current_price': current_price,
                                                'confidence_score': alert['confidence_score']
                                            }
                                            
                                            result = execute_signal_trade(portfolio, signal_data, status['default_position_size'])
                                            if result.get('success', False):
                                                trades_executed += 1
                                except Exception as e:
                                    st.error(f"Error trading {alert['symbol']}: {e}")
                            
                            if trades_executed > 0:
                                st.success(f"✅ Executed {trades_executed} high-confidence trades!")
                                st.rerun()
                            else:
                                st.warning("No trades could be executed")
                        else:
                            st.info("No high-confidence signals found")
                    except Exception as e:
                        st.error(f"Error scanning signals: {e}")
        
        with col2:
            st.markdown("#### Auto-Trading Settings")
            
            # Settings form
            with st.form("auto_trading_settings"):
                new_min_confidence = st.slider(
                    "Minimum Confidence Threshold (%)",
                    min_value=50,
                    max_value=100,
                    value=int(status['min_confidence_threshold']),
                    step=5,
                    help="Only trade signals with this confidence or higher"
                )
                
                new_position_size = st.number_input(
                    "Default Position Size ($)",
                    min_value=100,
                    max_value=2000,
                    value=int(status['default_position_size']),
                    step=100,
                    help="Default USD amount per auto-trade"
                )
                
                new_max_positions = st.number_input(
                    "Maximum Positions",
                    min_value=1,
                    max_value=20,
                    value=status['max_positions'],
                    step=1,
                    help="Maximum number of open positions"
                )
                
                new_cooldown = st.number_input(
                    "Cooldown Period (seconds)",
                    min_value=60,
                    max_value=3600,
                    value=status['cooldown_period'],
                    step=60,
                    help="Minimum time between trades for same symbol"
                )
                
                if st.form_submit_button("Update Settings"):
                    auto_engine.update_settings(
                        min_confidence_threshold=new_min_confidence,
                        default_position_size=new_position_size,
                        max_positions=new_max_positions,
                        cooldown_period=new_cooldown
                    )
                    st.success("Settings updated!")
                    st.rerun()
            
            st.markdown("#### System Information")
            st.write(f"**Monitoring Thread:** {'Active' if status['monitoring_active'] else 'Inactive'}")
            st.write(f"**Processed Alerts:** {status['processed_alerts_count']}")
            st.write(f"**Cooldown Period:** {status['cooldown_period']} seconds")
        
        # Recent auto-trading activity
        st.markdown("---")
        st.markdown("#### Auto-Trading Activity")
        
        if portfolio.trade_history:
            # Filter for recent trades (last 10)
            recent_auto_trades = portfolio.trade_history[-10:]
            
            if recent_auto_trades:
                st.markdown("**Recent Automated Trades:**")
                
                for trade in reversed(recent_auto_trades):  # Show newest first
                    timestamp = datetime.fromisoformat(trade['timestamp'])
                    time_str = timestamp.strftime("%H:%M:%S")
                    
                    if trade['side'] == 'BUY':
                        st.write(f"🟢 {time_str} - BUY {trade['symbol']} - ${trade['total_value']:,.2f}")
                    else:
                        pnl = trade.get('pnl', 0)
                        pnl_color = "🟢" if pnl > 0 else "🔴"
                        st.write(f"{pnl_color} {time_str} - SELL {trade['symbol']} - P&L: ${pnl:+,.2f}")
            else:
                st.info("No automated trades executed yet")
        else:
            st.info("No trading activity yet")

def main():
    """Main dashboard application"""
    
    # Page header
    st.title("🎯 Crypto Sniper Dashboard")
    st.markdown("Real-time Solana token analysis with intelligent alerts")
    
    # Display alert sidebar
    display_alert_sidebar()
    
    # Check for new alerts
    check_for_new_alerts()
    
    # Display alert banner if there are active alerts
    display_alert_banner()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Token Analysis", "Portfolio", "Alert Analytics", "Data Export", "ML Training", "Paper Trading"])
    
    with tab1:
        display_token_analysis()
    
    with tab2:
        display_portfolio_tracker()
    
    with tab3:
        display_alert_analytics()
    
    with tab4:
        display_export_management()
    
    with tab5:
        display_ml_training()
    
    with tab6:
        display_paper_trading()
    
    # Auto-refresh controls
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Refresh Data"):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
    with col3:
        st.markdown(f"*Last updated: {datetime.now().strftime('%H:%M:%S')}*")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()