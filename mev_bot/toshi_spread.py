
import requests
import json

TOSHI = "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4"
url = f"https://api.dexscreener.com/latest/dex/tokens/{TOSHI}"

try:
    data = requests.get(url, timeout=10).json()
    pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and p.get('quoteToken', {}).get('symbol') in ['WETH', 'ETH']]
    
    if not pairs:
        print("No TOSHI/WETH pairs found on Base.")
    else:
        print(f"🔍 TOSHI/WETH SPREAD ANALYSIS")
        print("-" * 85)
        print(f"{'DEX':15} | {'PRICE (USD)':12} | {'PRICE (WETH)':18} | {'LIQUIDITY':12}")
        print("-" * 85)
        
        # Sort by price
        pairs.sort(key=lambda x: float(x.get('priceUsd', 0)))
        
        for p in pairs:
            dex = p.get('dexId', 'unknown')
            price_usd = f"${float(p.get('priceUsd', 0)):.6f}"
            price_weth = f"{float(p.get('priceNative', 0)):.10f}"
            liq = f"${float(p.get('liquidity', {}).get('usd', 0)):,.0f}"
            print(f"{dex:15} | {price_usd:12} | {price_weth:18} | {liq:12}")
        
        if len(pairs) >= 2:
            # Filter for pools with at least $1000 liquidity to find real spreads
            liquid_pairs = [p for p in pairs if float(p.get('liquidity', {}).get('usd', 0)) > 1000]
            if len(liquid_pairs) >= 2:
                min_p = float(liquid_pairs[0]['priceUsd'])
                max_p = float(liquid_pairs[-1]['priceUsd'])
                spread = (max_p - min_p) / min_p * 100
                print("-" * 85)
                print(f"💰 CURRENT MAX SPREAD (Liq > $1k): {spread:.2f}%")
                print(f"   Buy on: {liquid_pairs[0]['dexId']}")
                print(f"   Sell on: {liquid_pairs[-1]['dexId']}")
            else:
                print("\n⚠️ Not enough liquid pools (> $1,000) to calculate a safe spread.")

except Exception as e:
    print(f"Error: {e}")
