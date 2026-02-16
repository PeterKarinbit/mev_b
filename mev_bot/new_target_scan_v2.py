
import requests

tokens = {
    "ELSA": "0x29cC30f9D113B356Ce408667aa6433589CeCBDcA",
    "MOLTEN": "0x59c0d5c34C301aC0600147924D6C9be22a2F0B07",
    "ZRO": "0x6985884C4392D348587B19cb9eAAf157F13271cd",
    "BNKR": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"
}

print("🔍 SCANNING NEW TARGETS FOR ARB GAPS...")

for name, addr in tokens.items():
    print(f"\n--- {name} ({addr[:10]}...) ---")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    try:
        data = requests.get(url, timeout=10).json()
        base_pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base']
        
        if not base_pairs:
            print("❌ No Base pairs found.")
            continue
            
        for p in base_pairs:
            dex = p.get('dexId')
            base = p.get('baseToken', {}).get('symbol')
            quote = p.get('quoteToken', {}).get('symbol')
            price = float(p.get('priceUsd', 0))
            price_native = float(p.get('priceNative', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            
            if liq > 1000:
                print(f"✅ {dex:12} | {base}/{quote} | USD: ${price:,.6f} | Native: {price_native:.10f} | Liq: ${liq:,.0f}")
                
        # Simple cross-DEX comparison for the same quote
        quotes = set(p.get('quoteToken', {}).get('symbol') for p in base_pairs)
        for q in quotes:
            q_pools = [p for p in base_pairs if p.get('quoteToken', {}).get('symbol') == q and float(p.get('liquidity', {}).get('usd', 0)) > 1000]
            if len(q_pools) >= 2:
                prices = [float(p.get('priceNative', 0)) for p in q_pools]
                spread = (max(prices) - min(prices)) / min(prices) * 100
                print(f"💰 SPREAD ({q}): {spread:.2f}%")
                
    except Exception as e:
        print(f"Error scanning {name}: {e}")
