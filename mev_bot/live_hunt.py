from web3 import Web3
import json
import time
import os
from dotenv import load_dotenv

# --- SECURITY & CONFIG ---
load_dotenv()
PRIVATE_KEY = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS = os.getenv("BOT_ADDRESS")

# Use multiple RPCs for reliability
RPC_URLS = [
    "https://mainnet.base.org",
    "https://base.llamarpc.com",
    "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
]

def get_w3():
    for url in RPC_URLS:
        w3 = Web3(Web3.HTTPProvider(url))
        if w3.is_connected():
            return w3
    return None

w3 = get_w3()

# Token Addresses on Base
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")

# Pool Addresses
UNI_V3_POOL = Web3.to_checksum_address("0xd0b53d9277642d899df5c87a3966a349a798f224")
AERO_FACTORY = Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da")

# ABIs
V3_POOL_ABI = json.loads('[{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]')
AERO_FACTORY_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"bool","name":"stable","type":"bool"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')
V2_POOL_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"type":"function"}]')

def get_prices():
    # Uniswap V3
    uni_contract = w3.eth.contract(address=UNI_V3_POOL, abi=V3_POOL_ABI)
    sqrtPriceX96 = uni_contract.functions.slot0().call()[0]
    uni_p = ((sqrtPriceX96 / (2**96)) ** 2) * 10**12
    
    # Aerodrome
    factory = w3.eth.contract(address=AERO_FACTORY, abi=AERO_FACTORY_ABI)
    pool_addr = factory.functions.getPool(USDC, WETH, False).call()
    pool = w3.eth.contract(address=pool_addr, abi=V2_POOL_ABI)
    res = pool.functions.getReserves().call()
    aero_p = (res[1] / 10**6) / (res[0] / 10**18)
    
    return aero_p, uni_p

def run_sniffer():
    print(f"\n>>> BOT LIVE ON BASE NETWORK <<<")
    print(f"Address: {BOT_ADDRESS}")
    print(f"Strategy: Zero-Capital Flash Loan Arbitrage")
    print(f"Safe from pigs. Hunting now...\n")
    
    # Limit to 50 iterations for safety in this session
    iterations = 0
    while iterations < 50:
        try:
            aero, uni = get_prices()
            gap = abs(aero - uni)
            p_gap = (gap / min(aero, uni)) * 100
            
            print(f"[{time.strftime('%H:%M:%S')}] Aero: ${aero:.2f} | Uni: ${uni:.2f} | Gap: {p_gap:.4f}%")
            
            if p_gap > 0.5: # 0.5% threshold for real execution
                print("\n" + "!"*60)
                print(f"PROFIT GAP DETECTED: {p_gap:.2f}%")
                print("In a live execution, this would trigger the Flash Loan contract.")
                print("Current setting: OBSERVER MODE (Safety First)")
                print("!"*60 + "\n")
            
            iterations += 1
            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_sniffer()
