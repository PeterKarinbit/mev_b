
import requests

tokens = {
    "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
    "ELSA": "0x29cC30f9D113B356Ce408667aa6433589CeCBDcA",
    "VVV": "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"
}

print("🎯 ORGANIZED PROFIT SCAN")

for name, addr in tokens.items():
    print(f"\n--- {name} ---")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    try:
        data = requests.get(url, timeout=10).json()
        base_pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base']
        
        # Check USDC pools
        usdc_pools = [p for p in base_pairs if p.get('quoteToken', {}).get('symbol') == 'USDC' and float(p.get('liquidity', {}).get('usd', 0)) > 5000]
        for p in usdc_pools:
            print(f"💰 USDC | {p.get('dexId'):12} | Price: ${p.get('priceUsd'):10} | Liq: ${float(p.get('liquidity', {}).get('usd',0)):,.0f} | {p.get('pairAddress')}")
            
        # Check WETH pools
        weth_pools = [p for p in base_pairs if p.get('quoteToken', {}).get('symbol') == 'WETH' and float(p.get('liquidity', {}).get('usd', 0)) > 5000]
        for p in weth_pools:
            print(f"💎 WETH | {p.get('dexId'):12} | Price: ${p.get('priceUsd'):10} | Liq: ${float(p.get('liquidity', {}).get('usd',0)):,.0f} | {p.get('pairAddress')}")
            
    except Exception as e:
        print(f"Error: {e}")
