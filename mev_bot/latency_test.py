
import os
import time
import requests
from web3 import Web3

# On-chain setup (The "True" Price)
RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# VVV/WETH Aerodrome Pool
POOL_ADDR = "0x01784ef301d79e4b2df3a21ad9a536d4cf09a5ce"
VVV = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"

def get_onchain_price():
    # Aerodrome Swap Pool (WETH/VVV)
    # reserves: [reserve0, reserve1, blockTimestampLast]
    abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint256"},{"name":"_reserve1","type":"uint256"},{"name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"}]
    pool = w3.eth.contract(address=Web3.to_checksum_address(POOL_ADDR), abi=abi)
    r0, r1, _ = pool.functions.getReserves().call()
    # reserve0 is WETH, reserve1 is VVV
    price = (r0 / 1e18) / (r1 / 1e18)
    return price

def test_latency():
    print("🕒 Starting Latency Benchmark (DexScreener vs BirdEye)...")
    
    # 1. On-chain Price (Baseline)
    t0 = time.time()
    onchain = get_onchain_price()
    print(f"✅ On-chain Price: {onchain:.8f} WETH | Fetch Time: {time.time() - t0:.2f}s")

    # 2. DexScreener
    t0 = time.time()
    ds_price = 0
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{VVV}"
        data = requests.get(url, timeout=5).json()
        pair = next(p for p in data['pairs'] if p['pairAddress'].lower() == POOL_ADDR.lower())
        ds_price = float(pair['priceNative'])
        print(f"📊 DexScreener Price: {ds_price:.8f} WETH | Fetch Time: {time.time() - t0:.2f}s")
        print(f"   Delta vs On-chain: {abs(ds_price - onchain)/onchain*100:.4f}%")
    except Exception as e:
        print(f"❌ DexScreener Error: {e}")

    # 3. Birdeye (Using public search endpoint if possible, or just scraping/browser check)
    # BirdEye usually requires x-api-key for standard REST. 
    # We will try a public metadata fetch if available.
    print("\n⚠️  BirdEye often requires an API key for REST. Checking public presence...")
    
test_latency()
