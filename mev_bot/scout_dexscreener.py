import requests
import time

def scout():
    print("📢 SEARCHING DEXSCREENER FOR USDC GAPS ON BASE...")
    # Search for USDC to find main liquidity pairs on Base
    url = "https://api.dexscreener.com/latest/dex/search?q=USDC%20base"
    
    try:
        resp = requests.get(url).json()
        pairs = resp.get('pairs', [])
        
        # Group by token to find multiple DEX listings
        token_groups = {}
        for p in pairs:
            base_token = p['baseToken']['address'].lower()
            if base_token not in token_groups:
                token_groups[base_token] = []
            token_groups[base_token].append(p)
            
        print(f"📊 Scanned {len(pairs)} pairs. Found {len(token_groups)} unique tokens.")
        print("-" * 50)
        
        found_arb = False
        for token, listings in token_groups.items():
            if len(listings) > 1:
                # Find pairs on different DEXs (e.g. Aerodrome vs Uniswap)
                dexes = [l['dexId'] for l in listings]
                if len(set(dexes)) > 1:
                    # Calculate Gap
                    prices = [float(l['priceUsd']) for l in listings if 'priceUsd' in l]
                    if len(prices) < 2: continue
                    
                    max_p = max(prices)
                    min_p = min(prices)
                    gap = ((max_p - min_p) / min_p) * 100
                    
                    symbol = listings[0]['baseToken']['symbol']
                    
                    if gap > 0.5:
                        found_arb = True
                        print(f"💎 OPPORTUNITY: {symbol}")
                        print(f"   Gap: {gap:.2f}%")
                        for l in listings:
                            print(f"   - {l['dexId']} | Price: ${l['priceUsd']} | Vol: ${l['volume']['h24']:,}")
                        print("-" * 30)
        
        if not found_arb:
            print("🌑 No significant cross-DEX gaps found in trending tokens right now.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    scout()
