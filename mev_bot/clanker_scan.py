
import requests

addr = "0x1bc0c42215582d5A085795f4baDbaC3ff36d1Bcb"
url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"

try:
    data = requests.get(url, timeout=10).json()
    print("🔍 SCANNING CLANKER POOLS ON BASE...")
    print("-" * 80)
    print(f"{'DEX':12} | {'QUOTE':6} | {'PRICE':10} | {'LIQUIDITY':12} | {'ADDRESS'}")
    print("-" * 80)
    
    for p in data.get('pairs', []):
        if p.get('chainId') == 'base':
            dex = p.get('dexId', 'unknown')
            quote = p.get('quoteToken', {}).get('symbol', '???')
            price = f"${float(p.get('priceUsd', 0)):.4f}"
            liq = f"${float(p.get('liquidity', {}).get('usd', 0)):,.0f}"
            addr = p.get('pairAddress')
            print(f"{dex:12} | {quote:6} | {price:10} | {liq:12} | {addr}")
except Exception as e:
    print(f"Error: {e}")
