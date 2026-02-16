from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"))
fac_abi = [{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
fac = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=fac_abi)
t1 = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
t2 = "0x4200000000000000000000000000000000000006"
print(f"Checking Stable=False: {fac.functions.getPool(t1, t2, False).call()}")
print(f"Checking Stable=True: {fac.functions.getPool(t1, t2, True).call()}")
