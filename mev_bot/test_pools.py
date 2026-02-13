from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

AERO_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
WETH = "0x4200000000000000000000000000000000000006"

# Try AERO/USDC
AERO = "0x940181a94a35a4569e4529a3cdfb74e38fd98631"

FACTORY_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"bool","name":"stable","type":"bool"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')

def test():
    factory = w3.eth.contract(address=AERO_FACTORY, abi=FACTORY_ABI)
    
    # Try different combinations
    pools = [
        ("WETH/USDC", factory.functions.getPool(WETH, USDC, False).call()),
        ("AERO/USDC", factory.functions.getPool(AERO, USDC, False).call()),
        ("BRETT/WETH", factory.functions.getPool("0x532f27101965dd16442E59d40670FaF5eBB142E4", WETH, False).call())
    ]
    
    for name, addr in pools:
        print(f"{name} Pool: {addr}")

if __name__ == "__main__":
    test()
