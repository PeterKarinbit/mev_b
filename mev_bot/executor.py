"""
╔══════════════════════════════════════════════════════╗
║         MEV FLASH ARBITRAGE BOT - V3 (SHIELD)        ║
║         Owner: 0xF2B9...AdDC                         ║
║         Mode: Triple-Layer Stability                ║
╚══════════════════════════════════════════════════════╝
"""
from web3 import Web3
import json, time, os, asyncio, requests, eth_abi
from dotenv import load_dotenv

load_dotenv()
load_dotenv("mev_bot/.env")

PRIVATE_KEY      = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS      = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
TG_TOKEN         = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT          = os.getenv("TELEGRAM_CHAT_ID")

# ───────────────────────── DYNAMIC CONFIG ─────────────────────────
MIN_GAP_PERCENT = 0.8  # Default
BASE_PRIORITY_FEE = 0.05 # Gwei
MAX_PRIORITY_FEE = 2.0   # Gwei (for $10+ profit)

# Volatility Tracking
WETH_PRICE_HISTORY = [] # Stores (timestamp, price)
VOLATILITY_MODE = False

# ───────────────────────── STABLE RPC ROTATION ─────────────────────────
# Using stable, free-tier primary nodes
RPC_URLS = [
    "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2", # Alchemy (Private)
    "https://base.llamarpc.com",                                   # Llama (Reliable)
    "https://1rpc.io/base",                                        # 1RPC (Privacy oriented)
    "https://mainnet.base.org"                                     # Public (Failover)
]
rpc_idx = 0

def get_w3():
    global rpc_idx
    for _ in range(len(RPC_URLS)):
        url = RPC_URLS[rpc_idx]
        rpc_idx = (rpc_idx + 1) % len(RPC_URLS)
        try:
            w = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 8}))
            if w.is_connected(): return w
        except: continue
    return None

# Rest of the optimized code...
# [Parallel scanning logic preserved for performance]
# ...
TOKENS = {
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "AERO": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
    "BRETT": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
    "DEGEN": "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
    "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
    "TOSHI": "0x8544fe9d190fd7ec52860abbf45088e81ee24a8c",
    "MOCHI": "0xf6e932ca12afa26665dc4dde7e27be02a7c02e50",
    "TYBG": "0x0d97f261b1e88845184f678e2d1e7a98D9FD38dE",
    "MIGGLES": "0xb1a03eda10342529bbf8eb700a06c60441fef25d",
    "KEYCAT": "0x9a26f5433671751c3276a065f57e5a02d2817973",
}
PAIRS = [
    ("USDC", "WETH", "HIGH"), ("USDC", "AERO", "HIGH"), ("WETH", "BRETT", "WILD"),
    ("WETH", "VIRTUAL", "WILD"), ("WETH", "DEGEN", "WILD"), ("WETH", "TOSHI", "WILD"),
    ("WETH", "MOCHI", "WILD"), ("WETH", "TYBG", "WILD"), ("WETH", "MIGGLES", "WILD"),
    ("WETH", "KEYCAT", "WILD"),
]

RESERVES_ABI = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
V3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"token","type":"address"}],"type":"function"}]
ERC20_ABI = [{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
EXEC_ABI = [{"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"params","type":"bytes"}],"name":"execute","outputs":[],"type":"function"}]

DEC_CACHE = {}

def get_dec(addr, w3):
    if addr not in DEC_CACHE: DEC_CACHE[addr] = w3.eth.contract(address=addr, abi=ERC20_ABI).functions.decimals().call()
    return DEC_CACHE[addr]

def get_aero_price(token_a, token_b, w3):
    try:
        f = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pa = f.functions.getPool(token_a, token_b, False).call()
        if int(pa, 16) == 0: return None
        pool = w3.eth.contract(address=pa, abi=RESERVES_ABI)
        res = pool.functions.getReserves().call()
        t0 = pool.functions.token0().call()
        da, db = get_dec(token_a, w3), get_dec(token_b, w3)
        ra, rb = (res[0], res[1]) if t0.lower() == token_a.lower() else (res[1], res[0])
        return (rb / 10**db) / (ra / 10**da)
    except: return None

def get_uni_price(token_a, token_b, w3):
    for f in [500, 3000, 10000]:
        try:
            fac = w3.eth.contract(address="0x33128a8fC17869897dcE68Ed026d694621f6FDfD", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"f","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
            pa = fac.functions.getPool(token_a, token_b, f).call()
            if int(pa, 16) == 0: continue
            pool = w3.eth.contract(address=pa, abi=V3_POOL_ABI)
            sq = pool.functions.slot0().call()[0]
            if sq == 0: continue
            da, db = get_dec(token_a, w3), get_dec(token_b, w3)
            pr = (sq / (2**96)) ** 2
            try: t0 = pool.functions.token0().call()
            except: t0 = pool.functions.token().call() # Fallback for some ABIs
            p = pr*(10**da)/(10**db) if t0.lower()==token_a.lower() else (1.0/pr)*(10**db)/(10**da)
            return p, f
        except: continue
    return None, None

async def check_volatility(w3):
    global MIN_GAP_PERCENT, VOLATILITY_MODE
    try:
        current_price = get_aero_price(TOKENS["WETH"], TOKENS["USDC"], w3)
        if not current_price: return
        now = time.time()
        WETH_PRICE_HISTORY.append((now, current_price))
        
        # Keep only last 1 hour of history
        one_hour_ago = now - 3600
        while WETH_PRICE_HISTORY and WETH_PRICE_HISTORY[0][0] < one_hour_ago:
            WETH_PRICE_HISTORY.pop(0)

        if len(WETH_PRICE_HISTORY) > 10:
            old_price = WETH_PRICE_HISTORY[0][1]
            change = abs(current_price - old_price) / old_price * 100
            
            if change > 3.0: # 3% move in 1 hour = Aggressive Mode
                if not VOLATILITY_MODE:
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": f"🔥 VOLATILITY DETECTED: {change:.2f}% move. Switching to AGGRESSIVE MODE (Gap: 0.5%)"})
                MIN_GAP_PERCENT = 0.5
                VOLATILITY_MODE = True
            else:
                if VOLATILITY_MODE:
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": "🛡️ Market Stabilized. Returning to SHIELD MODE (Gap: 0.8%)"})
                MIN_GAP_PERCENT = 0.8
                VOLATILITY_MODE = False
    except: pass

async def scan(w3):
    tasks = []
    for n1, n2, diff in PAIRS:
        addr1, addr2 = TOKENS[n1], TOKENS[n2]
        async def check(n1, n2, a1, a2, diff):
            try:
                aero, uni_data = get_aero_price(a1, a2, w3), get_uni_price(a1, a2, w3)
                u, f = uni_data
                if aero and u:
                    gap = (abs(aero - u) / min(aero, u)) * 100
                    if gap > MIN_GAP_PERCENT:
                        amt = 500 if diff == "HIGH" else 50
                        fire_trade(w3, n1, n2, a1, amt * 10**get_dec(a1, w3), a2, f, aero < u, gap)
            except: pass
        tasks.append(check(n1, n2, addr1, addr2, diff))
    await asyncio.gather(*tasks)

def fire_trade(w3, n1, n2, a1, raw, a2, f, buyAero, gap):
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=EXEC_ABI)
    params = eth_abi.encode(['bool', 'address', 'uint24', 'bool', 'address'], [False, a2, f, buyAero, "0x0000000000000000000000000000000000000000"])
    
    # DYNAMIC PRIORITY FEE (Nitro)
    # Higher gap = Higher probability of profit = Higher priority 'tip'
    priority_tip = BASE_PRIORITY_FEE
    if gap > 2.0: priority_tip = 0.5
    if gap > 5.0: priority_tip = 1.5 # Go full aggro for big gaps
    
    tx = contract.functions.execute(a1, raw, params).build_transaction({
        'from': BOT_ADDRESS, 'nonce': w3.eth.get_transaction_count(BOT_ADDRESS), 'gas': 800000,
        'maxFeePerGas': int(w3.eth.gas_price * 1.5), 
        'maxPriorityFeePerGas': w3.to_wei(str(priority_tip), 'gwei')
    })
    try:
        w3.eth.call(tx)
        h = w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, PRIVATE_KEY).raw_transaction)
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": f"🚀 STRIKE: {n1}/{n2} Gap: {gap:.2f}% | Tip: {priority_tip} Gwei"})
    except: pass

async def main():
    print("SHIELD MODE ACTIVE: Volatility Sensors & Auto-Nitro Enabled.")
    while True:
        w = get_w3()
        if w: 
            await check_volatility(w) # Update sensors
            await scan(w) # Target hunt
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
