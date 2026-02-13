from web3 import Web3

# Use public Base RPC as a fallback if Alchemy is not enabled
RPC_URLS = [
    "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2",
    "https://mainnet.base.org",
    "https://base.llamarpc.com"
]

address = "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC"

def check_balance():
    for url in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(url))
            if w3.is_connected():
                balance_wei = w3.eth.get_balance(address)
                balance_eth = w3.from_wei(balance_wei, 'ether')
                print(f"Connected to: {url}")
                print(f"Address: {address}")
                print(f"Balance: {balance_eth} ETH")
                return
        except Exception as e:
            print(f"Failed to connect to {url}: {e}")

if __name__ == "__main__":
    check_balance()
