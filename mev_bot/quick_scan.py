
import requests
import time

tokens = {
    'VIRTUAL': '0x0b3e32845582222E555335911A017ef74550cc11',
    'DEGEN': '0x4ed4E28C2F43d0f0050672e1dC16f298BD898687',
    'cbBTC': '0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf',
    'AERO': '0x9401562132ee8740d4b769b6ad8325D001711204',
    'FELIX': '0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07'
}

print("="*60)
print("🚀 SCANNING FOR BASE ARBITRAGE OPPORTUNITIES")
print("="*60)

for name, addr in tokens.items():
    try:
        url = f'https://api.dexscreener.com/latest/dex/tokens/{addr}'
        r = requests.get(url, timeout=10)
        data = r.json()
        pairs = data.get('pairs', [])
        if not pairs: continue
        
        base_pairs = [p for p in pairs if p.get('chainId') == 'base']
        if len(base_pairs) < 2: continue
        
        # Filter for decent liquidity
        valid_pairs = [p for p in base_pairs if float(p.get('liquidity', {}).get('usd', 0)) > 2000]
        if len(valid_pairs) < 2: continue
        
        prices = {}
        for p in valid_pairs:
            dex = p.get('dexId', 'unknown')
            price = float(p.get('priceUsd', 0))
            if dex not in prices or price > prices[dex][0]: # Key by dex, keep max price for spread calc
                prices[dex] = (price, p.get('url'))

        if len(prices) < 2: continue
        
        all_prices = [val[0] for val in prices.values()]
        min_p = min(all_prices)
        max_p = max(all_prices)
        spread = (max_p - min_p) / min_p * 100
        
        if spread > 0.5:
            print(f"\n💎 {name} | Spread: {spread:.2f}%")
            print(f"   Buy: {min([k for k,v in prices.items() if v[0] == min_p])[0]} @ ${min_p:.6f}")
            print(f"   Sell: {max([k for k,v in prices.items() if v[0] == max_p])[0]} @ ${max_p:.6f}")
            print(f"   Potential: {'✅ ACTIVE' if spread > 1.0 else '⚠️ LOW MARGIN'}")
    except Exception as e:
        print(f"Error checking {name}: {e}")

print("\n" + "="*60)
