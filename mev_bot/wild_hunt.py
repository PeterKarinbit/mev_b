from web3 import Web3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()
BOT_ADDRESS = os.getenv("BOT_ADDRESS")
PRIVATE_KEY = os.getenv("BOT_PRIVATE_KEY")

# ───────────────────────── RPC ROTATION ─────────────────────────
RPC_URLS = [
    "https://mainnet.base.org",
    "https://base.llamarpc.com",
    "https://1rpc.io/base",
    "https://base.meowrpc.com"
]
rpc_index = 0

def get_w3():
    global rpc_index
    for _ in range(len(RPC_URLS)):
        url = RPC_URLS[rpc_index]
        rpc_index = (rpc_index + 1) % len(RPC_URLS)
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 8}))
            if w3.is_connected():
                return w3
        except:
            continue
    return None

# ───────────────────────── CONTRACTS ─────────────────────────
AERO_FACTORY = Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da")
UNI_V3_FACTORY = Web3.to_checksum_address("0x33128a8fC17869897dcE68Ed026d694621f6FDfD")

TOKENS = {
    "WETH":    Web3.to_checksum_address("0x4200000000000000000000000000000000000006"),
    "USDC":    Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
    "AERO":    Web3.to_checksum_address("0x940181a94a35a4569e4529a3cdfb74e38fd98631"),
    "BRETT":   Web3.to_checksum_address("0x532f27101965dd16442E59d40670FaF5eBB142E4"),
    "DEGEN":   Web3.to_checksum_address("0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed"),
    "VIRTUAL": Web3.to_checksum_address("0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"),
}

PAIRS = [
    ("WETH",    "USDC"),
    ("AERO",    "USDC"),
    ("BRETT",   "WETH"),
    ("VIRTUAL", "WETH"),
    ("DEGEN",   "WETH"),
]

# ───────────────────────── ABIs ─────────────────────────
FACTORY_ABI    = json.loads('[{"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]')
V3_FACTORY_ABI = json.loads('[{"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]')
RESERVES_ABI   = json.loads('[{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]')
V3_POOL_ABI    = json.loads('[{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]')
ERC20_ABI      = json.loads('[{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')

# ───────────────────────── CACHING ─────────────────────────
DECIMAL_CACHE = {}
POOL_CACHE = {}  # (dex, tokenA, tokenB) -> pool_address

def get_decimals(addr, w3):
    if addr not in DECIMAL_CACHE:
        DECIMAL_CACHE[addr] = w3.eth.contract(address=addr, abi=ERC20_ABI).functions.decimals().call()
    return DECIMAL_CACHE[addr]

# ───────────────────────── AERODROME PRICE ─────────────────────────
def get_aero_price(token_a, token_b, w3):
    """Returns the price of token_a denominated in token_b on Aerodrome."""
    try:
        cache_key = ("aero", token_a, token_b)
        if cache_key in POOL_CACHE:
            pool_addr = POOL_CACHE[cache_key]
        else:
            factory = w3.eth.contract(address=AERO_FACTORY, abi=FACTORY_ABI)
            pool_addr = factory.functions.getPool(token_a, token_b, False).call()
            if pool_addr == "0x0000000000000000000000000000000000000000":
                return None
            POOL_CACHE[cache_key] = pool_addr

        pool = w3.eth.contract(address=pool_addr, abi=RESERVES_ABI)
        res = pool.functions.getReserves().call()
        pool_token0 = pool.functions.token0().call()

        dec_a = get_decimals(token_a, w3)
        dec_b = get_decimals(token_b, w3)

        # Figure out which reserve belongs to which token
        if pool_token0.lower() == token_a.lower():
            reserve_a, reserve_b = res[0], res[1]
        else:
            reserve_a, reserve_b = res[1], res[0]

        # Price = how much token_b you get per 1 token_a
        if reserve_a == 0:
            return None
        price = (reserve_b / 10**dec_b) / (reserve_a / 10**dec_a)
        # Sanity: reject impossible prices
        if price <= 0 or price > 1e12:
            return None
        return price
    except:
        return None

# ───────────────────────── UNISWAP V3 PRICE ─────────────────────────
def get_uni_price(token_a, token_b, w3):
    """Returns the price of token_a denominated in token_b on Uniswap V3."""
    for fee in [500, 3000, 10000, 100]:
        try:
            cache_key = ("uni", token_a, token_b, fee)
            if cache_key in POOL_CACHE:
                pool_addr = POOL_CACHE[cache_key]
            else:
                factory = w3.eth.contract(address=UNI_V3_FACTORY, abi=V3_FACTORY_ABI)
                pool_addr = factory.functions.getPool(token_a, token_b, fee).call()
                if pool_addr == "0x0000000000000000000000000000000000000000":
                    continue
                POOL_CACHE[cache_key] = pool_addr

            pool = w3.eth.contract(address=pool_addr, abi=V3_POOL_ABI)
            slot0 = pool.functions.slot0().call()
            sqrtPriceX96 = slot0[0]
            if sqrtPriceX96 == 0:
                continue

            pool_token0 = pool.functions.token0().call()
            dec_a = get_decimals(token_a, w3)
            dec_b = get_decimals(token_b, w3)

            # sqrtPriceX96 gives price of token1 in terms of token0
            # price_raw = (token1 / token0) in raw units
            price_raw = (sqrtPriceX96 / (2**96)) ** 2

            if pool_token0.lower() == token_a.lower():
                # token0 = A, token1 = B → price_raw = B_raw / A_raw
                price = price_raw * (10**dec_a) / (10**dec_b)
            else:
                # token0 = B, token1 = A → price_raw = A_raw / B_raw → invert
                price = (1.0 / price_raw) * (10**dec_b) / (10**dec_a)

            # Sanity: reject impossible prices
            if price <= 0 or price > 1e12:
                continue
            return price
        except:
            continue
    return None

# ───────────────────────── MAIN SCANNER ─────────────────────────
def main():
    print(f"\n>>> WILD TOKEN SCANNER (LIVE) <<<")
    print(f"Bot Wallet: {BOT_ADDRESS}")
    print(f"Watching {len(PAIRS)} pairs on Base  |  Safety Mode: ON")
    print(f"Gas per failed tx: ~$0.01  |  Your ETH covers ~600 attempts")
    print("-" * 55)

    best_gap = 0
    best_pair = ""

    while True:
        try:
            w3 = get_w3()
            if not w3:
                print("RPC down. Retrying...")
                time.sleep(5)
                continue

            for name_a, name_b in PAIRS:
                addr_a, addr_b = TOKENS[name_a], TOKENS[name_b]

                aero = get_aero_price(addr_a, addr_b, w3)
                uni  = get_uni_price(addr_a, addr_b, w3)

                if aero and uni and aero > 0 and uni > 0:
                    p_gap = (abs(aero - uni) / min(aero, uni)) * 100
                    tag = f"{name_a}/{name_b}"

                    if p_gap > best_gap:
                        best_gap = p_gap
                        best_pair = tag

                    if p_gap > 1.0:
                        direction = "BUY on Aero, SELL on Uni" if aero < uni else "BUY on Uni, SELL on Aero"
                        print(f"[{time.strftime('%H:%M:%S')}] {tag:14} | Gap: {p_gap:6.2f}% 🔥 {direction}")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] {tag:14} | Gap: {p_gap:6.4f}%")

            print(f"--- Best ever: {best_pair} at {best_gap:.2f}% ---")
            time.sleep(8)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
