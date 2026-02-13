from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv("mev_bot/.env")

RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

BOT_ADDRESS = os.getenv("BOT_ADDRESS")
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]

def check():
    eth_bal = w3.eth.get_balance(BOT_ADDRESS)
    print(f"ETH Balance: {w3.from_wei(eth_bal, 'ether')} ETH")
    
    usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
    usdc_bal = usdc_contract.functions.balanceOf(BOT_ADDRESS).call()
    print(f"USDC Balance: {usdc_bal / 1e6} USDC")

if __name__ == "__main__":
    check()
