from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"))

BALANCER_VAULT = Web3.to_checksum_address("0xBA12222222228d8Ba445958a75a0704d566BF2C8")

# Get bytecode
code = w3.eth.get_code(BALANCER_VAULT)

# Check for flashLoan selector
# flashLoan(address,address[],uint256[],bytes) = 5c38449e
# flashLoan(IFlashLoanRecipient,IERC20[],uint256[],bytes) = same since IERC20/address are same on wire
import hashlib
selectors_to_check = {
    "flashLoan(address,address[],uint256[],bytes)": Web3.keccak(text="flashLoan(address,address[],uint256[],bytes)")[:4].hex(),
    "flashLoan(address,uint256[],uint256[],bytes)": Web3.keccak(text="flashLoan(address,uint256[],uint256[],bytes)")[:4].hex(),
}

for name, sel in selectors_to_check.items():
    found = sel in code.hex()
    print(f"{name}: {sel} -> {'FOUND' if found else 'NOT FOUND'}")

# Also check if it's actually a Balancer V3 Vault
v3_selectors = {
    "unlock(bytes)": Web3.keccak(text="unlock(bytes)")[:4].hex(),
    "getVaultExtension()": Web3.keccak(text="getVaultExtension()")[:4].hex(),
}
for name, sel in v3_selectors.items():
    found = sel in code.hex()
    print(f"V3: {name}: {sel} -> {'FOUND' if found else 'NOT FOUND'}")

# Test: call the Vault with an empty flashLoan to test selector
print("\n=== Direct raw flashLoan test ===")
# Build raw calldata manually for flashLoan(address,address[],uint256[],bytes)
from eth_abi import encode

selector = bytes.fromhex("5c38449e")
FLASH_ARB = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")

params = encode(
    ['address', 'address[]', 'uint256[]', 'bytes'],
    [FLASH_ARB, [WETH], [1], b'']  # 1 wei, empty callback data
)

calldata = '0x' + (selector + params).hex()

try:
    result = w3.eth.call({
        'from': os.getenv("BOT_ADDRESS"), 
        'to': BALANCER_VAULT,
        'data': calldata,
        'value': 0,
        'gas': 1000000
    })
    print("SUCCESS:", result.hex())
except Exception as e:
    error = str(e)
    print("Error:", error[:300])
    # Try to extract hex error data
    if '0x' in error:
        import re
        matches = re.findall(r'0x[0-9a-fA-F]{8,}', error)
        for m in matches:
            print(f"Hex: {m[:20]}...")
