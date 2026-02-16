"""
╔══════════════════════════════════════════════════════╗
║         MEV DIAGNOSTIC BOT - TEST MODE               ║
║         Goal: Zero-Gas Performance Analysis          ║
║         Tests: Simulation, Volatility, Competition   ║
╚══════════════════════════════════════════════════════╝
"""
from web3 import Web3
import json, time, os, asyncio, requests, eth_abi
from dotenv import load_dotenv

load_dotenv()
load_dotenv("mev_bot/.env")

# Config
BOT_ADDRESS      = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
RPC_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Test Flags
TEST_MODE = True # NEVER sends live transactions

# Stats Trackers
stats = {
    "total_scans": 0,
    "opportunities_found": 0,
    "simulations_passed": 0,
    "total_est_profit": 0,
    "competitors_spotted": 0,
    "pair_volatility": {},
    "logs": []
}

# Assets
TOKENS = {
    "WETH": Web3.to_checksum_address("0x4200000000000000000000000000000000000006"),
    "USDC": Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
    "AERO": Web3.to_checksum_address("0x940181a94a35a4569e4529a3cdfb74e38fd98631"),
    "BRETT": Web3.to_checksum_address("0x532f27101965dd16442E59d40670FaF5eBB142E4"),
    "DEGEN": Web3.to_checksum_address("0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed"),
    "VIRTUAL": Web3.to_checksum_address("0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"),
    "TOSHI": Web3.to_checksum_address("0x8544fe9d190fd7ec52860abbf45088e81ee24a8c"),
    "MOCHI": Web3.to_checksum_address("0xf6e932ca12afa26665dc4dde7e27be02a7c02e50"),
}
PAIRS = [
    ("USDC", "WETH", "HIGH"), ("USDC", "AERO", "HIGH"), ("WETH", "BRETT", "WILD"),
    ("WETH", "VIRTUAL", "WILD"), ("WETH", "DEGEN", "WILD"), ("WETH", "TOSHI", "WILD"),
]

# ABIs
RESERVES_ABI = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
V3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"token","type":"address"}],"type":"function"}]
EXEC_ABI = [{"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"params","type":"bytes"}],"name":"execute","outputs":[],"type":"function"}]

def log_event(event):
    print(f"[{time.strftime('%H:%M:%S')}] {event}")
    stats["logs"].append({"time": time.time(), "event": event})

DEC_CACHE = {}
def get_dec(addr):
    if addr not in DEC_CACHE:
        log_event(f"Fetching decimals for {addr}...")
        try:
            DEC_CACHE[addr] = w3.eth.contract(address=addr, abi=ERC20_ABI).functions.decimals().call()
            log_event(f"Decimals: {DEC_CACHE[addr]}")
        except: 
            log_event("Decimals fetch failed, defaulting to 18")
            DEC_CACHE[addr] = 18
    return DEC_CACHE[addr]

def get_aero_price(token_a, token_b):
    try:
        log_event(f"Aerodrome: Fetching pool for {token_a} and {token_b}...")
        f = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pa = f.functions.getPool(token_a, token_b, False).call()
        log_event(f"Aerodrome Pool Address: {pa}")
        if int(pa, 16) == 0: return None
        pool = w3.eth.contract(address=pa, abi=RESERVES_ABI)
        log_event("Aerodrome: Fetching reserves...")
        res = pool.functions.getReserves().call()
        log_event(f"Reserves: {res}")
        t0 = pool.functions.token0().call()
        da, db = get_dec(token_a), get_dec(token_b)
        ra, rb = (res[0], res[1]) if t0.lower() == token_a.lower() else (res[1], res[0])
        return (rb / 10**db) / (ra / 10**da)
    except Exception as e:
        log_event(f"Aero Error: {e}")
        return None

def get_uni_price(token_a, token_b):
    for f in [500, 3000, 10000]:
        try:
            fac = w3.eth.contract(address="0x33128a8fC17869897dcE68Ed026d694621f6FDfD", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"f","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
            pa = fac.functions.getPool(token_a, token_b, f).call()
            if int(pa, 16) == 0: continue
            pool = w3.eth.contract(address=pa, abi=V3_POOL_ABI)
            sq = pool.functions.slot0().call()[0]
            da, db = get_dec(token_a), get_dec(token_b)
            pr = (sq / (2**96)) ** 2
            try: t0 = pool.functions.token0().call()
            except: t0 = pool.functions.token().call()
            p = pr*(10**da)/(10**db) if t0.lower()==token_a.lower() else (1.0/pr)*(10**db)/(10**da)
            return p, f
        except: continue
    return None, None

def check_competition(block_num, pair_name):
    try:
        block = w3.eth.get_block(block_num, full_transactions=True)
        for tx in block.transactions:
            if tx.to and tx.to.lower() == CONTRACT_ADDRESS.lower():
                stats["competitors_spotted"] += 1
                return True
    except: pass
    return False

async def check_liquidations():
    AAVE_POOL = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
    AAVE_ABI = [{"inputs":[{"name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"name":"totalCollateralBase","type":"uint256"},{"name":"totalDebtBase","type":"uint256"},{"name":"availableBorrowsBase","type":"uint256"},{"name":"currentLiquidationThreshold","type":"uint256"},{"name":"ltv","type":"uint256"},{"name":"healthFactor","type":"uint256"}],"type":"function"}]
    aave = w3.eth.contract(address=AAVE_POOL, abi=AAVE_ABI)
    
    # Check a few known addresses or the ones in targets.txt
    targets = []
    if os.path.exists("mev_bot/targets.txt"):
        with open("mev_bot/targets.txt", "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    
    for user in targets[:10]:
        try:
            d = aave.functions.getUserAccountData(Web3.to_checksum_address(user)).call()
            hf = d[5] / 1e18
            if hf < 1.05:
                log_event(f"💀 LIQ OPPORTUNITY: {user[:10]} HF: {hf:.4f}")
        except: continue

async def diagnostic_scan():
    stats["total_scans"] += 1
    # log_event("Starting Liquidation Check...")
    # await check_liquidations()
    log_event("Starting Pair Scan...")
    for n1, n2, diff in PAIRS:
        log_event(f"Checking {n1}/{n2}...")
        a1, a2 = TOKENS[n1], TOKENS[n2]
        
        start_p = time.time()
        aero = get_aero_price(a1, a2)
        log_event(f"Aero Price: {aero} (took {(time.time()-start_p)*1000:.0f}ms)")
        
        start_u = time.time()
        uni_data = get_uni_price(a1, a2)
        uni, fee = uni_data if uni_data else (None, None)
        log_event(f"Uni Price: {uni} (took {(time.time()-start_u)*1000:.0f}ms)")
        
        if aero and uni:
            gap = (abs(aero - uni) / min(aero, uni)) * 100
            if gap > 0.5: # Lowered threshold for diagnostics
                stats["opportunities_found"] += 1
                log_event(f"Findable Gap: {n1}/{n2} at {gap:.2f}%")
                
                # Test 1 & 3: Simulation Check
                contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=EXEC_ABI)
                amt_raw = 500 * 10**6 if n1 == "USDC" else 1 * 10**18
                params = eth_abi.encode(['bool', 'address', 'uint24', 'bool', 'address'], [False, a2, fee, aero < uni, "0x0000000000000000000000000000000000000000"])
                
                try:
                    # SIMULATION ONLY
                    start_sim = time.time()
                    w3.eth.call({
                        'from': BOT_ADDRESS,
                        'to': CONTRACT_ADDRESS,
                        'data': contract.encode_abi("execute", [a1, amt_raw, params])
                    })
                    end_sim = time.time()
                    stats["simulations_passed"] += 1
                    log_event(f"✅ SIM PASSED: {n1}/{n2} in {(end_sim-start_sim)*1000:.0f}ms")
                except Exception as e:
                    log_event(f"❌ SIM FAILED: {n1}/{n2} - {str(e)[:50]}")
                
                # Test 4: Competition
                latest = w3.eth.block_number
                if check_competition(latest, f"{n1}/{n2}"):
                    log_event(f"⚠️ COMPETITOR DETECTED in Block {latest}")

async def main():
    log_event("DIAGNOSTIC BOT STARTED (TEST MODE)")
    try:
        while True:
            await diagnostic_scan()
            # Save stats every cycle
            with open("diagnostic_stats.json", "w") as f:
                json.dump(stats, f, indent=4)
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        log_event("SUMMARY:")
        log_event(f"Total Scans: {stats['total_scans']}")
        log_event(f"Total Opportunities: {stats['opportunities_found']}")
        log_event(f"Total Sims Passed: {stats['simulations_passed']}")
        log_event(f"Competitors Noticed: {stats['competitors_spotted']}")

if __name__ == "__main__":
    asyncio.run(main())
