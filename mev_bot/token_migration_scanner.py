#!/usr/bin/env python3
"""
Token Migration Scanner
- Scans for token migrations, upgrades, and airdrop opportunities
- Uses flash loans to participate in migrations without holding tokens
"""

import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Optional

# Try to load .env file
try:
    load_dotenv("mev_bot/.env")
except:
    pass

class TokenMigrationScanner:
    def __init__(self):
        # Connect to Base network
        rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to RPC")
        
        print("✅ Connected to Base network")
        
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        
        # Base tokens
        self.USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        self.WETH = "0x4200000000000000000000000000000000000006"
        
        # Known migration patterns to watch
        self.migration_patterns = [
            "migration",
            "upgrade",
            "v2",
            "v3",
            "new",
            "migrate"
        ]
        
    def check_wallet_balance(self):
        """Check wallet ETH balance"""
        try:
            balance_wei = self.w3.eth.get_balance(self.bot_address)
            balance_eth = balance_wei / 10**18
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = gas_price / 10**9
            
            print(f"\n💰 Wallet Balance: {balance_eth:.8f} ETH")
            print(f"   Gas Price: {gas_price_gwei:.4f} gwei")
            return balance_eth > 0.00001
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def scan_dexscreener_for_migrations(self) -> List[Dict]:
        """Scan DexScreener for potential migration opportunities"""
        print("\n🔍 Scanning DexScreener for migration opportunities...")
        
        opportunities = []
        
        # Search for tokens with migration-related keywords
        search_terms = ["migration", "upgrade", "v2", "v3", "new token"]
        
        for term in search_terms:
            try:
                url = f"https://api.dexscreener.com/latest/dex/search?q={term}%20base"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                pairs = data.get('pairs', [])
                print(f"   ✅ Found {len(pairs)} pairs for '{term}'")
                
                for pair in pairs:
                    chain_id = pair.get('chainId', '').lower()
                    if chain_id != 'base':
                        continue
                    
                    base_token = pair.get('baseToken', {})
                    token_symbol = base_token.get('symbol', '')
                    token_address = base_token.get('address', '')
                    
                    # Check if token name suggests migration
                    symbol_lower = token_symbol.lower()
                    if any(pattern in symbol_lower for pattern in self.migration_patterns):
                        liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
                        volume_24h = pair.get('volume', {}).get('h24', 0)
                        
                        if liquidity_usd > 10000:  # Minimum liquidity
                            opportunities.append({
                                'symbol': token_symbol,
                                'address': token_address,
                                'liquidity_usd': liquidity_usd,
                                'volume_24h': volume_24h,
                                'price_usd': float(pair.get('priceUsd', 0)) if pair.get('priceUsd') else 0,
                                'dex_id': pair.get('dexId', ''),
                                'url': f"https://dexscreener.com/base/{pair.get('pairAddress', '')}",
                                'type': 'potential_migration'
                            })
                
            except Exception as e:
                print(f"   ❌ Error searching '{term}': {e}")
                continue
        
        return opportunities
    
    def check_token_contract(self, token_address: str) -> Dict:
        """Check token contract for migration functions"""
        try:
            # Standard ERC20 ABI
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
            ]
            
            token = self.w3.eth.contract(address=token_address, abi=erc20_abi)
            
            try:
                name = token.functions.name().call()
                symbol = token.functions.symbol().call()
                decimals = token.functions.decimals().call()
                total_supply = token.functions.totalSupply().call()
                
                return {
                    'name': name,
                    'symbol': symbol,
                    'decimals': decimals,
                    'total_supply': total_supply,
                    'has_migration_keywords': any(p in name.lower() or p in symbol.lower() for p in self.migration_patterns)
                }
            except:
                return {'error': 'Could not read contract'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def simulate_migration_flash_loan(self, old_token: str, new_token: str, amount: int) -> Dict:
        """Simulate flash loan for token migration"""
        print(f"\n🎯 Simulating migration flash loan...")
        print(f"   Old Token: {old_token}")
        print(f"   New Token: {new_token}")
        print(f"   Amount: {amount}")
        
        # This would interact with migration contract
        # For now, just simulate
        try:
            if not self.flash_loan_contract:
                return {'status': 'no_contract', 'message': 'Flash loan contract not configured'}
            
            # Calculate potential profit
            # Migration bonus typically 1-10%
            migration_bonus_rate = 0.05  # 5% bonus
            bonus_amount = amount * migration_bonus_rate
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            estimated_gas = 400000  # Migration typically uses less gas
            gas_cost = (gas_price * estimated_gas) / 10**18
            
            # Flash loan fee (0.09%)
            flash_loan_fee = amount * 0.0009
            
            net_profit = bonus_amount - flash_loan_fee - (gas_cost * 2500)  # Convert ETH to USD
            
            return {
                'status': 'success',
                'bonus_amount': bonus_amount,
                'flash_loan_fee': flash_loan_fee,
                'gas_cost_eth': gas_cost,
                'gas_cost_usd': gas_cost * 2500,
                'net_profit': net_profit,
                'profitable': net_profit > 0
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def run_scan(self):
        """Run migration scan"""
        print("="*80)
        print("🔄 TOKEN MIGRATION SCANNER")
        print("="*80)
        
        if not self.check_wallet_balance():
            print("❌ Insufficient balance")
            return
        
        # Scan for migration opportunities
        opportunities = self.scan_dexscreener_for_migrations()
        
        if opportunities:
            print(f"\n✅ Found {len(opportunities)} potential migration opportunities:")
            print("="*80)
            
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"\n{i}. {opp['symbol']}")
                print(f"   Address: {opp['address']}")
                print(f"   Liquidity: ${opp['liquidity_usd']:,.0f}")
                print(f"   Volume 24h: ${opp['volume_24h']:,.0f}")
                print(f"   DEX: {opp['dex_id']}")
                print(f"   URL: {opp['url']}")
                
                # Check contract
                contract_info = self.check_token_contract(opp['address'])
                if 'name' in contract_info:
                    print(f"   Contract: {contract_info['name']} ({contract_info['symbol']})")
                    if contract_info.get('has_migration_keywords'):
                        print(f"   ⚠️  Contains migration keywords!")
        else:
            print("\n❌ No migration opportunities found")
            print("   (Migrations are rare events)")
        
        print("\n" + "="*80)
        print("💡 Tips:")
        print("   - Monitor protocol announcements for migrations")
        print("   - Watch for token upgrade events")
        print("   - Check governance proposals for token changes")
        print("="*80)

if __name__ == "__main__":
    try:
        scanner = TokenMigrationScanner()
        scanner.run_scan()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
