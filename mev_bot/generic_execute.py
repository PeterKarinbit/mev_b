
import os
import sys
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS = os.getenv("BOT_ADDRESS")

# Addresses
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
UNI_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"
AERO_ROUTER = "0xcF77a3Ba9A5CA399B7C97c7a1C7f6F1a4f79D2f8"
AERO_FACTORY = "0x4200DD381b31aEf6683db6B902084cB0FFECe40Da"

# Default Token
VVV = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"

class GenericFlashExecutor:
    def __init__(self, contract_addr):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.account = Web3.to_checksum_address(BOT_ADDRESS)
        # ArbConfig: (address, address, address, address, uint24, uint8, bool)
        self.contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=[
            {"inputs": [{"type": "uint256", "name": "amount"}, {"components": [{"name": "targetToken", "type": "address"}, {"name": "uniRouter", "type": "address"}, {"name": "aeroRouter", "type": "address"}, {"name": "aeroFactory", "type": "address"}, {"name": "uniFee", "type": "uint24"}, {"name": "mode", "type": "uint8"}, {"name": "useUsdcHop", "type": "bool"}], "name": "config", "type": "tuple"}], "name": "execute", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
        ])

    def scan_opportunity(self, token_addr):
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}"
        data = requests.get(url).json()
        pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 2000]
        
        aero = [p for p in pairs if 'aero' in p.get('dexId', '').lower()]
        uni = [p for p in pairs if 'uniswap' in p.get('dexId', '').lower()]
        
        if not aero or not uni: return None
        
        aero_p = float(aero[0]['priceUsd'])
        uni_p = float(uni[0]['priceUsd'])
        
        spread = (uni_p - aero_p) / aero_p * 100
        print(f"📊 Prices: Aero ${aero_p:.6f} | Uni ${uni_p:.6f} | Spread: {spread:.2f}%")
        
        if spread > 1.5: return 1 # Buy Aero -> Sell Uni
        if spread < -1.5: return 2 # Buy Uni -> Sell Aero
        return None

    def execute_arb(self, token_addr, mode, amount_eth=0.1):
        print(f"⚡ Executing Flash Arb for {token_addr} | Mode {mode} | {amount_eth} ETH")
        
        config = (
            Web3.to_checksum_address(token_addr),
            Web3.to_checksum_address(UNI_ROUTER),
            Web3.to_checksum_address(AERO_ROUTER),
            Web3.to_checksum_address(AERO_FACTORY),
            10000, # 1% Uni Fee
            mode,
            True # Use USDC hop for Aero by default (safer for VVV)
        )
        
        tx = self.contract.functions.execute(int(amount_eth * 10**18), config).build_transaction({
            'from': self.account,
            'gas': 600000,
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
    if len(sys.argv) < 2:
        print("Usage: python generic_execute.py <contract_addr> [token_addr]")
        sys.exit(1)
    
    contract = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else VVV
    
    bot = GenericFlashExecutor(contract)
    mode = bot.scan_opportunity(token)
    
    if mode:
        bot.execute_arb(token, mode, 0.25)
    else:
        print("No profitable spread detected (>1.5%).")
