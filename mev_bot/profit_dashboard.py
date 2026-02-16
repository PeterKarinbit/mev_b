
import requests

tokens = {
    "VVV": "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf",
    "TOSHI": "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4",
    "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
    "DIEM": "0xF4d97F2da56e8c3098f3a8D538DB630A2606a024",
    "ELSA": "0x29cC30f9D113B356Ce408667aa6433589CeCBDcA",
    "MOLTEN": "0x59c0d5c34C301aC0600147924D6C9be22a2F0B07",
    "ZRO": "0x6985884C4392D348587B19cb9eAAf157F13271cd",
    "BNKR": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"
}

print("📊 CURRENT PROFITABILITY DASHBOARD")
print(f"{'TOKEN':10} | {'MAX SPREAD':10} | {'BEST DEX PAIR':25} | {'LIQUIDITY'}")
print("-" * 70)

for name, addr in tokens.items():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    try:
        data = requests.get(url, timeout=10).json()
        base_pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 2000]
        
        if not base_pairs:
            continue
            
        # Group by quote token (WETH, USDC, etc)
        quotes = set(p.get('quoteToken', {}).get('symbol') for p in base_pairs)
        max_token_spread = 0
        best_pair = "N/A"
        best_liq = 0
        
        for q in quotes:
            q_pools = [p for p in base_pairs if p.get('quoteToken', {}).get('symbol') == q]
            if len(q_pools) >= 2:
                prices = [float(p.get('priceNative', 0)) for p in q_pools]
                spread = (max(prices) - min(prices)) / min(prices) * 100
                if spread > max_token_spread:
                    max_token_spread = spread
                    dexes = [p.get('dexId') for p in q_pools]
                    best_pair = f"{dexes[0]} / {dexes[1]} ({q})"
                    best_liq = sum(float(p.get('liquidity', {}).get('usd', 0)) for p in q_pools)
        
        status = "🔥" if max_token_spread > 1.3 else "⏳" if max_token_spread > 0.8 else "💤"
        print(f"{status} {name:7} | {max_token_spread:9.2f}% | {best_pair:25} | ${best_liq:,.0f}")
                
    except Exception:
        pass
