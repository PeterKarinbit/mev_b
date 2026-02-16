#!/usr/bin/env python3
"""
Yield Farming Optimizer
- Scans multiple protocols for yield opportunities
- Uses flash loans to optimize yield farming
- Compares APY across Aave, Compound, and other protocols
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

class YieldFarmingOptimizer:
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
        
        # Protocol addresses on Base
        self.protocols = {
            'aave_v3': {
                'pool': '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5',
                'name': 'Aave V3'
            },
            'moonwell': {
                'comptroller': '0xfBb21302264E2b10239d49931Cc71e687D037920',
                'name': 'Moonwell'
            }
        }
        
        # Minimum profitable amount (considering gas)
        self.min_profitable_amount = 100000 * 10**6  # 100k USDC minimum
        
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
    
    def get_aave_apy(self, token_address: str) -> Optional[float]:
        """Get APY from Aave V3"""
        try:
            # Aave V3 Pool ABI (simplified)
            pool_abi = [{
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getReserveData",
                "outputs": [{
                    "components": [
                        {"name": "currentLiquidityRate", "type": "uint128"},
                        {"name": "currentStableBorrowRate", "type": "uint128"},
                        {"name": "currentVariableBorrowRate", "type": "uint128"}
                    ],
                    "name": "",
                    "type": "tuple"
                }],
                "type": "function"
            }]
            
            pool = self.w3.eth.contract(
                address=self.protocols['aave_v3']['pool'],
                abi=pool_abi
            )
            
            reserve_data = pool.functions.getReserveData(token_address).call()
            liquidity_rate = reserve_data[0]  # Supply APY in ray (1e27)
            
            # Convert ray to APY percentage
            # APY = (liquidityRate / 1e27) * 100 * 365 * 24 * 3600
            apy = (liquidity_rate / 10**27) * 100 * 365 * 24 * 3600
            
            return apy
            
        except Exception as e:
            return None
    
    def get_moonwell_apy(self, token_address: str) -> Optional[float]:
        """Get APY from Moonwell"""
        try:
            # Moonwell Comptroller ABI (simplified)
            comptroller_abi = [{
                "inputs": [{"name": "cToken", "type": "address"}],
                "name": "supplyRatePerBlock",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }]
            
            comptroller = self.w3.eth.contract(
                address=self.protocols['moonwell']['comptroller'],
                abi=comptroller_abi
            )
            
            # Need to find cToken address first (simplified)
            # This would require additional calls to get cToken address
            # For now, return None as placeholder
            
            return None
            
        except Exception as e:
            return None
    
    def fetch_yield_data_from_api(self) -> Dict:
        """Fetch yield data from DeFiLlama or similar API"""
        try:
            # DeFiLlama API for Base chain yields
            url = "https://yields.llama.fi/pools"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            base_yields = []
            for pool in data.get('data', []):
                chain = pool.get('chain', '').lower()
                if chain == 'base':
                    base_yields.append({
                        'protocol': pool.get('project', ''),
                        'symbol': pool.get('symbol', ''),
                        'apy': pool.get('apy', 0),
                        'tvl': pool.get('tvlUsd', 0),
                        'pool': pool.get('pool', '')
                    })
            
            return {'base': base_yields}
            
        except Exception as e:
            print(f"   ❌ API Error: {e}")
            return {}
    
    def compare_yields(self) -> List[Dict]:
        """Compare yields across protocols"""
        print("\n🔍 Comparing yields across protocols...")
        
        opportunities = []
        
        # Fetch from API (more reliable)
        yield_data = self.fetch_yield_data_from_api()
        
        if yield_data.get('base'):
            print(f"   ✅ Found {len(yield_data['base'])} yield pools on Base")
            
            # Group by token symbol
            token_yields = {}
            for pool in yield_data['base']:
                symbol = pool['symbol']
                if symbol not in token_yields:
                    token_yields[symbol] = []
                token_yields[symbol].append(pool)
            
            # Find opportunities (same token, different APY)
            for symbol, pools in token_yields.items():
                if len(pools) >= 2:
                    # Sort by APY
                    pools_sorted = sorted(pools, key=lambda x: x['apy'], reverse=True)
                    highest = pools_sorted[0]
                    lowest = pools_sorted[-1]
                    
                    apy_diff = highest['apy'] - lowest['apy']
                    
                    if apy_diff > 1.0:  # At least 1% APY difference
                        opportunities.append({
                            'token': symbol,
                            'high_protocol': highest['protocol'],
                            'high_apy': highest['apy'],
                            'low_protocol': lowest['protocol'],
                            'low_apy': lowest['apy'],
                            'apy_diff': apy_diff,
                            'high_tvl': highest['tvl'],
                            'low_tvl': lowest['tvl']
                        })
        
        return opportunities
    
    def calculate_flash_loan_profit(self, amount_usdc: int, apy_diff: float, duration_days: int = 1) -> Dict:
        """Calculate profit from flash loan yield farming"""
        print(f"\n💰 Calculating profit for ${amount_usdc/10**6:,.0f} USDC...")
        
        # Annual yield difference
        annual_profit = (amount_usdc / 10**6) * (apy_diff / 100)
        
        # Profit for duration
        profit = annual_profit * (duration_days / 365)
        
        # Flash loan fee (0.09%)
        flash_loan_fee = (amount_usdc / 10**6) * 0.0009
        
        # Gas cost
        gas_price = self.w3.eth.gas_price
        estimated_gas = 500000  # Deposit + withdraw + flash loan
        gas_cost_eth = (gas_price * estimated_gas) / 10**18
        gas_cost_usd = gas_cost_eth * 2500  # Approximate ETH price
        
        # Net profit
        net_profit = profit - flash_loan_fee - gas_cost_usd
        
        return {
            'amount_usdc': amount_usdc / 10**6,
            'apy_diff': apy_diff,
            'duration_days': duration_days,
            'gross_profit': profit,
            'flash_loan_fee': flash_loan_fee,
            'gas_cost_usd': gas_cost_usd,
            'net_profit': net_profit,
            'profitable': net_profit > 0,
            'min_amount_needed': (gas_cost_usd + flash_loan_fee) * 365 / (apy_diff / 100) if apy_diff > 0 else 0
        }
    
    def run_scan(self):
        """Run yield farming scan"""
        print("="*80)
        print("🌾 YIELD FARMING OPTIMIZER")
        print("="*80)
        
        if not self.check_wallet_balance():
            print("❌ Insufficient balance")
            return
        
        # Compare yields
        opportunities = self.compare_yields()
        
        if opportunities:
            print(f"\n✅ Found {len(opportunities)} yield opportunities:")
            print("="*80)
            
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"\n{i}. {opp['token']}")
                print(f"   High APY: {opp['high_protocol']} - {opp['high_apy']:.2f}%")
                print(f"   Low APY: {opp['low_protocol']} - {opp['low_apy']:.2f}%")
                print(f"   Difference: {opp['apy_diff']:.2f}% APY")
                print(f"   TVL: ${opp['high_tvl']:,.0f} (high) / ${opp['low_tvl']:,.0f} (low)")
                
                # Calculate profit for different amounts
                for amount in [100000, 500000, 1000000]:  # 100k, 500k, 1M USDC
                    calc = self.calculate_flash_loan_profit(
                        amount * 10**6,
                        opp['apy_diff'],
                        duration_days=7  # 1 week
                    )
                    
                    if calc['profitable']:
                        print(f"\n   💰 With ${amount:,.0f} USDC for 7 days:")
                        print(f"      Gross profit: ${calc['gross_profit']:.2f}")
                        print(f"      Fees: ${calc['flash_loan_fee']:.2f} + ${calc['gas_cost_usd']:.2f} gas")
                        print(f"      Net profit: ${calc['net_profit']:.2f}")
                    else:
                        print(f"\n   ⚠️  ${amount:,.0f} USDC: Not profitable (need ${calc['min_amount_needed']:,.0f}+)")
        else:
            print("\n❌ No yield opportunities found")
            print("   (Yield differences are usually small)")
        
        print("\n" + "="*80)
        print("💡 Tips:")
        print("   - Yield farming requires large amounts to be profitable")
        print("   - Gas costs can eat into small profits")
        print("   - Consider longer durations for better returns")
        print("   - Monitor protocol changes and new launches")
        print("="*80)

if __name__ == "__main__":
    try:
        optimizer = YieldFarmingOptimizer()
        optimizer.run_scan()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
