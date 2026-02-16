#!/usr/bin/env python3
import requests
import json

def analyze_usdc_vs_weth_arbitrage():
    """Compare USDC vs WETH arbitrage opportunities"""
    print("🔍 USDC vs WETH ARBITRAGE ANALYSIS")
    print("="*60)
    
    # Check USDC liquidity on Base
    usdc_address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    weth_address = "0x4200000000000000000000000000000000000006"
    
    # Get top tokens with USDC pairs
    try:
        # Search for popular tokens
        search_url = "https://api.dexscreener.com/latest/dex/search?q=VIRTUAL"
        response = requests.get(search_url, timeout=10)
        data = response.json()
        
        if 'pairs' in data:
            usdc_pairs = []
            weth_pairs = []
            
            for pair in data['pairs']:
                if pair.get('chainId') == 'base':
                    base_addr = pair.get('baseToken', {}).get('address', '').lower()
                    quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
                    
                    if base_addr == usdc_address.lower() or quote_addr == usdc_address.lower():
                        usdc_pairs.append(pair)
                    elif base_addr == weth_address.lower() or quote_addr == weth_address.lower():
                        weth_pairs.append(pair)
            
            print(f"📊 VIRTUAL Pairs Found:")
            print(f"  USDC pairs: {len(usdc_pairs)}")
            print(f"  WETH pairs: {len(weth_pairs)}")
            
            # Analyze liquidity comparison
            if usdc_pairs and weth_pairs:
                usdc_liquidity = sum(p.get('liquidity', {}).get('usd', 0) for p in usdc_pairs)
                weth_liquidity = sum(p.get('liquidity', {}).get('usd', 0) for p in weth_pairs)
                
                print(f"\n💰 LIQUIDITY COMPARISON:")
                print(f"  USDC Total: ${usdc_liquidity:,.0f}")
                print(f"  WETH Total: ${weth_liquidity:,.0f}")
                print(f"  USDC Advantage: {((usdc_liquidity - weth_liquidity) / weth_liquidity * 100):+.1f}%")
                
                # Show top pairs
                print(f"\n🏆 TOP USDC PAIRS:")
                for i, pair in enumerate(sorted(usdc_pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0), reverse=True)[:3]):
                    liquidity = pair.get('liquidity', {}).get('usd', 0)
                    volume = pair.get('volume', {}).get('h24', 0)
                    print(f"  {i+1}. {pair.get('dexId', 'N/A')}: ${liquidity:,.0f} liquidity, ${volume:,.0f} volume")
                
                print(f"\n🏆 TOP WETH PAIRS:")
                for i, pair in enumerate(sorted(weth_pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0), reverse=True)[:3]):
                    liquidity = pair.get('liquidity', {}).get('usd', 0)
                    volume = pair.get('volume', {}).get('h24', 0)
                    print(f"  {i+1}. {pair.get('dexId', 'N/A')}: ${liquidity:,.0f} liquidity, ${volume:,.0f} volume")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n💡 USDC ARBITRAGE ADVANTAGES:")
    print("="*60)
    print("✅ Lower flash loan fees (stablecoin borrowing is cheaper)")
    print("✅ More trading pairs (every token has USDC pairs)")
    print("✅ Stable value calculations (no ETH price volatility)")
    print("✅ Higher liquidity (USDC pools are typically deeper)")
    print("✅ Less competition (most MEV bots focus on WETH)")
    print("✅ Better for large trades (stablecoin pools handle bigger sizes)")
    
    print(f"\n⚙️ IMPLEMENTATION STRATEGY:")
    print("="*60)
    print("1. Change asset from WETH to USDC in contract calls")
    print("2. Update trade amounts (USDC uses 6 decimals vs 18 for ETH)")
    print("3. Lower gap thresholds (USDC arbitrage is more profitable)")
    print("4. Increase trade sizes (USDC pools have more liquidity)")
    print("5. Monitor USDC-specific opportunities")
    
    print(f"\n🎯 RECOMMENDED CONFIG:")
    print("="*60)
    print("// USDC-based configuration")
    print("const USDC: &str = \"0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\";")
    print("")
    print("fn get_trade_config(token_symbol: &str) -> (f64, u64) {")
    print("    match token_symbol {")
    print('        "VIRTUAL" => (0.6, 20000000000u64),     // 0.6% gap, 20,000 USDC')
    print('        "DEGEN" => (0.3, 15000000000u64),       // 0.3% gap, 15,000 USDC')
    print('        _ => (0.15, 25000000000u64),           // 0.15% gap, 25,000 USDC')
    print("    }")
    print("}")

if __name__ == "__main__":
    analyze_usdc_vs_weth_arbitrage()
