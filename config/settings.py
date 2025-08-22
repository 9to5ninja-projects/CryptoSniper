#!/usr/bin/env python3
"""
Configuration settings for Crypto Sniper Dashboard
Includes alert configuration and system settings
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# =============================================================================
# ALERT CONFIGURATION
# =============================================================================

# Default alert settings
ALERTS = {
    'ENABLE_ALERTS': True,
    'STRONG_BUY_THRESHOLD': 80,
    'VOLATILITY_THRESHOLD': 15,
    'VOLUME_SPIKE_THRESHOLD': 200,
    'MAX_ALERTS_DISPLAY': 10,
    'ALERT_RETENTION_MINUTES': 60
}

# =============================================================================
# API CONFIGURATION
# =============================================================================

# CoinGecko API settings
COINGECKO = {
    'BASE_URL': 'https://api.coingecko.com/api/v3',
    'REQUEST_TIMEOUT': 30,
    'RATE_LIMIT_DELAY': 1.0
}

# Kraken API settings
KRAKEN = {
    'BASE_URL': 'https://api.kraken.com',
    'REQUEST_TIMEOUT': 30
}

# =============================================================================
# DASHBOARD CONFIGURATION
# =============================================================================

DASHBOARD = {
    'REFRESH_INTERVAL_SECONDS': 30,
    'MAX_TOKENS_DISPLAY': 50,
    'DEFAULT_TOKEN_LIMIT': 30
}

# =============================================================================
# DATA STORAGE CONFIGURATION
# =============================================================================

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = DATA_DIR / 'logs'
EXPORTS_DIR = DATA_DIR / 'exports'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Configuration file paths
CONFIG_FILE = DATA_DIR / 'alert_config.json'

# =============================================================================
# ENVIRONMENT VARIABLE OVERRIDES
# =============================================================================

def get_env_override(key: str, default: Any, value_type: type = str) -> Any:
    """Get environment variable with type conversion and default fallback"""
    env_value = os.getenv(key)
    if env_value is None:
        return default
    
    try:
        if value_type == bool:
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif value_type == int:
            return int(env_value)
        elif value_type == float:
            return float(env_value)
        else:
            return env_value
    except (ValueError, TypeError):
        return default

# Apply environment overrides to alert settings
ALERTS['ENABLE_ALERTS'] = get_env_override('CRYPTO_ENABLE_ALERTS', ALERTS['ENABLE_ALERTS'], bool)
ALERTS['STRONG_BUY_THRESHOLD'] = get_env_override('CRYPTO_STRONG_BUY_THRESHOLD', ALERTS['STRONG_BUY_THRESHOLD'], int)
ALERTS['VOLATILITY_THRESHOLD'] = get_env_override('CRYPTO_VOLATILITY_THRESHOLD', ALERTS['VOLATILITY_THRESHOLD'], int)
ALERTS['VOLUME_SPIKE_THRESHOLD'] = get_env_override('CRYPTO_VOLUME_SPIKE_THRESHOLD', ALERTS['VOLUME_SPIKE_THRESHOLD'], int)
ALERTS['MAX_ALERTS_DISPLAY'] = get_env_override('CRYPTO_MAX_ALERTS_DISPLAY', ALERTS['MAX_ALERTS_DISPLAY'], int)
ALERTS['ALERT_RETENTION_MINUTES'] = get_env_override('CRYPTO_ALERT_RETENTION_MINUTES', ALERTS['ALERT_RETENTION_MINUTES'], int)

# =============================================================================
# CONFIGURATION HELPER FUNCTIONS
# =============================================================================

def get_alert_config() -> Dict[str, Any]:
    """
    Get current alert configuration, merging defaults with saved settings
    
    Returns:
        Dict containing all alert configuration settings
    """
    config = ALERTS.copy()
    
    # Load saved configuration if it exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                config.update(saved_config.get('alerts', {}))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load saved config: {e}")
    
    return config

def update_alert_threshold(alert_type: str, new_value: float) -> bool:
    """
    Update a specific alert threshold value
    
    Args:
        alert_type: Type of alert threshold to update
                   ('STRONG_BUY', 'VOLATILITY', 'VOLUME_SPIKE')
        new_value: New threshold value
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    threshold_map = {
        'STRONG_BUY': 'STRONG_BUY_THRESHOLD',
        'VOLATILITY': 'VOLATILITY_THRESHOLD', 
        'VOLUME_SPIKE': 'VOLUME_SPIKE_THRESHOLD'
    }
    
    if alert_type not in threshold_map:
        print(f"Error: Unknown alert type '{alert_type}'")
        return False
    
    threshold_key = threshold_map[alert_type]
    
    # Validate new value
    if not isinstance(new_value, (int, float)) or new_value < 0:
        print(f"Error: Invalid threshold value '{new_value}'. Must be a positive number.")
        return False
    
    # Load current config
    current_config = load_full_config()
    
    # Update the specific threshold
    current_config['alerts'][threshold_key] = new_value
    
    # Save updated config
    return save_full_config(current_config)

def save_alert_settings(alert_config: Dict[str, Any]) -> bool:
    """
    Save alert settings to configuration file
    
    Args:
        alert_config: Dictionary containing alert configuration
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Load existing config or create new one
        full_config = load_full_config()
        
        # Update alert section
        full_config['alerts'] = alert_config
        
        # Save to file
        return save_full_config(full_config)
        
    except Exception as e:
        print(f"Error saving alert settings: {e}")
        return False

def load_full_config() -> Dict[str, Any]:
    """Load full configuration from file or return defaults"""
    default_config = {
        'alerts': get_alert_config(),
        'dashboard': DASHBOARD.copy(),
        'api': {
            'coingecko': COINGECKO.copy(),
            'kraken': KRAKEN.copy()
        }
    }
    
    if not CONFIG_FILE.exists():
        return default_config
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            saved_config = json.load(f)
            
        # Merge with defaults to ensure all keys exist
        for section, defaults in default_config.items():
            if section not in saved_config:
                saved_config[section] = defaults
            else:
                # Update missing keys in existing sections
                for key, value in defaults.items():
                    if key not in saved_config[section]:
                        saved_config[section][key] = value
        
        return saved_config
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load config file, using defaults: {e}")
        return default_config

def save_full_config(config: Dict[str, Any]) -> bool:
    """Save full configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving configuration: {e}")
        return False

def reset_alert_config() -> bool:
    """Reset alert configuration to defaults"""
    default_alerts = {
        'ENABLE_ALERTS': True,
        'STRONG_BUY_THRESHOLD': 80,
        'VOLATILITY_THRESHOLD': 15,
        'VOLUME_SPIKE_THRESHOLD': 200,
        'MAX_ALERTS_DISPLAY': 10,
        'ALERT_RETENTION_MINUTES': 60
    }
    
    return save_alert_settings(default_alerts)

def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration"""
    config = get_alert_config()
    
    return {
        'alert_settings': config,
        'config_file_exists': CONFIG_FILE.exists(),
        'config_file_path': str(CONFIG_FILE),
        'environment_overrides': {
            'CRYPTO_ENABLE_ALERTS': os.getenv('CRYPTO_ENABLE_ALERTS'),
            'CRYPTO_STRONG_BUY_THRESHOLD': os.getenv('CRYPTO_STRONG_BUY_THRESHOLD'),
            'CRYPTO_VOLATILITY_THRESHOLD': os.getenv('CRYPTO_VOLATILITY_THRESHOLD'),
            'CRYPTO_VOLUME_SPIKE_THRESHOLD': os.getenv('CRYPTO_VOLUME_SPIKE_THRESHOLD'),
            'CRYPTO_MAX_ALERTS_DISPLAY': os.getenv('CRYPTO_MAX_ALERTS_DISPLAY'),
            'CRYPTO_ALERT_RETENTION_MINUTES': os.getenv('CRYPTO_ALERT_RETENTION_MINUTES')
        }
    }

# =============================================================================
# TESTING AND VALIDATION
# =============================================================================

def validate_config() -> Dict[str, Any]:
    """Validate current configuration and return status"""
    config = get_alert_config()
    issues = []
    
    # Validate alert thresholds
    if config['STRONG_BUY_THRESHOLD'] < 0 or config['STRONG_BUY_THRESHOLD'] > 100:
        issues.append("STRONG_BUY_THRESHOLD must be between 0 and 100")
    
    if config['VOLATILITY_THRESHOLD'] < 0:
        issues.append("VOLATILITY_THRESHOLD must be positive")
    
    if config['VOLUME_SPIKE_THRESHOLD'] < 0:
        issues.append("VOLUME_SPIKE_THRESHOLD must be positive")
    
    if config['MAX_ALERTS_DISPLAY'] < 1:
        issues.append("MAX_ALERTS_DISPLAY must be at least 1")
    
    if config['ALERT_RETENTION_MINUTES'] < 1:
        issues.append("ALERT_RETENTION_MINUTES must be at least 1")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'config': config
    }

# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

if __name__ == "__main__":
    # Test configuration system
    print("🔧 Testing Configuration System...")
    print("=" * 50)
    
    # Test getting config
    config = get_alert_config()
    print(f"✅ Alert config loaded: {len(config)} settings")
    
    # Test validation
    validation = validate_config()
    if validation['valid']:
        print("✅ Configuration validation passed")
    else:
        print(f"❌ Configuration issues: {validation['issues']}")
    
    # Test config summary
    summary = get_config_summary()
    print(f"✅ Config summary generated")
    
    # Test threshold update
    if update_alert_threshold('STRONG_BUY', 85):
        print("✅ Threshold update test passed")
    else:
        print("❌ Threshold update test failed")
    
    print("\n📊 Current Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n🎉 Configuration system test complete!")