#!/usr/bin/env python3
"""
Specific Yield Opportunities - Verifiable $100k+ Opportunities
Shows exact opportunities you can check and verify
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

def get_specific_opportunities():
    """Get specific, verifiable yield opportunities"""
    
    print("="*80)
    print("💰 SPECIFIC YIELD OPPORTUNITIES FOR $100k+ FLASH LOANS")
    print("="*80)
    
    # Fetch yield data
    try:
        url = "https://yields.llama.fi/pools"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        base_pools = [p for p in data.get('data', []) if p.get('chain', '').lower() == 'base']
        print(f"\n✅ Found {len(base_pools)} pools on Base")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Focus on specific tokens with multiple pools
    target_tokens = ['USDC', 'WETH', 'CBBTC', 'VIRTUAL']
    
    opportunities = []
    
    for token in target_tokens:
        token_pools = [p for p in base_pools if token in p.get('symbol', '')]
        
        if len(token_pools) >= 2:
            # Sort by APY
            token_pools.sort(key=lambda x: x.get('apy', 0), reverse=True)
            
            high_pool = token_pools[0]
            low_pool = token_pools[-1]
            
            high_apy = high_pool.get('apy', 0)
            low_apy = low_pool.get('apy', 0)
            apy_diff = high_apy - low_apy
            
            high_protocol = high_pool.get('project', '')
            low_protocol = low_pool.get('project', '')
            high_tvl = high_pool.get('tvlUsd', 0)
            low_tvl = low_pool.get('tvlUsd', 0)
            high_pool_id = high_pool.get('pool', '')
            low_pool_id = low_pool.get('pool', '')
            
            # Calculate profit for $100k and $122k (max available)
            flash_fee_rate = 0.0009
            gas_cost = 0.01
            
            for amount in [100000, 122659]:
                yield_7d = amount * (apy_diff / 100) * (7 / 365)
                flash_fee = amount * flash_fee_rate
                net_profit = yield_7d - flash_fee - gas_cost
                
                if net_profit > 0 and apy_diff > 2.0:  # At least 2% difference
                    opportunities.append({
                        'token': token,
                        'high_protocol': high_protocol,
                        'high_apy': high_apy,
                        'high_tvl': high_tvl,
                        'low_protocol': low_protocol,
                        'low_apy': low_apy,
                        'low_tvl': low_tvl,
                        'apy_diff': apy_diff,
                        'amount': amount,
                        'net_profit': net_profit,
                        'high_pool_id': high_pool_id,
                        'low_pool_id': low_pool_id
                    })
                    break  # Only add once per token
    
    if opportunities:
        print(f"\n🎯 FOUND {len(opportunities)} SPECIFIC OPPORTUNITIES")
        print("="*80)
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n{i}. {opp['token']} - VERIFIABLE OPPORTUNITY")
            print(f"   {'─'*76}")
            print(f"   📊 APY Comparison:")
            print(f"      High: {opp['high_protocol']} - {opp['high_apy']:.2f}% APY")
            print(f"      Low:  {opp['low_protocol']} - {opp['low_apy']:.2f}% APY")
            print(f"      Difference: {opp['apy_diff']:.2f}%")
            print(f"\n   💰 Profit with ${opp['amount']:,.0f} USDC (7 days):")
            yield_earned = opp['amount'] * (opp['apy_diff'] / 100) * (7 / 365)
            flash_fee = opp['amount'] * 0.0009
            print(f"      Yield Earned: ${yield_earned:,.2f}")
            print(f"      Flash Loan Fee: -${flash_fee:,.2f}")
            print(f"      Gas Cost: -$0.01")
            print(f"      ─────────────────────────────")
            print(f"      NET PROFIT: ${opp['net_profit']:,.2f} ✅")
            print(f"      ROI: {(opp['net_profit']/opp['amount']*100):.3f}%")
            
            print(f"\n   📈 TVL (Total Value Locked):")
            print(f"      High Protocol: ${opp['high_tvl']:,.0f}")
            print(f"      Low Protocol: ${opp['low_tvl']:,.0f}")
            
            print(f"\n   🔗 VERIFICATION LINKS:")
            if opp['high_pool_id']:
                print(f"      High APY Pool: https://defillama.com/yields/pool/{opp['high_pool_id']}")
            if opp['low_pool_id']:
                print(f"      Low APY Pool: https://defillama.com/yields/pool/{opp['low_pool_id']}")
            
            print(f"\n   ⚠️  IMPORTANT CHECKS:")
            print(f"      1. Verify APY is stable (not temporary incentives)")
            print(f"      2. Check TVL is sufficient (need ${opp['amount']:,.0f}+ available)")
            print(f"      3. Confirm protocol is audited and secure")
            print(f"      4. Test with simulation before executing")
    else:
        print("\n❌ No specific opportunities found")
        print("   (Most opportunities need smaller amounts or have smaller APY differences)")
    
    # Show top opportunities from yield optimizer
    print("\n" + "="*80)
    print("💡 ALTERNATIVE: Check Yield Farming Optimizer Results")
    print("="*80)
    print("Run: python3 mev_bot/yield_farming_optimizer.py")
    print("This will show all opportunities, including high APY ones")
    print("="*80)

if __name__ == "__main__":
    get_specific_opportunities()
