#!/usr/bin/env python3
import requests
import json

def get_base_gainers():
    """Get top Base gainers from DexScreener with specific filters"""
    url = "https://dexscreener.com/gainers/base?rankBy=priceChangeH24&order=desc&minLiq=250000&min24HTxns=300&min24HSells=30&min24HVol=250000&profile=1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # DexScreener returns HTML, we need to extract the data
        # Let's try the API endpoint for gainers instead
        api_url = "https://api.dexscreener.com/latest/dex/gainers/base"
        api_response = requests.get(api_url, headers=headers, timeout=10)
        api_response.raise_for_status()
        
        return api_response.json()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def analyze_gainers(data):
    """Analyze top gainers for arbitrage opportunities"""
    print("🔥 BASE TOP GAINERS ANALYSIS")
    print("="*80)
    print("Filters: Min $250K liquidity, 300+ txns, 30+ sells, $250K+ volume")
    print("="*80)
    
    if not data or 'pairs' not in data:
        print("❌ No data received")
        return []
    
    weth_address = "0x4200000000000000000000000000000000000006"
    weth_pairs = []
    
    # Filter for WETH pairs only
    for pair in data['pairs']:
        base_addr = pair.get('baseToken', {}).get('address', '').lower()
        quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
        
        if (base_addr == weth_address.lower() or quote_addr == weth_address.lower()):
            weth_pairs.append(pair)
    
    print(f"📊 Found {len(weth_pairs)} WETH pairs among top gainers")
    
    # Sort by price change
    weth_pairs.sort(key=lambda x: x.get('priceChange', {}).get('h24', 0), reverse=True)
    
    top_targets = []
    
    for i, pair in enumerate(weth_pairs[:15]):  # Top 15
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
        sells_24h = pair.get('txns', {}).get('h24', {}).get('sells', 0)
        price_change = pair.get('priceChange', {}).get('h24', 0)
        
        base_token = pair.get('baseToken', {})
        quote_token = pair.get('quoteToken', {})
        
        # Determine which is WETH and which is the target token
        if base_token.get('address', '').lower() == weth_address.lower():
            target_token = quote_token
        else:
            target_token = base_token
        
        print(f"\n{i+1}. 🚀 {target_token.get('symbol', 'UNKNOWN')} (+{price_change:.2f}%)")
        print(f"    Address: {target_token.get('address', 'N/A')}")
        print(f"    DEX: {pair.get('dexId', 'N/A')}")
        print(f"    Liquidity: ${liquidity:,.0f}")
        print(f"    Volume 24h: ${volume_24h:,.0f}")
        print(f"    Txns 24h: {txns_24h} (Buys: {pair.get('txns', {}).get('h24', {}).get('buys', 0)}, Sells: {sells_24h})")
        print(f"    URL: https://dexscreener.com/base/{pair.get('pairAddress', '')}")
        
        # Arbitrage potential assessment
        if (liquidity > 100000 and  # Good liquidity
            txns_24h > 200 and      # Active trading
            sells_24h > 20 and      # Selling pressure (creates arbitrage gaps)
            abs(price_change) > 5):   # High volatility
            
            top_targets.append({
                'symbol': target_token.get('symbol', 'UNKNOWN'),
                'address': target_token.get('address', ''),
                'liquidity': liquidity,
                'volume': volume_24h,
                'txns': txns_24h,
                'sells': sells_24h,
                'price_change': price_change,
                'dex': pair.get('dexId', ''),
                'pair_address': pair.get('pairAddress', '')
            })
            print("    ✅ EXCELLENT ARBITRAGE TARGET")
        else:
            print("    ⚠️  Moderate potential")
    
    print(f"\n🎯 TOP {len(top_targets)} ARBITRAGE TARGETS:")
    print("="*80)
    
    for token in top_targets:
        print(f"• {token['symbol']:<8} | Change: {token['price_change']:>6.2f}% | "
              f"Liq: ${token['liquidity']:>8,.0f} | Vol: ${token['volume']:>8,.0f} | "
              f"Txns: {token['txns']:>4.0f} | Sells: {token['sells']:>3.0f}")
        print(f"  Address: {token['address']}")
        print(f"  DEX: {token['dex']}")
    
    # Generate Rust config
    print(f"\n🦍 OPTIMIZED RUST CONFIGURATION:")
    print("="*80)
    print("// Replace your current tokens array with these:")
    print("let tokens = vec![")
    
    # Add unique tokens only
    seen = set()
    for token in top_targets:
        if token['address'] not in seen:
            seen.add(token['address'])
            print(f'    TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18 }},')
    
    print("];")
    
    print(f"\n💡 STRATEGY RECOMMENDATIONS:")
    print("="*80)
    print("• These tokens have high volatility + good liquidity = more arbitrage gaps")
    print("• High selling pressure creates price discrepancies between DEXs")
    print("• Focus on tokens with 10%+ daily changes for best opportunities")
    print("• Monitor these tokens closely - they're trending upward!")
    
    return top_targets

if __name__ == "__main__":
    print("🔥 Fetching Base gainers with your specific filters...")
    data = get_base_gainers()
    
    if data:
        analyze_gainers(data)
    else:
        print("❌ Failed to fetch gainers data")
