
import requests

targets = [
    {"name": "KellyClaude", "address": "0x50D2280441372486BeecdD328c1854743EBaCb07"},
    {"name": "DIEM", "address": "0xF4d97F2da56e8c3098f3a8D538DB630A2606a024"}
]

print("🔍 SCANNING NEW TARGETS...")

for t in targets:
    print(f"\n--- {t['name']} ({t['address'][:10]}...) ---")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{t['address']}"
    try:
        data = requests.get(url, timeout=10).json()
        pairs = data.get('pairs', [])
        found_pools = []
        for p in pairs:
            if p.get('chainId') == 'base':
                dex = p.get('dexId')
                quote = p.get('quoteToken', {}).get('symbol')
                price = float(p.get('priceNative', 0))
                liq = float(p.get('liquidity', {}).get('usd', 0))
                if liq > 1000:
                    found_pools.append({
                        "dex": dex,
                        "quote": quote,
                        "price": price,
                        "liq": liq,
                        "addr": p.get('pairAddress')
                    })
                    print(f"✅ {dex:12} | {quote:5} | {price:.10f} | Liq: ${liq:,.0f} | {p.get('pairAddress')}")
        
        # Spread calculation (Simple USD/Native comparison)
        if len(found_pools) >= 2:
            prices = [p['price'] for p in found_pools if p['quote'] in ['WETH', 'ETH', 'VVV']]
            if len(prices) >= 2:
                spread = (max(prices) - min(prices)) / min(prices) * 100
                print(f"💰 THEORETICAL SPREAD: {spread:.2f}%")
            else:
                print("⚠️ Need at least 2 pools with same quote token for spread analysis.")
    except Exception as e:
        print(f"Error fetching {t['name']}: {e}")
