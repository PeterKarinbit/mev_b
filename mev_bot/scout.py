"""
        MASTER SCOUT - AAVE V3 USER DISCOVERY
        Scans blockchain history to find all borrowers.
"""
from web3 import Web3
import json, os

RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

POOL_ADDR = Web3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5")
BORROW_EVENT_SIG = "0xb53027b4096d2f3db98a883a48e89f899e32a67a0ee9d34e64f9f25a98bf793c"

def scout_history(blocks_to_scan=20000):
    print(f"Scouting the last {blocks_to_scan} blocks for borrowers...")
    current = w3.eth.block_number
    step = 2000 # Scan in chunks to avoid RPC limits
    
    all_borrowers = set()
    
    for start in range(current - blocks_to_scan, current, step):
        end = start + step
        print(f"  Scanning blocks {start} to {end}...")
        try:
            logs = w3.eth.get_logs({
                "fromBlock": start,
                "toBlock": end,
                "address": POOL_ADDR,
                "topics": [BORROW_EVENT_SIG]
            })
            for log in logs:
                user = "0x" + log['topics'][2].hex()[-40:]
                all_borrowers.add(Web3.to_checksum_address(user))
        except Exception as e:
            print(f"  Chunk failed: {e}")
            continue

    print(f"\n✅ Discovery Complete! Found {len(all_borrowers)} unique borrowers.")
    
    # Save to file
    with open("targets.txt", "w") as f:
        for addr in all_borrowers:
            f.write(addr + "\n")
    print(f"Targets saved to targets.txt")

if __name__ == "__main__":
    scout_history(50000) # Scan roughly last 24 hours of activity
