import json
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv('/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/mev_bot/.env')

w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f'))

FLASH_ADDR = os.getenv('FLASH_ARB_CONTRACT')
BOT_ADDR = os.getenv('BOT_ADDRESS')
VIRTUAL = '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b'
WETH = '0x4200000000000000000000000000000000000006'

# ABI for execute(uint256,uint8,bytes)
abi = [
    {
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "mode", "type": "uint8"},
            {"name": "params", "type": "bytes"}
        ],
        "name": "execute",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=FLASH_ADDR, abi=abi)

# Simulate Mode 0 (Uni vs Pan) for VIRTUAL
# params = abi.encode(is_buy_first, tokenB, fee1, fee2)
from eth_abi import encode

# We saw Uni -> Pan (Mode 0) in logs
is_buy_first = True # Buy on Uni, Sell on Pan
fee_uni = 3000
fee_pan = 2500
internal_params = encode(['bool', 'address', 'uint24', 'uint24'], [is_buy_first, VIRTUAL, fee_uni, fee_pan])

print(f"Simulating FlashArb.execute for VIRTUAL...")
try:
    tx = contract.functions.execute(
        int(0.1 * 1e18), 
        0, 
        internal_params
    ).call({'from': BOT_ADDR})
    print("✅ SIMULATION SUCCESS!")
except Exception as e:
    print(f"❌ SIMULATION FAILED: {e}")

# Try Mode 1 (Aero vs Pan)
internal_params_aero = encode(['bool', 'address', 'uint24', 'uint24'], [True, VIRTUAL, 0, 2500])
try:
    tx = contract.functions.execute(
        int(0.1 * 1e18), 
        1, 
        internal_params_aero
    ).call({'from': BOT_ADDR})
    print("✅ AERO SIMULATION SUCCESS!")
except Exception as e:
    print(f"❌ AERO SIMULATION FAILED: {e}")
