from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"))
print(f"Connected: {w3.is_connected()}")
print(f"Block: {w3.eth.block_number}")
