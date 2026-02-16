import json
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"))
bot_addr = os.getenv("BOT_ADDRESS")
contract_addr = os.getenv("FLASH_ARB_CONTRACT")

WETH = "0x4200000000000000000000000000000000000006"
DEGEN = "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed"

# Build calldata for: execute(uint256,bool,address,uint24,uint24)
# Selector
from web3 import Web3 as W3
selector = W3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]

# Encode params
from eth_abi import encode
amount = 500000000000000000  # 0.5 ETH
is_uni_first = True
token_b = DEGEN
fee1 = 3000
fee2 = 2500

params = encode(
    ['uint256', 'bool', 'address', 'uint24', 'uint24'],
    [amount, is_uni_first, W3.to_checksum_address(token_b), fee1, fee2]
)

calldata = selector + params

# Simulate
try:
    result = w3.eth.call({
        'from': W3.to_checksum_address(bot_addr),
        'to': W3.to_checksum_address(contract_addr),
        'data': '0x' + calldata.hex(),
        'value': 0
    })
    print("SUCCESS:", result.hex())
except Exception as e:
    error_str = str(e)
    print("REVERT REASON:", error_str)
    
    # Try to decode revert data
    if 'revert' in error_str.lower():
        # Check if there's hex data
        import re
        hex_match = re.search(r'0x[0-9a-fA-F]+', error_str)
        if hex_match:
            hex_data = hex_match.group()
            print("Hex Data:", hex_data)
            if len(hex_data) > 10:
                try:
                    # Standard Error(string) selector = 0x08c379a0
                    if hex_data.startswith('0x08c379a0'):
                        decoded = bytes.fromhex(hex_data[10:]).decode('utf-8', errors='ignore').strip('\x00').strip()
                        print("DECODED:", decoded)
                except:
                    pass
