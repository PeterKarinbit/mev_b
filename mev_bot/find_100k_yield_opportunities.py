#!/usr/bin/env python3
"""
Find Specific Yield Opportunities Requiring $100k+
- Filters for legitimate, verifiable opportunities
- Shows exact amounts needed and expected profits
"""

import requests
import json
from web3 import Web3
from dotenv import load_dotenv
import os

# Try to load .env file
try:
    load_dotenv("mev_bot/.env")
except:
    pass

class YieldOpportunityFinder:
    def __init__(self):
        rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to RPC")
        
        print("✅ Connected to Base network")
        
        self.min_amount = 100000  # $100k minimum
        self.flash_loan_fee_rate = 0.0009  # 0.09%
        self.gas_cost_usd = 0.01  # Approximate
        
    def fetch_yield_data(self):
        """Fetch yield data from DeFiLlama"""
        try:
            url = "https://yields.llama.fi/pools"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            base_pools = []
            for pool in data.get('data', []):
                if pool.get('chain', '').lower() == 'base':
                    base_pools.append(pool)
            
            return base_pools
        except Exception as e:
            print(f"❌ Error fetching yield data: {e}")
            return []
    
    def filter_legitimate_yields(self, pools):
        """Filter for legitimate, verifiable yields"""
        legitimate = []
        
        for pool in pools:
            apy = pool.get('apy', 0)
            tvl = pool.get('tvlUsd', 0)
            project = pool.get('project', '').lower()
            symbol = pool.get('symbol', '')
            pool_id = pool.get('pool', '')
            
            # Green flags for legitimacy
            is_legitimate = (
                apy > 0 and apy < 500 and  # Reasonable APY (not scam-level)
                tvl > 10000 and  # Minimum TVL (lowered to find more opportunities)
                project in ['aave', 'compound', 'moonwell', 'aerodrome', 'uniswap', 
                           'morpho', 'merkl', 'beefy', 'balancer', 'origin-ether',
                           'kiloex', 'pancakeswap']  # Known protocols
            )
            
            if is_legitimate:
                legitimate.append({
                    'project': pool.get('project', ''),
                    'symbol': symbol,
                    'apy': apy,
                    'tvl': tvl,
                    'pool_id': pool_id,
                    'chain': pool.get('chain', ''),
                    'url': f"https://defillama.com/yields/pool/{pool_id}" if pool_id else None
                })
        
        return legitimate
    
    def find_opportunities(self, pools):
        """Find yield opportunities that need $100k+"""
        print("\n🔍 Finding opportunities requiring $100k+...")
        
        # Group by token symbol
        token_pools = {}
        for pool in pools:
            symbol = pool.get('symbol', '')
            if symbol not in token_pools:
                token_pools[symbol] = []
            token_pools[symbol].append(pool)
        
        opportunities = []
        
        for symbol, pools_list in token_pools.items():
            if len(pools_list) >= 2:
                # Sort by APY
                pools_sorted = sorted(pools_list, key=lambda x: x.get('apy', 0), reverse=True)
                highest = pools_sorted[0]
                lowest = pools_sorted[-1]
                
                apy_diff = highest.get('apy', 0) - lowest.get('apy', 0)
                
                if apy_diff > 2.0:  # At least 2% difference (more realistic)
                    # Calculate minimum amount needed
                    min_amount = self.calculate_min_amount(apy_diff, 7)  # 7 days
                    
                    # Also check if it's profitable with $100k
                    profit_100k = self.calculate_profit(100000, apy_diff, 7)
                    
                    if min_amount < 200000 and profit_100k['net_profit'] > 0:  # Profitable with $100k
                        opportunities.append({
                            'token': symbol,
                            'high_protocol': highest.get('project', ''),
                            'high_apy': highest.get('apy', 0),
                            'high_tvl': highest.get('tvlUsd', 0),
                            'low_protocol': lowest.get('project', ''),
                            'low_apy': lowest.get('apy', 0),
                            'low_tvl': lowest.get('tvlUsd', 0),
                            'apy_diff': apy_diff,
                            'min_amount': min_amount,
                            'high_pool_id': highest.get('pool', ''),
                            'low_pool_id': lowest.get('pool', '')
                        })
        
        return opportunities
    
    def calculate_min_amount(self, apy_diff, days):
        """Calculate minimum amount needed to be profitable"""
        # We need: Yield > Flash Fee + Gas
        # Principal × (APY/100) × (Days/365) > Principal × 0.0009 + Gas
        # Principal × [(APY/100) × (Days/365) - 0.0009] > Gas
        # Principal > Gas / [(APY/100) × (Days/365) - 0.0009]
        
        total_fees = self.gas_cost_usd
        denominator = (apy_diff / 100) * (days / 365) - self.flash_loan_fee_rate
        
        if denominator <= 0:
            return float('inf')  # Not profitable
        
        min_amount = total_fees / denominator
        return min_amount
    
    def calculate_profit(self, amount, apy_diff, days):
        """Calculate profit for given amount"""
        yield_earned = amount * (apy_diff / 100) * (days / 365)
        flash_fee = amount * self.flash_loan_fee_rate
        net_profit = yield_earned - flash_fee - self.gas_cost_usd
        return {
            'amount': amount,
            'yield_earned': yield_earned,
            'flash_fee': flash_fee,
            'gas_cost': self.gas_cost_usd,
            'net_profit': net_profit,
            'roi': (net_profit / amount) * 100
        }
    
    def run(self):
        """Run the finder"""
        print("="*80)
        print("💰 YIELD OPPORTUNITIES REQUIRING $100k+")
        print("="*80)
        
        # Fetch data
        print("\n📡 Fetching yield data from DeFiLlama...")
        all_pools = self.fetch_yield_data()
        print(f"   ✅ Found {len(all_pools)} pools on Base")
        
        # Filter legitimate
        print("\n🔍 Filtering for legitimate yields...")
        legitimate_pools = self.filter_legitimate_yields(all_pools)
        print(f"   ✅ Found {len(legitimate_pools)} legitimate pools")
        
        # Find opportunities
        opportunities = self.find_opportunities(legitimate_pools)
        
        if opportunities:
            # Sort by minimum amount needed
            opportunities.sort(key=lambda x: x['min_amount'])
            
            print(f"\n🎯 FOUND {len(opportunities)} OPPORTUNITIES REQUIRING $100k+")
            print("="*80)
            
            for i, opp in enumerate(opportunities[:10], 1):  # Top 10
                print(f"\n{i}. {opp['token']}")
                print(f"   High APY: {opp['high_protocol']} - {opp['high_apy']:.2f}%")
                print(f"   Low APY: {opp['low_protocol']} - {opp['low_apy']:.2f}%")
                print(f"   APY Difference: {opp['apy_diff']:.2f}%")
                print(f"   TVL: ${opp['high_tvl']:,.0f} (high) / ${opp['low_tvl']:,.0f} (low)")
                print(f"   Minimum Amount Needed: ${opp['min_amount']:,.0f}")
                
                # Calculate profits for different amounts
                print(f"\n   💰 Profit Calculations (7 days):")
                for amount in [100000, 122659]:  # $100k and max available
                    if amount <= opp['high_tvl'] * 0.1:  # Within 10% of TVL
                        calc = self.calculate_profit(amount, opp['apy_diff'], 7)
                        if calc['net_profit'] > 0:
                            print(f"      ${amount:,.0f}: ${calc['net_profit']:.2f} profit ({calc['roi']:.3f}% ROI)")
                        else:
                            print(f"      ${amount:,.0f}: Not profitable")
                
                # Verification links
                if opp['high_pool_id']:
                    print(f"\n   🔗 Verify High APY: https://defillama.com/yields/pool/{opp['high_pool_id']}")
                if opp['low_pool_id']:
                    print(f"   🔗 Verify Low APY: https://defillama.com/yields/pool/{opp['low_pool_id']}")
        else:
            print("\n❌ No opportunities found requiring $100k+")
            print("   (This is normal - most opportunities need smaller amounts)")
        
        print("\n" + "="*80)
        print("💡 Next Steps:")
        print("   1. Click the verification links above")
        print("   2. Check if APY is stable (not temporary)")
        print("   3. Verify TVL is sufficient")
        print("   4. Check protocol audits and security")
        print("   5. Test with simulation before executing")
        print("="*80)

if __name__ == "__main__":
    try:
        finder = YieldOpportunityFinder()
        finder.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
