
import requests
from web3 import Web3

VVV = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"
logger_fmt = "{:<12} | {:<5} | {:<12} | {:<12} | {:<15}"

print("🔍 SCANNING VVV POOLS...")
print(logger_fmt.format("DEX", "QUOTE", "PRICE", "LIQUIDITY", "ADDRESS"))
print("-" * 65)

try:
    data = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{VVV}", timeout=10).json()
    pairs = data.get('pairs', [])
    for p in pairs:
        if p.get('chainId') == 'base':
            dex = p.get('dexId', 'unknown')
            quote = p.get('quoteToken', {}).get('symbol', '???')
            price = f"${float(p.get('priceUsd', 0)):.6f}"
            liq = f"${float(p.get('liquidity', {}).get('usd', 0)):,.0f}"
            addr = p.get('pairAddress')[:15] + "..."
            print(logger_fmt.format(dex, quote, price, liq, addr))
except Exception as e:
    print(f"Error: {e}")
