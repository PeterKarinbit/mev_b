
import requests

tokens = {
    "KellyClaude": "0x50D2280441372486BeecdD328c1854743EBaCb07",
    "DIEM": "0xF4d97F2da56e8c3098f3a8D538DB630A2606a024",
    "VVV": "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"
}

print("🔍 DEEP SCAN FOR ARB OPPORTUNITIES")

for name, addr in tokens.items():
    print(f"\n--- {name} ---")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    try:
        data = requests.get(url, timeout=10).json()
        for p in data.get('pairs', []):
            if p.get('chainId') == 'base':
                dex = p.get('dexId')
                base = p.get('baseToken', {}).get('symbol')
                quote = p.get('quoteToken', {}).get('symbol')
                liq = float(p.get('liquidity', {}).get('usd', 0))
                price = p.get('priceUsd', '0')
                if liq > 500:
                    print(f"✅ {dex:12} | {base}/{quote} | ${float(price):.8f} | Liq: ${liq:,.0f} | {p.get('pairAddress')}")
    except Exception as e:
        print(f"Error: {e}")
