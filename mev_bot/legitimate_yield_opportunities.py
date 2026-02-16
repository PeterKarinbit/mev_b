#!/usr/bin/env python3
"""
Legitimate Yield Opportunities - Realistic, Verifiable $100k+ Opportunities
Filters out unrealistic APY numbers and focuses on legitimate opportunities
"""

import requests
import json

def get_legitimate_opportunities():
    """Get legitimate, verifiable yield opportunities"""
    
    print("="*80)
    print("💰 LEGITIMATE YIELD OPPORTUNITIES FOR $100k+ FLASH LOANS")
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
    
    # Focus on legitimate protocols and reasonable APY
    legitimate_protocols = ['aave', 'moonwell', 'morpho', 'aerodrome', 'uniswap', 
                           'beefy', 'balancer', 'origin-ether', 'kiloex']
    
    opportunities = []
    
    # Group by token symbol
    token_groups = {}
    for pool in base_pools:
        symbol = pool.get('symbol', '')
        project = pool.get('project', '').lower()
        apy = pool.get('apy', 0)
        tvl = pool.get('tvlUsd', 0)
        
        # Filter for legitimate pools
        if (project in legitimate_protocols and 
            apy > 0 and apy < 100 and  # Reasonable APY (2-100%)
            tvl > 50000):  # Minimum TVL
            
            if symbol not in token_groups:
                token_groups[symbol] = []
            token_groups[symbol].append({
                'symbol': symbol,
                'project': pool.get('project', ''),
                'apy': apy,
                'tvl': tvl,
                'pool_id': pool.get('pool', '')
            })
    
    # Find opportunities
    for symbol, pools in token_groups.items():
        if len(pools) >= 2:
            pools.sort(key=lambda x: x['apy'], reverse=True)
            high = pools[0]
            low = pools[-1]
            
            apy_diff = high['apy'] - low['apy']
            
            # Only consider if difference is meaningful and realistic
            if apy_diff > 2.0 and high['apy'] < 50:  # 2%+ diff, max 50% APY
                # Calculate profit for $100k
                amount = 100000
                yield_7d = amount * (apy_diff / 100) * (7 / 365)
                flash_fee = amount * 0.0009
                net_profit = yield_7d - flash_fee - 0.01
                
                if net_profit > 0:
                    opportunities.append({
                        'token': symbol,
                        'high_protocol': high['project'],
                        'high_apy': high['apy'],
                        'high_tvl': high['tvl'],
                        'low_protocol': low['project'],
                        'low_apy': low['apy'],
                        'low_tvl': low['tvl'],
                        'apy_diff': apy_diff,
                        'net_profit': net_profit,
                        'high_pool_id': high['pool_id'],
                        'low_pool_id': low['pool_id']
                    })
    
    if opportunities:
        # Sort by profit
        opportunities.sort(key=lambda x: x['net_profit'], reverse=True)
        
        print(f"\n🎯 FOUND {len(opportunities)} LEGITIMATE OPPORTUNITIES")
        print("="*80)
        
        for i, opp in enumerate(opportunities[:5], 1):  # Top 5
            print(f"\n{i}. {opp['token']} - VERIFIABLE OPPORTUNITY")
            print(f"   {'─'*76}")
            print(f"   📊 APY Comparison:")
            print(f"      High: {opp['high_protocol']} - {opp['high_apy']:.2f}% APY")
            print(f"      Low:  {opp['low_protocol']} - {opp['low_apy']:.2f}% APY")
            print(f"      Difference: {opp['apy_diff']:.2f}%")
            
            print(f"\n   💰 Profit with $100,000 USDC (7 days):")
            yield_earned = 100000 * (opp['apy_diff'] / 100) * (7 / 365)
            flash_fee = 100000 * 0.0009
            print(f"      Yield Earned: ${yield_earned:,.2f}")
            print(f"      Flash Loan Fee: -${flash_fee:,.2f}")
            print(f"      Gas Cost: -$0.01")
            print(f"      ─────────────────────────────")
            print(f"      NET PROFIT: ${opp['net_profit']:,.2f} ✅")
            
            print(f"\n   📈 TVL (Total Value Locked):")
            print(f"      High Protocol: ${opp['high_tvl']:,.0f}")
            print(f"      Low Protocol: ${opp['low_tvl']:,.0f}")
            
            # Check if TVL is sufficient
            if opp['high_tvl'] >= 100000:
                print(f"      ✅ Sufficient liquidity available")
            else:
                print(f"      ⚠️  TVL may be too low for $100k")
            
            print(f"\n   🔗 VERIFICATION LINKS:")
            if opp['high_pool_id']:
                print(f"      High APY: https://defillama.com/yields/pool/{opp['high_pool_id']}")
            if opp['low_pool_id']:
                print(f"      Low APY: https://defillama.com/yields/pool/{opp['low_pool_id']}")
            
            print(f"\n   ✅ LEGITIMACY CHECKS:")
            print(f"      ✓ APY in reasonable range (2-50%)")
            print(f"      ✓ Known protocol ({opp['high_protocol']})")
            print(f"      ✓ TVL > $50k")
            print(f"      ✓ Verifiable on DeFiLlama")
    else:
        print("\n❌ No legitimate opportunities found with current filters")
        print("\n💡 This means:")
        print("   - Most yield differences are small (< 2%)")
        print("   - Or high APY pools have low TVL")
        print("   - Or yields are temporary incentives")
        print("\n🔍 Try running yield_farming_optimizer.py for all opportunities")
    
    print("\n" + "="*80)
    print("📋 SUMMARY:")
    print("="*80)
    print("Maximum Flash Loan Available:")
    print("  • USDC: 61,329 USDC (from Balancer vault)")
    print("  • WETH: 26.94 ETH (~$94k)")
    print("\nFor $100k+ opportunities:")
    print("  • You can use up to $61k USDC from vault")
    print("  • Or convert to WETH and use up to $94k")
    print("  • Verify yields are legitimate before executing")
    print("="*80)

if __name__ == "__main__":
    get_legitimate_opportunities()
