from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os, traceback

load_dotenv()

w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"))

BALANCER_VAULT = Web3.to_checksum_address("0xBA12222222228d8Ba445958a75a0704d566BF2C8")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
FLASH_ARB = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
BOT = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))

# 1. Check if Vault implements flashLoan by checking its bytecode for the selector
vault_abi = [
    {
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "tokens", "type": "address[]"},
            {"name": "amounts", "type": "uint256[]"},
            {"name": "userData", "type": "bytes"}
        ],
        "name": "flashLoan",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [
            {"name": "token", "type": "address"}
        ],
        "name": "getProtocolFeesCollector",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]

vault = w3.eth.contract(address=BALANCER_VAULT, abi=vault_abi)

# 2. Try flashLoan with a TINY amount (1 wei) to see if it works at all
print("=== Test 1: flashLoan with 1 wei ===")
try:
    tx_data = vault.functions.flashLoan(
        FLASH_ARB,
        [WETH],
        [1],  # 1 wei
        b''   # empty userData - will fail in callback but should get past Vault
    ).build_transaction({
        'from': BOT,
        'value': 0,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price
    })
    
    result = w3.eth.call({
        'from': BOT,
        'to': BALANCER_VAULT,
        'data': tx_data['data'],
        'value': 0
    })
    print("SUCCESS:", result.hex())
except Exception as e:
    error = str(e)
    print("REVERT:", error[:200])
    
    # Check if it's a different error now
    if "BAL#" in error:
        print(">> Balancer error code found!")
    if "Only Balancer" in error:
        print(">> Our callback was reached! Balancer called us!")

# 3. Try a simple owner() call on our contract to make sure it works
print("\n=== Test 2: Check FlashArb owner ===")
flash_abi = [
    {"inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"inputs": [], "name": "WETH", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"inputs": [], "name": "BALANCER_VAULT", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]
flash = w3.eth.contract(address=FLASH_ARB, abi=flash_abi)
try:
    owner = flash.functions.owner().call()
    print(f"Owner: {owner}")
    print(f"Is BOT owner: {owner.lower() == BOT.lower()}")
    weth = flash.functions.WETH().call()
    print(f"WETH: {weth}")
    vault_addr = flash.functions.BALANCER_VAULT().call()
    print(f"Vault: {vault_addr}")
except Exception as e:
    print("Error:", e)

# 4. Check Vault's getProtocolFeesCollector to verify it's real
print("\n=== Test 3: Vault liveness check ===")
try:
    collector = vault.functions.getProtocolFeesCollector().call()
    print(f"Protocol Fees Collector: {collector}")
    print("Vault is ALIVE and responding!")
except Exception as e:
    print("Vault call failed:", e)
