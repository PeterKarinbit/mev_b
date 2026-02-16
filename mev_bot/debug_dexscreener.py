#!/usr/bin/env python3
import requests
import json

def debug_dexscreener_response():
    """Debug what DexScreener is actually returning"""
    url = "https://api.dexscreener.com/latest/dex/search?q=WETH"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print("🔍 Raw API Response Structure:")
        print(f"Keys: {list(data.keys())}")
        
        if 'pairs' in data:
            pairs = data['pairs']
            print(f"\n📊 Total pairs: {len(pairs)}")
            
            # Show first few pairs
            for i, pair in enumerate(pairs[:5]):
                print(f"\n--- Pair {i+1} ---")
                print(f"DexId: {pair.get('dexId', 'N/A')}")
                print(f"ChainId: {pair.get('chainId', 'N/A')}")
                print(f"BaseToken: {pair.get('baseToken', {}).get('symbol', 'N/A')} - {pair.get('baseToken', {}).get('address', 'N/A')}")
                print(f"QuoteToken: {pair.get('quoteToken', {}).get('symbol', 'N/A')} - {pair.get('quoteToken', {}).get('address', 'N/A')}")
                print(f"Liquidity: ${pair.get('liquidity', {}).get('usd', 0):,.0f}")
                print(f"Volume 24h: ${pair.get('volume', {}).get('h24', 0):,.0f}")
                print(f"Txns 24h: {pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)}")
                
                # Check if it's Base chain
                if pair.get('chainId') == 'base':
                    print("✅ BASE CHAIN")
                else:
                    print(f"❌ Chain: {pair.get('chainId')}")
        else:
            print("❌ No 'pairs' key in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_dexscreener_response()
