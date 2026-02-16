#!/usr/bin/env python3
import requests
import json
import time
from typing import List, Dict

def get_base_tokens_from_dexscreener():
    """Fetch high-liquidity tokens from Base chain via DexScreener API"""
    # Try multiple endpoints
    urls = [
        "https://api.dexscreener.com/latest/dex/tokens/base",
        "https://api.dexscreener.com/latest/dex/search?q=WETH",
        "https://api.dexscreener.com/latest/dex/pairs/base"
    ]
    
    for url in urls:
        try:
            print(f"🔄 Trying: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got data with {len(data.get('pairs', []))} pairs")
            return data
        except Exception as e:
            print(f"❌ API Error: {e}")
            continue
    
    return None

def analyze_token_liquidity(pairs_data: List[Dict]) -> List[Dict]:
    """Analyze and filter tokens by liquidity and competition metrics"""
    high_liquidity_tokens = []
    
    for pair in pairs_data:
        # More lenient filtering for initial analysis
        if not pair.get('liquidity'):
            continue
            
        # Extract key metrics
        liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
        
        # Lower thresholds to find more opportunities
        if (liquidity_usd > 10000 and  # Min $10k liquidity (lowered)
            volume_24h > 1000 and      # Min $1k daily volume (lowered)
            txns_24h < 2000):         # Less than 2000 daily txns (raised)
            
            token_info = {
                'symbol': pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                'address': pair.get('baseToken', {}).get('address', ''),
                'liquidity_usd': liquidity_usd,
                'volume_24h': volume_24h,
                'txns_24h': txns_24h,
                'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                'pair_address': pair.get('pairAddress', ''),
                'dex_id': pair.get('dexId', ''),
                'url': f"https://dexscreener.com/base/{pair.get('pairAddress', '')}"
            }
            high_liquidity_tokens.append(token_info)
    
    return sorted(high_liquidity_tokens, key=lambda x: x['liquidity_usd'], reverse=True)

def get_weth_pairs(tokens_data: Dict) -> List[Dict]:
    """Filter for WETH pairs specifically"""
    weth_pairs = []
    weth_address = "0x4200000000000000000000000000000000000006"
    
    if 'pairs' in tokens_data:
        for pair in tokens_data['pairs']:
            # Check if pair involves WETH
            quote_token = pair.get('quoteToken', {})
            base_token = pair.get('baseToken', {})
            
            if (quote_token.get('address', '').lower() == weth_address.lower() or
                base_token.get('address', '').lower() == weth_address.lower()):
                weth_pairs.append(pair)
    
    return weth_pairs

def format_output(tokens: List[Dict]) -> None:
    """Format and display the analysis results"""
    print("\n" + "="*80)
    print("🔍 BASE TOKENS WITH HIGH LIQUIDITY + LOW COMPETITION")
    print("="*80)
    print(f"Found {len(tokens)} potential arbitrage targets:")
    print()
    
    for i, token in enumerate(tokens[:20], 1):  # Top 20 tokens
        print(f"{i:2d}. {token['symbol']:<8} | Liquidity: ${token['liquidity_usd']:>10,.0f} | "
              f"Volume: ${token['volume_24h']:>8,.0f} | Txns: {token['txns_24h']:>4.0f} | "
              f"24h: {token['price_change_24h']:>6.2f}%")
        print(f"    Address: {token['address']}")
        print(f"    DEX: {token['dex_id']} | {token['url']}")
        print()

def generate_rust_config(tokens: List[Dict]) -> None:
    """Generate Rust token configuration for the MEV bot"""
    print("\n" + "="*80)
    print("🦍 RUST TOKEN CONFIGURATION")
    print("="*80)
    
    print("// Add these tokens to your main.rs:")
    print("let tokens = vec![")
    
    for token in tokens[:10]:  # Top 10 tokens
        print(f'    TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18 }},')
    
    print("];")

def main():
    print("🔍 Analyzing Base tokens for arbitrage opportunities...")
    print("Fetching data from DexScreener API...")
    
    # Get Base chain data
    data = get_base_tokens_from_dexscreener()
    if not data or not data.get('pairs'):
        print("❌ No data received from API")
        return
    
    # Filter for WETH pairs
    weth_pairs = get_weth_pairs(data)
    print(f"📊 Found {len(weth_pairs)} WETH pairs")
    
    # Analyze liquidity and competition
    high_liquidity_tokens = analyze_token_liquidity(weth_pairs)
    
    # Display results
    format_output(high_liquidity_tokens)
    
    # Generate Rust config
    generate_rust_config(high_liquidity_tokens)
    
    print(f"\n🎯 Analysis complete! Found {len(high_liquidity_tokens)} high-potential targets.")
    print("💡 These tokens have good liquidity but lower competition - perfect for MEV!")

if __name__ == "__main__":
    main()
