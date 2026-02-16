#!/usr/bin/env python3
import requests
import json

def get_base_weth_pairs():
    """Get Base chain WETH pairs specifically"""
    url = "https://api.dexscreener.com/latest/dex/search?q=0x4200000000000000000000000000000000000006"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        base_pairs = []
        if 'pairs' in data:
            for pair in data['pairs']:
                if pair.get('chainId') == 'base':
                    base_pairs.append(pair)
        
        return base_pairs
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def analyze_base_tokens(pairs):
    """Analyze Base tokens for arbitrage opportunities"""
    print("🔍 BASE CHAIN WETH PAIRS ANALYSIS")
    print("="*60)
    
    high_potential = []
    
    for i, pair in enumerate(pairs):
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
        
        base_token = pair.get('baseToken', {})
        quote_token = pair.get('quoteToken', {})
        
        # Determine which is WETH and which is the target token
        if base_token.get('address', '').lower() == '0x4200000000000000000000000000000000000006':
            target_token = quote_token
        else:
            target_token = base_token
        
        print(f"\n{i+1}. {target_token.get('symbol', 'UNKNOWN')}")
        print(f"   Address: {target_token.get('address', 'N/A')}")
        print(f"   DEX: {pair.get('dexId', 'N/A')}")
        print(f"   Liquidity: ${liquidity:,.0f}")
        print(f"   Volume 24h: ${volume_24h:,.0f}")
        print(f"   Txns 24h: {txns_24h}")
        print(f"   Price Change 24h: {pair.get('priceChange', {}).get('h24', 0):.2f}%")
        
        # Check if it's a good arbitrage target
        if (liquidity > 5000 and  # Min $5k liquidity
            volume_24h > 500 and   # Min $500 daily volume
            txns_24h < 1500):     # Lower competition
            high_potential.append({
                'symbol': target_token.get('symbol', 'UNKNOWN'),
                'address': target_token.get('address', ''),
                'liquidity': liquidity,
                'volume': volume_24h,
                'txns': txns_24h,
                'dex': pair.get('dexId', ''),
                'price_change': pair.get('priceChange', {}).get('h24', 0)
            })
            print("   ✅ GOOD ARBITRAGE TARGET")
        else:
            print("   ❌ Not suitable")
    
    print(f"\n🎯 FOUND {len(high_potential)} HIGH-POTENTIAL TARGETS:")
    print("="*60)
    
    for token in high_potential:
        print(f"• {token['symbol']:<8} | Liquidity: ${token['liquidity']:>8,.0f} | "
              f"Volume: ${token['volume']:>6,.0f} | Txns: {token['txns']:>4.0f} | "
              f"24h: {token['price_change']:>6.2f}%")
        print(f"  Address: {token['address']}")
    
    # Generate Rust config
    print(f"\n🦍 RUST CONFIGURATION:")
    print("="*60)
    print("// Add to your main.rs tokens array:")
    for token in high_potential:
        print(f'TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18 }},')
    
    return high_potential

if __name__ == "__main__":
    pairs = get_base_weth_pairs()
    print(f"📊 Found {len(pairs)} Base chain WETH pairs")
    
    if pairs:
        analyze_base_tokens(pairs)
    else:
        print("❌ No Base pairs found")
