from web3 import Web3
from eth_abi import encode
import json

w3 = Web3(Web3.HTTPProvider('https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2'))

WETH = Web3.to_checksum_address('0x4200000000000000000000000000000000000006')
DEGEN = Web3.to_checksum_address('0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed')

# Pool ABI for slot0
POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"stateMutability":"view","type":"function"}]

# Uni V3 DEGEN/WETH 0.3%
UNI_POOL = Web3.to_checksum_address('0xc9034c3E7F58003E6ae0C8438e7c8f4598d5ACAA')
# Pan V3 DEGEN/WETH 0.25%
PAN_POOL = Web3.to_checksum_address('0xFa98B3C0526C9bf96787e5797e87910f1175af0F')

def get_price(pool_addr, name):
    pool = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
    slot0 = pool.functions.slot0().call()
    sqrtPriceX96 = slot0[0]
    # Price = (sqrtPriceX96 / 2^96)^2 * 10^(dec0 - dec1)
    # WETH < DEGEN? 0x4200... < 0x4ed4... YES.
    # dec0 = 18 (WETH), dec1 = 18 (DEGEN)
    price_raw = (sqrtPriceX96 / (2**96))**2
    # price = DEGEN per WETH
    print(f"{name} Price: {price_raw:.2f} DEGEN/WETH")
    return price_raw

print("Checking Live Prices...")
p1 = get_price(UNI_POOL, "Uniswap")
p2 = get_price(PAN_POOL, "PancakeSwap")

gap = abs(p1 - p2) / min(p1, p2) * 100
print(f"Current Gap: {gap:.3f}%")
