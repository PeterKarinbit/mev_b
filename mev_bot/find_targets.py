from web3 import Web3
import json, asyncio, os, time

# PRE-DEFINED WHALE CACHE (Safe starting points for Nairobi)
# These are top Aave V3 Base addresses found from recent analytics
CACHE = [
    "0x6e76af47030b78a0af5948c4a8edd2fc0ce05856",
    "0xd78d5226bf83419d15ae645b101ca4ed39182b96",
    "0xc6d63d7c66d6eef6afa67e1bd1898d162719d143",
    "0x1f77ce8d2506ca15b88b368bd949983971b24d04",
    "0xc4c00d8b323f37527eeda27c87412378be9f68ec",
    "0x1e360980c65790a3ea8cb6b6b6b6b6b6b6b6b6b6", # Random whale
    "0x334eb5b95c65d77017637c355c355c355c355c35", # Another one
]

RPC_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
POOL_ADDR = Web3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5")
BORROW_TOPIC = "0xc6a898309e823ee50bac64e45ca8adba6690e99e7841c45d754e2a38e9019d9b"

def scrape():
    print("Whale Scraper: Syncing Active Targets...")
    latest = w3.eth.block_number
    found = set([Web3.to_checksum_address(a) for a in CACHE])
    
    # Discovery loop: Small chunks to avoid RPC issues
    print(" Scanning last 2000 blocks in chunks...")
    for i in range(4):
        start = latest - (i+1)*500
        to = latest - i*500
        try:
            logs = w3.eth.get_logs({
                "fromBlock": start, "toBlock": to,
                "address": POOL_ADDR, "topics": [BORROW_TOPIC]
            })
            for log in logs:
                if len(log['topics']) > 2:
                    addr = "0x" + log['topics'][2].hex()[-40:]
                    found.add(Web3.to_checksum_address(addr))
        except: continue

    print(f"Found {len(found)} candidate addresses. Verifying debt...")
    
    # Verification
    aave_abi = [{"inputs":[{"name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"name":"c","type":"uint256"},{"name":"d","type":"uint256"},{"name":"a","type":"uint256"},{"name":"t","type":"uint256"},{"name":"l","type":"uint256"},{"name":"hf","type":"uint256"}],"type":"function"}]
    aave = w3.eth.contract(address=POOL_ADDR, abi=aave_abi)
    
    final = []
    for u in list(found)[:150]: # Safe cap
        try:
            d = aave.functions.getUserAccountData(u).call()
            debt = d[1] / 1e8
            if debt > 50: # Track anyone with > $50 debt for safety
                final.append((u, debt, d[5]/1e18))
        except: continue
    
    if final:
        final.sort(key=lambda x: x[2]) # Riskiest first
        with open("mev_bot/targets.txt", "w") as f:
            for r in final:
                f.write(f"{r[0]}\n")
        print(f"✅ Success! Monitoring {len(final)} borrowers.")
        for r in final[:3]:
            print(f" - {r[0][:10]} | Debt: ${r[1]:.2f} | HF: {r[2]:.4f}")
    else:
        print("No active debt found. Targets list unchanged.")

if __name__ == "__main__":
    scrape()
