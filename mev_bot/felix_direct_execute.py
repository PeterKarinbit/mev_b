
import os
import sys
import json
import requests
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS = os.getenv("BOT_ADDRESS")
CONTRACT_ADDR = "0x8922C0A4F651c6b65349eEE205932baDaa7F21345dF6391" # Placeholder, will update

WETH = "0x4200000000000000000000000000000000000006"
FELIX = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"

class FelixDirectExecutor:
    def __init__(self, contract_addr):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.account = Web3.to_checksum_address(BOT_ADDRESS)
        self.contract_addr = Web3.to_checksum_address(contract_addr)
        
        self.abi = json.loads("""[
            {"inputs": [{"type": "uint256", "name": "amount"}, {"components": [{"name": "buyPool", "type": "address"}, {"name": "buyZeroForOne", "type": "bool"}, {"name": "sellPool", "type": "address"}, {"name": "sellZeroForOne", "type": "bool"}], "name": "params", "type": "tuple"}], "name": "execute", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"type": "address", "name": "token"}], "name": "withdraw", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
        ]""")
        self.contract = self.w3.eth.contract(address=self.contract_addr, abi=self.abi)

    def get_pool_order(self, pool_addr):
        # Minimal V3 Pool ABI
        abi = [{"inputs": [], "name": "token0", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}]
        pool = self.w3.eth.contract(address=Web3.to_checksum_address(pool_addr), abi=abi)
        t0 = pool.functions.token0().call().lower()
        return t0 == WETH.lower() # true if WETH is token0

    def run(self, buy_pool, sell_pool, amount_eth=0.1):
        print(f"🚀 Executing Direct Flash Arb: {amount_eth} ETH")
        
        buy_weth_is_t0 = self.get_pool_order(buy_pool)
        sell_weth_is_t0 = self.get_pool_order(sell_pool)
        
        # In Buy Leg: WETH -> FELIX
        # If WETH is token0, we do zeroForOne = True
        buy_zfo = buy_weth_is_t0
        
        # In Sell Leg: FELIX -> WETH
        # If FELIX is token0, we do zeroForOne = True
        # FELIX is token0 if WETH is NOT token0 (since it's a pair)
        sell_zfo = not sell_weth_is_t0
        
        params = (
            Web3.to_checksum_address(buy_pool),
            buy_zfo,
            Web3.to_checksum_address(sell_pool),
            sell_zfo
        )
        
        tx = self.contract.functions.execute(
            int(amount_eth * 10**18),
            params
        ).build_transaction({
            'from': self.account,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account),
            'value': 0,
            'chainId': 8453
        })
        
        signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"🔥 SENT: {tx_hash.hex()}")
        return tx_hash.hex()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python direct_execute.py <contract> <buy_pool> <sell_pool> [amount]")
        sys.exit(1)
    
    exec = FelixDirectExecutor(sys.argv[1])
    amt = float(sys.argv[4]) if len(sys.argv) > 4 else 0.1
    exec.run(sys.argv[2], sys.argv[3], amt)
