from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os

load_dotenv()

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

BALANCER_VAULT = Web3.to_checksum_address("0xBA12222222228d8Ba445958a75a0704d566BF2C8")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
FLASH_ARB = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
BOT = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))

# Test: Call flashLoan directly on Vault to see what happens
# Balancer V2 flashLoan(IFlashLoanRecipient recipient, IERC20[] tokens, uint256[] amounts, bytes userData)
# Since IFlashLoanRecipient and IERC20 are just addresses, the selector is:
# flashLoan(address,address[],uint256[],bytes) = 0x5c38449e

selector = bytes.fromhex("5c38449e")

# Encode: recipient=FlashArb, tokens=[WETH], amounts=[0.5 ETH], userData=encoded_params
# First encode the inner userData (isUniFirst, tokenB, fee1, fee2)
DEGEN = "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed"
user_data = encode(
    ['bool', 'address', 'uint24', 'uint24'],
    [True, Web3.to_checksum_address(DEGEN), 3000, 2500]
)

# Now encode the flashLoan params
flash_params = encode(
    ['address', 'address[]', 'uint256[]', 'bytes'],
    [FLASH_ARB, [WETH], [500000000000000000], user_data]
)

calldata = '0x' + (selector + flash_params).hex()

# Simulate calling flashLoan directly on Vault
print("Testing direct flashLoan call on Balancer Vault...")
try:
    result = w3.eth.call({
        'from': BOT,
        'to': BALANCER_VAULT,
        'data': calldata,
        'value': 0
    })
    print("SUCCESS:", result.hex())
except Exception as e:
    print("REVERT:", str(e))

# Also test calling execute on our contract
print("\n\nTesting execute on FlashArb...")
execute_sel = Web3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
execute_data = encode(
    ['uint256', 'bool', 'address', 'uint24', 'uint24'],
    [500000000000000000, True, Web3.to_checksum_address(DEGEN), 3000, 2500]
)
try:
    result = w3.eth.call({
        'from': BOT,
        'to': FLASH_ARB,
        'data': '0x' + (execute_sel + execute_data).hex(),
        'value': 0
    })
    print("SUCCESS:", result.hex())
except Exception as e:
    error = str(e)
    print("REVERT:", error)
    
    # Try smaller amount
    print("\nTrying smaller amount (0.01 ETH)...")
    execute_data2 = encode(
        ['uint256', 'bool', 'address', 'uint24', 'uint24'],
        [10000000000000000, True, Web3.to_checksum_address(DEGEN), 3000, 2500]
    )
    try:
        result = w3.eth.call({
            'from': BOT,
            'to': FLASH_ARB,
            'data': '0x' + (execute_sel + execute_data2).hex(),
            'value': 0
        })
        print("SUCCESS:", result.hex())
    except Exception as e2:
        print("REVERT:", str(e2))
        
    # Try with isUniFirst=False
    print("\nTrying isUniFirst=False...")
    execute_data3 = encode(
        ['uint256', 'bool', 'address', 'uint24', 'uint24'],
        [10000000000000000, False, Web3.to_checksum_address(DEGEN), 2500, 3000]
    )
    try:
        result = w3.eth.call({
            'from': BOT,
            'to': FLASH_ARB,
            'data': '0x' + (execute_sel + execute_data3).hex(),
            'value': 0
        })
        print("SUCCESS:", result.hex())
    except Exception as e3:
        print("REVERT:", str(e3))
