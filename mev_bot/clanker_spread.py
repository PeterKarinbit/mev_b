
import requests
import json

CLANKER = "0x1bc0c42215582d5a085795f4badbac3ff36d1bcb"
url = f"https://api.dexscreener.com/latest/dex/tokens/{CLANKER}"

try:
    data = requests.get(url, timeout=10).json()
    pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and p.get('quoteToken', {}).get('symbol') == 'WETH']
    
    if not pairs:
        print("No CLANKER/WETH pairs found on Base.")
    else:
        print(f"🔍 CLANKER/WETH SPREAD ANALYSIS")
        print("-" * 85)
        print(f"{'DEX':15} | {'PRICE (USD)':12} | {'PRICE (WETH)':18} | {'LIQUIDITY':12}")
        print("-" * 85)
        
        # Sort by price to find spread
        pairs.sort(key=lambda x: float(x.get('priceUsd', 0)))
        
        for p in pairs:
            dex = p.get('dexId', 'unknown')
            price_usd = f"${float(p.get('priceUsd', 0)):.4f}"
            price_weth = f"{float(p.get('priceNative', 0)):.8f}"
            liq = f"${float(p.get('liquidity', {}).get('usd', 0)):,.0f}"
            print(f"{dex:15} | {price_usd:12} | {price_weth:18} | {liq:12}")
        
        if len(pairs) >= 2:
            min_p = float(pairs[0]['priceUsd'])
            max_p = float(pairs[-1]['priceUsd'])
            spread = (max_p - min_p) / min_p * 100
            print("-" * 85)
            print(f"💰 CURRENT MAX SPREAD: {spread:.2f}%")
            print(f"   Buy on: {pairs[0]['dexId']}")
            print(f"   Sell on: {pairs[-1]['dexId']}")

except Exception as e:
    print(f"Error: {e}")
