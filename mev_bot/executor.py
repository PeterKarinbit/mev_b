"""
╔══════════════════════════════════════════════════════╗
║         MEV FLASH ARBITRAGE BOT - V2 (POWER)         ║
║         Owner: 0xF2B9...AdDC                         ║
║         Features: Async, Telegram, Dynamic Sniping   ║
╚══════════════════════════════════════════════════════╝
"""
from web3 import Web3
import json, time, os, asyncio, requests
from dotenv import load_dotenv

load_dotenv()

# ───────────────────────── CONFIG ─────────────────────────
PRIVATE_KEY      = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS      = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
TG_TOKEN         = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT          = os.getenv("TELEGRAM_CHAT_ID")

MIN_GAP_PERCENT = 0.8

def send_tg(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT, "text": f"🚀 MEV: {msg}"}, timeout=5)
    except: pass

# ───────────────────────── RPC ─────────────────────────
RPC_URLS = ["https://mainnet.base.org", "https://base.llamarpc.com", "https://1rpc.io/base"]
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

# ───────────────────────── ASSETS ─────────────────────────
AERO_FACTORY   = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
UNI_FACTORY    = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"

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
BORROW_CONFIG = {"HIGH": 500, "WILD": 50}
PAIRS = [
    ("USDC", "WETH", "HIGH"), ("USDC", "AERO", "HIGH"), 
    ("WETH", "BRETT", "WILD"), ("WETH", "VIRTUAL", "WILD"), 
    ("WETH", "DEGEN", "WILD"), ("WETH", "TOSHI", "WILD"),
    ("WETH", "MOCHI", "WILD"), ("WETH", "TYBG", "WILD"), 
    ("WETH", "MIGGLES", "WILD"), ("WETH", "KEYCAT", "WILD"),
]

# ABIs
RESERVES_ABI = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
V3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
ERC20_ABI = [{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
EXEC_ABI = [{"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"params","type":"bytes"}],"name":"execute","outputs":[],"type":"function"}]

DEC_CACHE = {}
POOL_CACHE = {}
FAILED_COOLDOWN = {}

def get_dec(addr, w3):
    if addr not in DEC_CACHE:
        DEC_CACHE[addr] = w3.eth.contract(address=addr, abi=ERC20_ABI).functions.decimals().call()
    return DEC_CACHE[addr]

def get_aero_price(token_a, token_b, w3):
    try:
        ck = ("aero", token_a, token_b)
        if ck in POOL_CACHE: pa = POOL_CACHE[ck]
        else:
            f = w3.eth.contract(address=AERO_FACTORY, abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
            pa = f.functions.getPool(token_a, token_b, False).call()
            if int(pa, 16) == 0: return None
            POOL_CACHE[ck] = pa
        pool = w3.eth.contract(address=pa, abi=RESERVES_ABI)
        res = pool.functions.getReserves().call()
        t0 = pool.functions.token0().call()
        da, db = get_dec(token_a, w3), get_dec(token_b, w3)
        ra, rb = (res[0], res[1]) if t0.lower() == token_a.lower() else (res[1], res[0])
        if ra == 0: return None
        return (rb / 10**db) / (ra / 10**da)
    except: return None

def get_uni_price(token_a, token_b, w3):
    for fee in [500, 3000, 10000]:
        try:
            ck = ("uni", token_a, token_b, fee)
            if ck in POOL_CACHE: pa = POOL_CACHE[ck]
            else:
                f = w3.eth.contract(address=UNI_FACTORY, abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"f","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
                pa = f.functions.getPool(token_a, token_b, fee).call()
                if int(pa, 16) == 0: continue
                POOL_CACHE[ck] = pa
            pool = w3.eth.contract(address=pa, abi=V3_POOL_ABI)
            sq = pool.functions.slot0().call()[0]
            if sq == 0: continue
            da, db = get_dec(token_a, w3), get_dec(token_b, w3)
            pr = (sq / (2**96)) ** 2
            t0 = pool.functions.token0().call()
            p = pr * (10**da) / (10**db) if t0.lower() == token_a.lower() else (1.0/pr) * (10**db) / (10**da)
            return p, fee
        except: continue
    return None, None

import eth_abi

def fire_trade(w3, name_a, name_b, asset, amount_raw, token_b_addr, fee, buyAero, est_p):
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=EXEC_ABI)
    params = eth_abi.encode(['bool', 'address', 'uint24', 'bool', 'address'], [False, token_b_addr, fee, buyAero, "0x0000000000000000000000000000000000000000"])
    
    p_fee = w3.to_wei('0.1', 'gwei')
    tx = contract.functions.execute(asset, amount_raw, params).build_transaction({
        'from': BOT_ADDRESS,
        'nonce': w3.eth.get_transaction_count(BOT_ADDRESS),
        'gas': 800000,
        'maxFeePerGas': w3.eth.gas_price + p_fee,
        'maxPriorityFeePerGas': p_fee,
    })
    
    try:
        w3.eth.call(tx)
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"  [TX] Sent! {h.hex()}")
        send_tg(f"🔥 TRADE FIRED: {name_a}/{name_b} | Est: ${est_p:.2f}")
        return True
    except Exception as e:
        print(f"  [SIM] Fail: {e}")
        return False

async def scan_pair(n1, n2, diff, w3):
    pid = f"{n1}/{n2}"
    if pid in FAILED_COOLDOWN and time.time() < FAILED_COOLDOWN[pid]: return
    
    a1, a2 = TOKENS[n1], TOKENS[n2]
    aero, uni_data = await asyncio.gather(
        asyncio.to_thread(get_aero_price, a1, a2, w3),
        asyncio.to_thread(get_uni_price, a1, a2, w3)
    )
    u, f = uni_data
    if aero and u:
        gap = (abs(aero - u) / min(aero, u)) * 100
        if gap >= MIN_GAP_PERCENT:
            print(f"\n[{time.strftime('%H:%M:%S')}] 🔥 {pid} GAP: {gap:.2f}%")
            b_amt = BORROW_CONFIG[diff]
            est_p = (b_amt * (gap / 100)) - 3.50
            if est_p > 0.50:
                if not fire_trade(w3, n1, n2, a1, b_amt * 10**get_dec(a1, w3), a2, f, aero < u, est_p):
                    FAILED_COOLDOWN[pid] = time.time() + 300
    print(".", end="", flush=True)

async def main():
    print(__doc__)
    while True:
        try:
            w3 = get_w3()
            if w3:
                tasks = [scan_pair(n1, n2, d, w3) for n1, n2, d in PAIRS]
                await asyncio.gather(*tasks)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Loop error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
