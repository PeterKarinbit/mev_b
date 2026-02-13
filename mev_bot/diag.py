from web3 import Web3
import json

# Your Alchemy Key
ALCHEMY_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

def test():
    if not w3.is_connected():
        print("Alchemy Connection Failed!")
        return
    
    # Aerodrome Factory
    FACTORY = Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da")
    ABI = [{"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
    
    WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
    USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
    
    contract = w3.eth.contract(address=FACTORY, abi=ABI)
    pool = contract.functions.getPool(WETH, USDC, False).call()
    print(f"Pool Address: {pool}")

if __name__ == "__main__":
    test()
