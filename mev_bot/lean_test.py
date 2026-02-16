from web3 import Web3
import time, os, json

# Use the fast Alchey RPC
RPC_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

TOKENS = {
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "AERO": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
}

PAIRS = [("USDC", "WETH"), ("USDC", "AERO")]

def test():
    print("Starting Lean Diagnostic...")
    for n1, n2 in PAIRS:
        t1, t2 = Web3.to_checksum_address(TOKENS[n1]), Web3.to_checksum_address(TOKENS[n2])
        print(f"Checking {n1}/{n2}...")
        
        # Aero
        fac = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pool_addr = fac.functions.getPool(t1, t2, False).call()
        print(f"Aero Pool: {pool_addr}")
        
    print("Diagnostic Complete.")

if __name__ == "__main__":
    test()
