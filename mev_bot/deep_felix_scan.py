
import requests

addr = '0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07'
url = f'https://api.dexscreener.com/latest/dex/tokens/{addr}'
data = requests.get(url).json()

# All base pairs with min liquidity
pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 500]

# Group by DEX and price to see clusters
print("📊 ALL REAL FELIX PAIRS ON BASE:")
for p in sorted(pairs, key=lambda x: float(x.get('priceUsd', 0))):
    dex = p.get('dexId')
    price = p.get('priceUsd')
    liq = p.get('liquidity', {}).get('usd', 0)
    vol = p.get('volume', {}).get('h24', 0)
    addr = p.get('pairAddress')
    label = p.get('labels', ['v2'])[0]
    print(f"   - {dex:12s} | {label:3s} | ${float(price):.8f} | liq ${float(liq):,.0f} | {addr}")

if len(pairs) >= 2:
    p_min = min(pairs, key=lambda x: float(x.get('priceUsd', 0)))
    p_max = max(pairs, key=lambda x: float(x.get('priceUsd', 0)))
    spread = (float(p_max['priceUsd']) - float(p_min['priceUsd'])) / float(p_min['priceUsd']) * 100
    print(f"\n💎 MAX SPREAD DETECTED: {spread:.2f}%")
    print(f"   BUY:  {p_min.get('dexId')} @ ${p_min.get('priceUsd')}")
    print(f"   SELL: {p_max.get('dexId')} @ ${p_max.get('priceUsd')}")
