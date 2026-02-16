
import requests
from web3 import Web3

tokens = {
    "VVV": "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf",
    "ELSA": "0x29cC30f9D113B356Ce408667aa6433589CeCBDcA",
    "BNKR": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b",
    "ZRO": "0x6985884C4392D348587B19cb9eAAf157F13271cd",
    "DIEM": "0xF4d97F2da56e8c3098f3a8D538DB630A2606a024"
}

print("🔎 VERIFYING BEST POOLS FOR TARGETS")

for name, addr in tokens.items():
    print(f"\n--- {name} ---")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    data = requests.get(url).json()
    base_pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base']
    
    aero = [p for p in base_pairs if p.get('dexId') == 'aerodrome']
    uni = [p for p in base_pairs if p.get('dexId') == 'uniswap']
    
    if aero:
        best_aero = max(aero, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
        print(f"🚀 BEST AERO: {best_aero.get('quoteToken', {}).get('symbol')} | Liq: ${float(best_aero.get('liquidity', {}).get('usd',0)):,.0f} | {best_aero.get('pairAddress')}")
    
    if uni:
        best_uni = max(uni, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
        print(f"🦄 BEST UNI : {best_uni.get('quoteToken', {}).get('symbol')} | Liq: ${float(best_uni.get('liquidity', {}).get('usd',0)):,.0f} | {best_uni.get('pairAddress')}")
