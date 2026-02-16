
import requests

targets = [
    {"name": "AntiHunter", "address": "0xe2f3FaE4bc62E21826018364aa30ae45D430bb07"},
    {"name": "VIRTUAL", "address": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"}
]

print("🔍 ANALYZING POOLS FOR NEW TARGETS...")

for t in targets:
    print(f"\n--- {t['name']} ({t['address'][:8]}...) ---")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{t['address']}"
    try:
        data = requests.get(url, timeout=10).json()
        pairs = data.get('pairs', [])
        for p in pairs:
            if p.get('chainId') == 'base':
                dex = p.get('dexId')
                quote = p.get('quoteToken', {}).get('symbol')
                price = p.get('priceUsd')
                liq = float(p.get('liquidity', {}).get('usd', 0))
                label = p.get('labels', [])
                if quote == 'WETH' and liq > 5000:
                    print(f"✅ {dex:12} | {quote:5} | ${float(price):.8f} | Liq: ${liq:,.0f} | {p.get('pairAddress')} | Labels: {label}")
    except Exception as e:
        print(f"Error fetching {t['name']}: {e}")
