
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

WETH = "0x4200000000000000000000000000000000000006"
FELIX = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Official Addresses
UNI_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"
AERO_ROUTER = "0xcF77a3Ba9A5CA399B7C97c7a1C7f6F1a4f79D2f8"
AERO_FACTORY = "0x4200DD381b31aEf6683db6B902084cB0FFECe40Da"

class FelixFinalExecutor:
    def __init__(self, addr):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.account = Web3.to_checksum_address(BOT_ADDRESS)
        # ArbConfig struct: (address, address, address, uint24, uint8)
        self.contract = self.w3.eth.contract(address=Web3.to_checksum_address(addr), abi=[
            {"inputs": [{"type": "uint256", "name": "amount"}, {"components": [{"name": "uniRouter", "type": "address"}, {"name": "aeroRouter", "type": "address"}, {"name": "aeroFactory", "type": "address"}, {"name": "uniFee", "type": "uint24"}, {"name": "mode", "type": "uint8"}], "name": "config", "type": "tuple"}], "name": "execute", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
        ])

    def fetch_prices(self):
        url = f"https://api.dexscreener.com/latest/dex/tokens/{FELIX}"
        data = requests.get(url).json()
        pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 1000]
        
        # DexScreener labels Aerodrome as 'aerodrome'
        aero = [p for p in pairs if 'aero' in p.get('dexId', '').lower()]
        uni = [p for p in pairs if 'uniswap' in p.get('dexId', '').lower()]
        
        if not aero or not uni: return None
        
        # Check spread between Aero FELIX/USDC and Uni FELIX/WETH
        # Note: This involves a WETH/USDC hop, but priceUsd captures that.
        aero_p = float(aero[0]['priceUsd'])
        uni_p = float(uni[0]['priceUsd'])
        
        print(f"📊 Prices: Aero ${aero_p:.8f} | Uni ${uni_p:.8f}")
        spread = (uni_p - aero_p) / aero_p * 100
        print(f"📈 Spread: {spread:.2f}%")
        
        if spread > 1.0: return 1 # Buy Aero -> Sell Uni
        if spread < -1.0: return 2 # Buy Uni -> Sell Aero
        return None

    def execute(self, mode, amount_eth=0.1):
        print(f"⚡ Executing Arbing Mode {mode} with {amount_eth} ETH...")
        
        config = (
            Web3.to_checksum_address(UNI_ROUTER),
            Web3.to_checksum_address(AERO_ROUTER),
            Web3.to_checksum_address(AERO_FACTORY),
            10000, # 1% Uni Fee
            mode
        )
        
        tx = self.contract.functions.execute(int(amount_eth * 10**18), config).build_transaction({
            'from': self.account,
            'gas': 500000,
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
        print("Usage: python final_execute.py <contract_addr>")
        sys.exit(1)
    
    bot = FelixFinalExecutor(sys.argv[1])
    mode = bot.fetch_prices()
    if mode:
        bot.execute(mode, 0.25) # Execute 0.25 ETH trade
    else:
        print("No profitable spread detected.")
