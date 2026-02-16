"""
╔══════════════════════════════════════════════════════╗
║         MEV DIAGNOSTIC BOT - STABLE VERSION          ║
╚══════════════════════════════════════════════════════╝
"""
from web3 import Web3
import json, time, os, asyncio, requests, eth_abi
from dotenv import load_dotenv

load_dotenv()
load_dotenv("mev_bot/.env")

RPC_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

BOT_ADDRESS = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))

TOKENS = {k: Web3.to_checksum_address(v) for k, v in {
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "AERO": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
    "BRETT": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
    "DEGEN": "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
    "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
}.items()}

PAIRS = [("USDC", "WETH"), ("USDC", "AERO"), ("WETH", "BRETT"), ("WETH", "DEGEN"), ("WETH", "VIRTUAL")]

stats = {"total_scans": 0, "gaps_found": 0, "sims_passed": 0, "sims_failed": 0, "competitors": 0}

ABI_POOL = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
ABI_FAC = [{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
ABI_UNI = [{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"f","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
ABI_EXEC = [{"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"params","type":"bytes"}],"name":"execute","outputs":[],"type":"function"}]

def get_price_aero(t1, t2):
    try:
        f = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=ABI_FAC)
        pa = f.functions.getPool(t1, t2, False).call()
        if int(pa, 16) == 0: return None
        res = w3.eth.contract(address=pa, abi=ABI_POOL).functions.getReserves().call()
        # Simple ratio for diagnostic
        return res[1]/res[0] if int(pa, 16)%2==0 else res[0]/res[1] # Dummy ratio check
    except: return None

async def run_diag():
    print(f"[{time.strftime('%H:%M:%S')}] Scan #{stats['total_scans']}...")
    stats['total_scans'] += 1
    for n1, n2 in PAIRS:
        p = get_price_aero(TOKENS[n1], TOKENS[n2])
        if p:
            print(f"  {n1}/{n2} found price.")
            stats['gaps_found'] += 1
            # Simulate
            try:
                # Dummy params for simulation test
                amt = 100 * 10**6 if n1=="USDC" else 10**17
                params = eth_abi.encode(['bool', 'address', 'uint24', 'bool', 'address'], [False, TOKENS[n2], 3000, True, "0x0000000000000000000000000000000000000000"])
                w3.eth.call({'from': BOT_ADDRESS, 'to': CONTRACT_ADDRESS, 
                             'data': w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI_EXEC).encode_abi("execute", [TOKENS[n1], amt, params])})
                stats['sims_passed'] += 1
                print(f"  ✅ {n1}/{n2} SIM PASSED")
            except Exception as e:
                stats['sims_failed'] += 1
                print(f"  ❌ {n1}/{n2} SIM REVERTED: {str(e)[:40]}")

async def main():
    print("MEV Diagnostic Active. Running for 3 cycles...")
    for _ in range(3):
        await run_diag()
        with open("diagnostic_results.json", "w") as f: json.dump(stats, f)
        await asyncio.sleep(2)
    print("Final Results:", stats)

if __name__ == "__main__":
    asyncio.run(main())
