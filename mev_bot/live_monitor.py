import time, os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv("mev_bot/.env")
RPC_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

TOKENS = {
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "DEGEN": "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
    "BRETT": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
    "SPAWN": "0x5f074d084c7a6598c1143c75ca77a3465941656c",
    "MOLTX": "0x5608b0d46654876b5c2c4aa0223592237083049b",
    "H1DR4": "0x9812eb121021bc5630327f426284fadd360824b2",
    "TIBBIR": "0x2e864070a2f4da8e1e70e9a502f615364132c34f"
}

PAIRS = [
    ("USDC", "WETH"), ("WETH", "DEGEN"), ("WETH", "BRETT"),
    ("WETH", "SPAWN"), ("WETH", "MOLTX"), ("WETH", "TIBBIR")
]

RESERVES_ABI = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
V3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
DEC_CACHE = {"0x4200000000000000000000000000000000000006": 18, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": 6}

def get_prices(a1, a2):
    try:
        # Aero
        f_aero = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pa = f_aero.functions.getPool(a1, a2, False).call()
        if int(pa, 16) == 0: return None, None
        
        pool = w3.eth.contract(address=pa, abi=RESERVES_ABI)
        res = pool.functions.getReserves().call()
        t0 = pool.functions.token0().call()
        ra, rb = (res[0], res[1]) if t0.lower() == a1.lower() else (res[1], res[0])
        aero_p = (rb / 10**DEC_CACHE.get(a2, 18)) / (ra / 10**DEC_CACHE.get(a1, 18))

        # Uni
        f_uni = w3.eth.contract(address="0x33128a8fC17869897dcE68Ed026d694621f6FDfD", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"f","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pu = f_uni.functions.getPool(a1, a2, 3000).call()
        # Fallback to fee 500 or 10000 if 3000 pool doesn't exist
        
        if int(pu, 16) == 0: return None, None
        
        pool_uni = w3.eth.contract(address=pu, abi=V3_POOL_ABI)
        slot0 = pool_uni.functions.slot0().call()
        sq = slot0[0]
        # Fixed Calculation Formula
        uni_p = ((sq / (2**96)) ** 2) * (10**DEC_CACHE.get(a1, 18)) / (10**DEC_CACHE.get(a2, 18))
        
        return aero_p, uni_p
    except: return None, None

def monitor():
    print(f"\n📺 GORILLA LIVE MONITOR (Base Mainnet)")
    print(f"{'PAIR':<15} | {'AERODROME':<12} | {'UNISWAP':<12} | {'GAP %':<8}")
    print("-" * 55)
    
    while True:
        for p in PAIRS:
            a1, a2 = TOKENS[p[0]], TOKENS[p[1]]
            aero, uni = get_prices(a1, a2)
            
            if aero and uni:
                gap = (abs(aero - uni) / min(aero, uni)) * 100
                color = "\033[92m" if gap > 0.5 else "\033[0m" # Green if gap > 0.5%
                print(f"{color}{p[0]}/{p[1]:<9} | {aero:.6f}     | {uni:.6f}     | {gap:.3f}%\033[0m")
        
        print("-" * 55)
        time.sleep(2)

if __name__ == "__main__":
    monitor()
