
import os
import time
import requests
import asyncio
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/mev_bot/.env')

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
WETH = "0x4200000000000000000000000000000000000006"
VVV = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"
AERO_POOL = "0x01784ef301d79e4b2df3a21ad9a536d4cf09a5ce"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

def get_onchain_price():
    # Aerodrome getReserves
    abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint256"},{"name":"_reserve1","type":"uint256"},{"name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"}]
    pool = w3.eth.contract(address=Web3.to_checksum_address(AERO_POOL), abi=abi)
    try:
        r0, r1, _ = pool.functions.getReserves().call()
        # reserve0 is WETH, reserve1 is VVV
        return (r0 / 1e18) / (r1 / 1e18)
    except:
        return None

def get_ds_price():
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{AERO_POOL}"
        data = requests.get(url, timeout=5).json()
        return float(data['pair']['priceNative'])
    except:
        return None

async def benchmark():
    print("🚀 LATENCY BENCHMARK: ON-CHAIN vs DEXSCREENER")
    print("-" * 60)
    print(f"{'Time':<10} | {'On-Chain (WETH)':<18} | {'DexScreener (WETH)':<18} | {'Lag %':<8}")
    print("-" * 60)
    
    for _ in range(12): # Run for 1 minute
        t_str = time.strftime("%H:%M:%S")
        onchain = get_onchain_price()
        ds = get_ds_price()
        
        if onchain and ds:
            lag = (onchain - ds) / onchain * 100
            print(f"{t_str:<10} | {onchain:18.8f} | {ds:18.8f} | {lag:+.4f}%")
        else:
            print(f"{t_str:<10} | Error fetching data")
            
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(benchmark())
