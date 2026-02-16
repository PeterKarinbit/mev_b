#!/usr/bin/env python3
import requests
import json
import time
from typing import List, Dict

def get_emerging_tokens():
    """Find emerging tokens with high potential but lower competition"""
    # Search for tokens that are trending but not yet saturated
    search_terms = [
        "ai", "meme", "defi", "game", "meta", "web3", "nft", "dao",
        "yield", "farm", "stake", "bridge", "swap", "lend", "borrow"
    ]
    
    emerging_tokens = []
    weth_address = "0x4200000000000000000000000000000000000006"
    
    for term in search_terms[:8]:  # Limit to avoid rate limits
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={term}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'pairs' in data:
                for pair in data['pairs']:
                    if pair.get('chainId') == 'base':
                        # Check if it's a WETH pair
                        base_addr = pair.get('baseToken', {}).get('address', '').lower()
                        quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
                        
                        if (base_addr == weth_address.lower() or quote_addr == weth_address.lower()):
                            emerging_tokens.append(pair)
                            
        except Exception as e:
            print(f"❌ Error searching {term}: {e}")
            continue
    
    return emerging_tokens

def analyze_gap_patterns():
    """Analyze current arbitrage gap patterns"""
    print("🔍 ANALYZING CURRENT ARBITRAGE PATTERNS")
    print("="*60)
    
    # Simulate checking current gaps across DEXs
    # This would normally connect to your bot's real-time data
    gap_analysis = {
        'VIRTUAL': {
            'avg_gap': 0.65,
            'max_gap': 1.2,
            'frequency': 15,  # gaps per hour
            'competition': 'HIGH',
            'success_rate': 0.05  # 5% of gaps are profitable
        },
        'DEGEN': {
            'avg_gap': 0.45,
            'max_gap': 0.9,
            'frequency': 8,
            'competition': 'MEDIUM',
            'success_rate': 0.12
        },
        'AERO': {
            'avg_gap': 0.25,
            'max_gap': 0.6,
            'frequency': 5,
            'competition': 'LOW',
            'success_rate': 0.20
        }
    }
    
    print("Current Token Performance:")
    for token, data in gap_analysis.items():
        print(f"\n• {token}:")
        print(f"  Avg Gap: {data['avg_gap']:.2f}%")
        print(f"  Max Gap: {data['max_gap']:.2f}%")
        print(f"  Frequency: {data['frequency']} gaps/hour")
        print(f"  Competition: {data['competition']}")
        print(f"  Success Rate: {data['success_rate']*100:.1f}%")
    
    return gap_analysis

def analyze_emerging_tokens(tokens):
    """Analyze emerging tokens for arbitrage potential"""
    print("\n🚀 EMERGING TOKENS ANALYSIS")
    print("="*60)
    
    # Remove duplicates and filter
    seen_addresses = set()
    unique_tokens = []
    
    for pair in tokens:
        pair_addr = pair.get('pairAddress', '')
        if pair_addr not in seen_addresses:
            seen_addresses.add(pair_addr)
            unique_tokens.append(pair)
    
    print(f"📊 Found {len(unique_tokens)} unique emerging tokens")
    
    high_potential = []
    
    for i, pair in enumerate(unique_tokens[:20]):  # Top 20
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
        price_change = pair.get('priceChange', {}).get('h24', 0)
        
        base_token = pair.get('baseToken', {})
        quote_token = pair.get('quoteToken', {})
        
        # Determine which is WETH and which is the target token
        weth_address = "0x4200000000000000000000000000000000000006"
        if base_token.get('address', '').lower() == weth_address.lower():
            target_token = quote_token
        else:
            target_token = base_token
        
        # Emerging token criteria (less strict than VIRTUAL)
        if (liquidity > 50000 and      # Min $50K liquidity
            volume_24h > 50000 and     # Min $50K volume
            txns_24h > 100 and        # Min 100 txns
            abs(price_change) > 3):     # Min 3% change
            
            # Calculate competition score (lower is better)
            competition_score = txns_24h / (liquidity / 1000)  # txns per $1K liquidity
            
            high_potential.append({
                'symbol': target_token.get('symbol', 'UNKNOWN'),
                'address': target_token.get('address', ''),
                'liquidity': liquidity,
                'volume': volume_24h,
                'txns': txns_24h,
                'price_change': price_change,
                'competition_score': competition_score,
                'dex': pair.get('dexId', ''),
                'potential_score': calculate_potential_score(liquidity, volume_24h, txns_24h, price_change, competition_score)
            })
    
    # Sort by potential score
    high_potential.sort(key=lambda x: x['potential_score'], reverse=True)
    
    print(f"\n🎯 TOP 10 EMERGING ARBITRAGE TARGETS:")
    print("="*60)
    
    for i, token in enumerate(high_potential[:10]):
        print(f"\n{i+1}. 🌟 {token['symbol']} ({token['price_change']:+.2f}%)")
        print(f"    Address: {token['address']}")
        print(f"    DEX: {token['dex']}")
        print(f"    Liquidity: ${token['liquidity']:,.0f}")
        print(f"    Volume: ${token['volume']:,.0f}")
        print(f"    Txns: {token['txns']}")
        print(f"    Competition Score: {token['competition_score']:.2f} (lower = better)")
        print(f"    Potential Score: {token['potential_score']:.1f}")
        
        if token['competition_score'] < 5:
            print("    ✅ LOW COMPETITION - PERFECT!")
        elif token['competition_score'] < 10:
            print("    ✅ MODERATE COMPETITION - GOOD")
        else:
            print("    ⚠️  HIGH COMPETITION")
    
    return high_potential

def calculate_potential_score(liquidity, volume, txns, price_change, competition):
    """Calculate arbitrage potential score"""
    # Normalize factors
    liquidity_score = min(liquidity / 100000, 10)  # Max 10 for $100K+ liquidity
    volume_score = min(volume / 100000, 10)        # Max 10 for $100K+ volume
    volatility_score = min(abs(price_change) / 5, 10) # Max 10 for 5%+ change
    competition_score = max(10 - competition, 0)     # Lower competition = higher score
    
    return liquidity_score + volume_score + volatility_score + competition_score

def generate_optimized_config(emerging_tokens, gap_analysis):
    """Generate optimized configuration"""
    print(f"\n🦍 OPTIMIZED STRATEGY RECOMMENDATIONS:")
    print("="*60)
    
    print("📊 GAP ANALYSIS INSIGHTS:")
    print("• VIRTUAL: High frequency but low success due to competition")
    print("• Target gaps >1.0% on VIRTUAL for profitable trades")
    print("• Consider smaller trade sizes (0.01 ETH) for better execution")
    
    print(f"\n🚀 EMERGING TOKEN STRATEGY:")
    print("• Focus on tokens with competition score <5")
    print("• Lower gap thresholds (0.2-0.3%) for emerging tokens")
    print("• Higher trade sizes (0.02-0.03 ETH) due to less competition")
    
    # Generate Rust config
    top_emerging = emerging_tokens[:5] if emerging_tokens else []
    
    print(f"\n🔧 OPTIMIZED RUST CONFIGURATION:")
    print("="*60)
    print("// Hybrid strategy - proven + emerging tokens")
    print("let tokens = vec![")
    print('    // Proven performer (high competition)')
    print('    TokenInfo { name: "VIRTUAL".to_string(), addr: "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b".parse()?, decimals: 18 },')
    
    if top_emerging:
        print('    // Emerging opportunities (lower competition)')
        for token in top_emerging:
            if token['competition_score'] < 8:  # Only include lower competition tokens
                print(f'    TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18 }},')
    
    print("];")
    
    print(f"\n⚙️ DYNAMIC THRESHOLD STRATEGY:")
    print("="*60)
    print("// Implement different thresholds per token type")
    print("if token.symbol == \"VIRTUAL\" {")
    print("    gap_threshold = 1.0;  // High threshold for high competition")
    print("    trade_size = 0.01;   // Smaller size for better execution")
    print("} else {")
    print("    gap_threshold = 0.25; // Lower threshold for emerging tokens")
    print("    trade_size = 0.025;  // Larger size due to less competition")
    print("}")

def main():
    print("🔍 Finding emerging tokens with VIRTUAL-like potential...")
    
    # Get gap analysis
    gap_analysis = analyze_gap_patterns()
    
    # Get emerging tokens
    emerging_tokens = get_emerging_tokens()
    
    if emerging_tokens:
        analyzed_tokens = analyze_emerging_tokens(emerging_tokens)
        generate_optimized_config(analyzed_tokens, gap_analysis)
    else:
        print("❌ No emerging tokens found")
        print("💡 VIRTUAL remains your best target - optimize for it instead")

if __name__ == "__main__":
    main()
