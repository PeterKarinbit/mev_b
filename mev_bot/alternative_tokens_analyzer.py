#!/usr/bin/env python3
import requests
import json

def get_base_alternative_tokens():
    """Get Base chain tokens with good liquidity but lower competition"""
    # Search for popular Base tokens that aren't USDC
    search_terms = [
        "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",  # VIRTUAL
        "0x9401813063411C64a1C02154D495638C4C34a210",  # AERO  
        "0x532f27101965dd1a3c95fef19C0693A8B59E5046",  # BRETT
        "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",  # DEGEN
        "0xAC1Bd2486aAf3b5C0df3625023906C7f8673329D",  # TOSHI
        "0xF6e9327233E388ea287BCA9eFe5498858A996D74",  # MOCHI
        "0x057871A2051447713F5670258BDAd05d9Ad7Caa1",  # HIGHER
        "BASE",  # Search for BASE token
        "SYN",   # Search for SYN token
        "KOTO"   # Search for KOTO token
    ]
    
    all_pairs = []
    
    for term in search_terms:
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={term}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'pairs' in data:
                for pair in data['pairs']:
                    if pair.get('chainId') == 'base':
                        all_pairs.append(pair)
                        
        except Exception as e:
            print(f"❌ Error searching {term}: {e}")
            continue
    
    return all_pairs

def analyze_alternative_tokens(pairs):
    """Analyze alternative tokens for arbitrage opportunities"""
    print("🔍 BASE ALTERNATIVE TOKENS ANALYSIS")
    print("="*70)
    
    # Remove duplicates and filter for WETH pairs
    seen_addresses = set()
    weth_address = "0x4200000000000000000000000000000000000006"
    weth_pairs = []
    
    for pair in pairs:
        base_addr = pair.get('baseToken', {}).get('address', '').lower()
        quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
        
        # Check if it's a WETH pair and not a duplicate
        if (base_addr == weth_address.lower() or quote_addr == weth_address.lower()):
            pair_addr = pair.get('pairAddress', '')
            if pair_addr not in seen_addresses:
                seen_addresses.add(pair_addr)
                weth_pairs.append(pair)
    
    print(f"📊 Found {len(weth_pairs)} unique WETH pairs")
    
    high_potential = []
    
    for i, pair in enumerate(weth_pairs):
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
        
        base_token = pair.get('baseToken', {})
        quote_token = pair.get('quoteToken', {})
        
        # Determine which is WETH and which is the target token
        if base_token.get('address', '').lower() == weth_address.lower():
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
        
        # Check if it's a good arbitrage target (more lenient criteria)
        if (liquidity > 2000 and  # Min $2k liquidity
            volume_24h > 200 and   # Min $200 daily volume
            txns_24h < 3000):     # Lower competition threshold
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
    print("="*70)
    
    for token in high_potential:
        print(f"• {token['symbol']:<8} | Liquidity: ${token['liquidity']:>8,.0f} | "
              f"Volume: ${token['volume']:>6,.0f} | Txns: {token['txns']:>4.0f} | "
              f"24h: {token['price_change']:>6.2f}%")
        print(f"  Address: {token['address']}")
    
    # Generate Rust config
    print(f"\n🦍 RUST CONFIGURATION:")
    print("="*70)
    print("// Add to your main.rs tokens array:")
    for token in high_potential:
        print(f'TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18 }},')
    
    return high_potential

if __name__ == "__main__":
    pairs = get_base_alternative_tokens()
    
    if pairs:
        analyze_alternative_tokens(pairs)
    else:
        print("❌ No pairs found")
