from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
WETH = "0x4200000000000000000000000000000000000006"

# Check 1: Does the Balancer Vault exist on Base?
code = w3.eth.get_code(Web3.to_checksum_address(BALANCER_VAULT))
print(f"Balancer Vault code size: {len(code)} bytes")
print(f"Vault exists: {len(code) > 2}")

# Check 2: How much WETH does the Vault hold?
erc20_abi = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]
weth_contract = w3.eth.contract(address=Web3.to_checksum_address(WETH), abi=erc20_abi)
vault_weth = weth_contract.functions.balanceOf(Web3.to_checksum_address(BALANCER_VAULT)).call()
print(f"Vault WETH Balance: {vault_weth / 1e18:.4f} ETH")
print(f"Can borrow 0.5 ETH: {vault_weth > 500000000000000000}")

# Check 3: Does our FlashArb contract exist?
flash_arb = os.getenv("FLASH_ARB_CONTRACT")
code2 = w3.eth.get_code(Web3.to_checksum_address(flash_arb))
print(f"\nFlashArb contract code size: {len(code2)} bytes")
print(f"FlashArb exists: {len(code2) > 2}")

# Check 4: Does the Vault support flashLoan?
# flashLoan(address,address[],uint256[],bytes)
selector = Web3.keccak(text="flashLoan(address,address[],uint256[],bytes)")[:4]
print(f"\nflashLoan selector: 0x{selector.hex()}")
