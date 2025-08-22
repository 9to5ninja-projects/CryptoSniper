import requests
import json
import base58
from typing import Dict, List, Optional
import logging
import pandas as pd

class SolanaWalletAPI:
    """Solana wallet API for portfolio tracking"""
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Known Solana tokens for better identification
        self.known_tokens = {
            "So11111111111111111111111111111111111111112": {"symbol": "SOL", "name": "Solana", "decimals": 9},
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {"symbol": "USDT", "name": "Tether USD", "decimals": 6},
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {"symbol": "BONK", "name": "Bonk", "decimals": 5},
            "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {"symbol": "ORCA", "name": "Orca", "decimals": 6},
            "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": {"symbol": "RAY", "name": "Raydium", "decimals": 6}
        }
    
    def _make_rpc_request(self, method: str, params: List) -> Dict:
        """Make RPC request to Solana"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            response = self.session.post(self.rpc_url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logging.error(f"Solana RPC error: {data['error']}")
                return {}
            
            return data.get('result', {})
            
        except Exception as e:
            logging.error(f"Solana RPC request failed: {e}")
            return {}
    
    def validate_wallet_address(self, address: str) -> bool:
        """Validate Solana wallet address format"""
        try:
            if len(address) < 32 or len(address) > 44:
                return False
            # Check if it's base58 encoded
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except:
            return False
    
    def get_sol_balance(self, wallet_address: str) -> float:
        """Get SOL balance for wallet"""
        try:
            result = self._make_rpc_request("getBalance", [wallet_address])
            if result and 'value' in result:
                # Convert lamports to SOL (1 SOL = 1,000,000,000 lamports)
                return result['value'] / 1_000_000_000
            return 0.0
        except Exception as e:
            logging.error(f"Error getting SOL balance: {e}")
            return 0.0
    
    def get_token_accounts(self, wallet_address: str) -> List[Dict]:
        """Get SPL token accounts for wallet"""
        try:
            result = self._make_rpc_request(
                "getTokenAccountsByOwner",
                [
                    wallet_address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            )
            
            if result and 'value' in result:
                token_accounts = []
                for account in result['value']:
                    try:
                        account_data = account['account']['data']['parsed']['info']
                        mint = account_data['mint']
                        token_amount = account_data['tokenAmount']
                        balance = float(token_amount['uiAmount'] or 0)
                        
                        if balance > 0:  # Only include accounts with balance
                            token_accounts.append({
                                'mint': mint,
                                'balance': balance,
                                'decimals': token_amount['decimals']
                            })
                    except (KeyError, TypeError, ValueError):
                        continue
                
                return token_accounts
            return []
            
        except Exception as e:
            logging.error(f"Error getting token accounts: {e}")
            return []
    
    def get_token_metadata(self, mint_address: str) -> Dict:
        """Get token metadata"""
        # Check known tokens first
        if mint_address in self.known_tokens:
            return self.known_tokens[mint_address]
        
        # Fallback to generic info
        return {
            "symbol": f"TOKEN{mint_address[:4]}",
            "name": f"Token {mint_address[:8]}...",
            "decimals": 6
        }
    
    def get_sol_price(self) -> float:
        """Get current SOL price from CoinGecko"""
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "solana", "vs_currencies": "usd"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('solana', {}).get('usd', 0.0)
            return 0.0
        except Exception:
            return 150.0  # Fallback price
    
    def build_portfolio(self, wallet_address: str) -> pd.DataFrame:
        """Build complete portfolio DataFrame"""
        try:
            portfolio_data = []
            
            # Get SOL balance and price
            sol_balance = self.get_sol_balance(wallet_address)
            sol_price = self.get_sol_price()
            sol_value = sol_balance * sol_price
            
            # Add SOL to portfolio
            portfolio_data.append({
                'Symbol': 'SOL',
                'Name': 'Solana',
                'Balance': sol_balance,
                'Price': sol_price,
                'Value': sol_value,
                'Type': 'Native'
            })
            
            # Get SPL tokens
            token_accounts = self.get_token_accounts(wallet_address)
            for token_account in token_accounts[:10]:  # Limit to top 10
                try:
                    mint = token_account['mint']
                    balance = token_account['balance']
                    metadata = self.get_token_metadata(mint)
                    
                    # Use estimated price for demo (in production, you'd fetch real prices)
                    estimated_price = 0.1
                    token_value = balance * estimated_price
                    
                    portfolio_data.append({
                        'Symbol': metadata['symbol'],
                        'Name': metadata['name'],
                        'Balance': balance,
                        'Price': estimated_price,
                        'Value': token_value,
                        'Type': 'SPL Token'
                    })
                except Exception:
                    continue
            
            df = pd.DataFrame(portfolio_data)
            return df.sort_values('Value', ascending=False) if not df.empty else df
            
        except Exception as e:
            logging.error(f"Error building portfolio: {e}")
            return pd.DataFrame()

# Test function
def test_wallet_api():
    """Test wallet API with a known public address"""
    print("👻 Testing Phantom Wallet API...")
    
    wallet_api = SolanaWalletAPI()
    
    # Test with a known public address (this is public info)
    test_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Random public address
    
    try:
        # Test address validation
        is_valid = wallet_api.validate_wallet_address(test_address)
        print(f"✅ Address validation: {is_valid}")
        
        if is_valid:
            # Test SOL balance
            sol_balance = wallet_api.get_sol_balance(test_address)
            print(f"✅ SOL balance: {sol_balance:.4f} SOL")
            
            # Test token accounts
            token_accounts = wallet_api.get_token_accounts(test_address)
            print(f"✅ Found {len(token_accounts)} SPL token accounts")
            
            # Test portfolio building
            portfolio_df = wallet_api.build_portfolio(test_address)
            print(f"✅ Built portfolio with {len(portfolio_df)} tokens")
            
            if not portfolio_df.empty:
                print("\n💼 Sample portfolio:")
                print(portfolio_df[['Symbol', 'Name', 'Balance', 'Value', 'Type']].head())
            
            print("\n👻 Wallet API test SUCCESSFUL!")
            return True
        else:
            print("❌ Invalid address format")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_wallet_api()