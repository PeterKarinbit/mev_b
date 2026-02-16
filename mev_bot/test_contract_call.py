#!/usr/bin/env python3
import subprocess
import sys
import os

def test_contract_call():
    """Test the exact same call that works in Python"""
    print("🔍 TESTING CONTRACT CALL WITH PYTHON REFERENCE")
    print("="*60)
    
    # Test the exact call from debug_deep.py that works
    python_script = '''
import requests
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os

load_dotenv("mev_bot/.env")

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

BOT = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
FLASH_ARB = os.getenv("FLASH_ARB_CONTRACT", "")
DEGEN = "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed"

# Test the exact working call
execute_sel = w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
execute_data = encode(
    ['uint256', 'bool', 'address', 'uint24', 'uint24'],
    [10000000000000000, True, DEGEN, 3000, 2500]
)

try:
    result = w3.eth.call({
        'from': BOT,
        'to': FLASH_ARB,
        'data': '0x' + (execute_sel + execute_data).hex(),
        'value': 0
    })
    print("✅ PYTHON CALL SUCCESS!")
    print(f"Result: {result.hex()}")
except Exception as e:
    print(f"❌ PYTHON CALL FAILED: {e}")
'''
    
    # Write to temp file and execute
    with open('/tmp/test_contract.py', 'w') as f:
        f.write(python_script)
    
    try:
        result = subprocess.run(['python3', '/tmp/test_contract.py'], 
                              capture_output=True, text=True, timeout=10)
        print("Python output:")
        print(result.stdout)
        if result.stderr:
            print("Python errors:")
            print(result.stderr)
    except Exception as e:
        print(f"Failed to run Python test: {e}")

if __name__ == "__main__":
    test_contract_call()
