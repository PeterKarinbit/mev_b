
import requests
import json

tokens = [
    {'name': 'VVV (Venice)', 'address': '0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf'},
    {'name': 'CLANKER (0x06Ce...)', 'address': '0x06CecE127F81Bf76d388859549A93a120Ec52BA3'}
]

print("="*60)
print("🚀 TARGET TOKEN ARBITRAGE SCAN")
print("="*60)

for t in tokens:
    print(f"\n🔍 Analyzing {t['name']}")
    print(f"   Address: {t['address']}")
    
    url = f"https://api.dexscreener.com/latest/dex/tokens/{t['address']}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base']
        
        if not pairs:
            print("   ❌ No pairs found on Base")
            continue
            
        # Group by DEX to see where liquidity sits
        valid_pairs = [p for p in pairs if float(p.get('liquidity', {}).get('usd', 0)) > 500]
        
        if len(valid_pairs) < 2:
            print(f"   ⚠️ Only {len(valid_pairs)} liquid pools found (>{500} liq).")
            # Filter for any liquidity to see what's out there
            any_liq = [p for p in pairs if float(p.get('liquidity', {}).get('usd', 0)) > 0]
            for p in any_liq[:5]:
                print(f"     - {p.get('dexId'):12s} | {p.get('quoteToken', {}).get('symbol'):5s} | ${float(p.get('priceUsd', 0)):.8f} | Liq: ${float(p.get('liquidity', {}).get('usd', 0)):,.0f}")
            continue
            
        prices = [float(p.get('priceUsd', 0)) for p in valid_pairs]
        min_p = min(prices)
        max_p = max(prices)
        spread = (max_p - min_p) / min_p * 100
        
        print(f"   🔥 MAX SPREAD: {spread:.2f}%")
        
        # Details
        for p in sorted(valid_pairs, key=lambda x: float(x.get('priceUsd', 0))):
            dex = p.get('dexId')
            quote = p.get('quoteToken', {}).get('symbol')
            price = float(p.get('priceUsd', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            vol = float(p.get('volume', {}).get('h24', 0))
            print(f"     - {dex:12s} | {quote:5s} | ${price:.8f} | Liq: ${liq:,.0f} | Vol 24h: ${vol:,.0f}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*60)
