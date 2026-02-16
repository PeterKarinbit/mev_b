
import requests

tokens = {
    "MORPHO": "0xBAa5CC21fd487B8Fcc2F632f3F4E8D37262a0842",
    "KEETA": "0xc0634090F2Fe6c6d75e61Be2b949464aBB498973"
}

print("🔎 SCANNING MORPHO & KEETA FOR ARB GAPS...")

for name, addr in tokens.items():
    print(f"\n--- {name} ({addr}) ---")
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
            price_native = float(p.get('priceNative', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            
            if liq > 1000:
                print(f"✅ {dex:12} | {base}/{quote} | Native: {price_native:.10f} | Liq: ${liq:,.0f}")
                
        # Calculate spreads for WETH pools
        weth_pools = [p for p in base_pairs if p.get('quoteToken', {}).get('symbol') == 'WETH' and float(p.get('liquidity', {}).get('usd', 0)) > 2000]
        if len(weth_pools) >= 2:
            prices = [float(p.get('priceNative', 0)) for p in weth_pools]
            spread = (max(prices) - min(prices)) / min(prices) * 100
            print(f"💰 SPREAD (WETH): {spread:.2f}%")
        else:
            print("⏳ Not enough deep WETH pools for direct arb.")
            
    except Exception as e:
        print(f"Error scanning {name}: {e}")
