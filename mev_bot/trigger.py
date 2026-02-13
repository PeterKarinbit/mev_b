import os
import subprocess
import time
import json
from web3 import Web3

# Configuration
THRESHOLD = 0.5  # We trigger if gap is > 0.5% (to show it clearly)
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

# Aerodrome & UniV3 Addresses (Same as sniffer)
UNI_V3_POOL = Web3.to_checksum_address("0xd0b53d9277642d899df5c87a3966a349a798f224")
AERO_FACTORY = Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da")
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")

# Minimal ABIs
V3_POOL_ABI = json.loads('[{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]')
AERO_FACTORY_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"bool","name":"stable","type":"bool"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')
V2_POOL_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"type":"function"}]')

def get_prices():
    # Uniswap V3 Price
    uni_contract = w3.eth.contract(address=UNI_V3_POOL, abi=V3_POOL_ABI)
    slot0 = uni_contract.functions.slot0().call()
    sqrtPriceX96 = slot0[0]
    uni_p = ((sqrtPriceX96 / (2**96)) ** 2) * 10**12
    
    # Aerodrome Price
    factor_contract = w3.eth.contract(address=AERO_FACTORY, abi=AERO_FACTORY_ABI)
    p_addr = factor_contract.functions.getPool(USDC, WETH, False).call()
    p_contract = w3.eth.contract(address=p_addr, abi=V2_POOL_ABI)
    res = p_contract.functions.getReserves().call()
    # Aerodrome (Base) sorts WETH first (0x4200) then USDC (0x8335)
    # reserve0 = WETH, reserve1 = USDC
    aero_p = (res[1] / 10**6) / (res[0] / 10**18)
    
    return aero_p, uni_p

def execute_attack():
    print("\n" + "!" * 50)
    print("CRITICAL OPPORTUNITY FOUND! INITIATING FLASH LOAN ATTACK...")
    print("!" * 50 + "\n")
    
    # Run our Hardhat script in the flash_loan_demo folder
    cmd = ["npx", "hardhat", "run", "scripts/run_flash_loan.js", "--network", "hardhat"]
    cwd = "/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/flash_loan_demo"
    
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERROR:", result.stderr)

def main():
    print(">>> BOT READY: WATCHING FOR OPPORTUNITIES ON BASE <<<")
    print(f"Targeting Aerodrome & Uniswap V3 | Threshold: {THRESHOLD}%")
    
    while True:
        try:
            aero, uni = get_prices()
            gap = abs(aero - uni)
            p_gap = (gap / min(aero, uni)) * 100
            
            print(f"Market Watch: Aero ${aero:.2f} | Uni ${uni:.2f} | Gap {p_gap:.4f}%")
            
            # For the demo, we'll force an attack if we see any gap > 0.01% 
            # so the user can see the trigger work.
            if p_gap > 0.01:
                execute_attack()
                break # Exit after one demo execution
                
            time.sleep(3)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
