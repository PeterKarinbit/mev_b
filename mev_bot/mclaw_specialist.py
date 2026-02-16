
import os
import asyncio
import time
from web3 import Web3
from dotenv import load_dotenv

# Use absolute path for .env
env_path = "/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/mev_bot/.env"
load_dotenv(env_path)

# --- CONFIG ---
# Contract: MclawTriangle (deployed to 0xA5B99eA7F336528a177b9B956ad6579b8B496045)
CONTRACT_ADDR = "0xA5B99eA7F336528a177b9B956ad6579b8B496045"
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
MCLAWD = "0x41f647dc424a298c11a8868151803a11a01dcd84"

# UNI V3 POOLS
POOL_WETH_MCLAWD = "0x7b70a37beF035dA212479EfFdC8cAc2f358b7fB5" # Fee 3000 (0.3%)
# USDC/WETH on Base is 0x4C36388bE6F65271172aAad57C175E4D13bb69 (Fee 500)
POOL_USDC_WETH = "0x4C36388bE6F65271172aAad57C175E4D13bb69"

# We need a MCLAWD/USDC pool for triangle arb. 
# If none exists yet, we can't do triangle via USDC.
# Let's check for other pools for MCLAWD.

RPC_URL = "https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

ABI_V3 = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"}],"stateMutability":"view","type":"function"}]

def get_v3_price(pool_addr, is_token0):
    try:
        pool = w3.eth.contract(address=Web3.to_checksum_address(pool_addr), abi=ABI_V3)
        s = pool.functions.slot0().call()
        p_raw = (s[0] / 2**96)**2
        return p_raw if is_token0 else (1/p_raw)
    except:
        return 0

async def monitor_mclaw():
    print(f"🚀 MCLAW SPECIALIST v1.0 | CONTRACT: {CONTRACT_ADDR}")
    print(f"Monitoring: {POOL_WETH_MCLAWD}")
    
    while True:
        try:
            # Price of 1 MCLAWD in WETH
            # Token0: WETH (0x4200...), Token1: MCLAWD (0x41f6...)
            # Since 0x41f6... < 0x4200..., MCLAWD is token0.
            # Wait, 0x41f6... vs 0x4200...
            # 41 < 42. So MCLAWD is token0.
            p_mclaw_in_eth = get_v3_price(POOL_WETH_MCLAWD, True)
            
            if p_mclaw_in_eth == 0:
                await asyncio.sleep(1)
                continue
                
            print(f"MCLAWD Price: {p_mclaw_in_eth:.10f} ETH", end="\r")
            
            # Since we only have one pool, direct arb is impossible.
            # But we can "Snif" for a second pool creation or big slippage if we find another route.
            # For now, let's just report the price and wait for user's next pair.
            
        except Exception as e:
            print(f"\nError: {e}")
            
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(monitor_mclaw())
