import time
from web3 import Web3

RPC = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"

print("🐍 PYTHON SPEED TEST")
start = time.time()
w3 = Web3(Web3.HTTPProvider(RPC))
block = w3.eth.block_number
end = time.time()
print(f"Block: {block}")
print(f"Time: {(end - start) * 1000:.2f} ms")
