
import requests
from web3 import Web3
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS = os.getenv("BOT_ADDRESS")

CONTRACT_ADDR = "0xC3369A6e34570CDAab97672E688Ff617Ee6D38A3"

class MultiTokenArbBot:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.account = Web3.to_checksum_address(BOT_ADDRESS)
        self.contract_addr = Web3.to_checksum_address(CONTRACT_ADDR)
        self.contract = self.w3.eth.contract(address=self.contract_addr, abi=[
            {"inputs": [{"type": "uint256", "name": "amount"}, {"components": [{"name": "targetToken", "type": "address"}, {"name": "uniRouter", "type": "address"}, {"name": "aeroRouter", "type": "address"}, {"name": "aeroFactory", "type": "address"}, {"name": "uniFee", "type": "uint24"}, {"name": "mode", "type": "uint8"}, {"name": "useUsdcHop", "type": "bool"}], "name": "config", "type": "tuple"}], "name": "execute", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
        ])

    def scan_and_execute(self, target_spread=1.2, amount_eth=0.1):
        print(f"🕵️ Scanning for Base opportunities (Threshold: {target_spread}%)...")
        # Get trending tokens on Base
        try:
            search = requests.get("https://api.dexscreener.com/latest/dex/search/?q=base", timeout=10).json()
            candidates = []
            seen = set()
            for p in search.get('pairs', []):
                t_addr = p.get('baseToken', {}).get('address')
                if t_addr and t_addr not in seen:
                    candidates.append(t_addr)
                    seen.add(t_addr)
                if len(candidates) > 20: break
                
            for token in candidates:
                self._process_token(token, target_spread, amount_eth)
                
        except Exception as e:
            print(f"Scan Error: {e}")

    def _process_token(self, token, target_spread, amount_eth):
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token}"
            data = requests.get(url, timeout=5).json()
            pairs = data.get('pairs', [])
            if not pairs: return
            
            base_pairs = [p for p in pairs if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 5000]
            if len(base_pairs) < 2: return
            
            aero = [p for p in base_pairs if 'aero' in p.get('dexId', '').lower()]
            uni = [p for p in base_pairs if 'uniswap' in p.get('dexId', '').lower()]
            
            if not aero or not uni: return
            
            aero_p = float(aero[0]['priceUsd'])
            uni_p = float(uni[0]['priceUsd'])
            symbol = aero[0].get('baseToken', {}).get('symbol', '???')
            
            spread = (uni_p - aero_p) / aero_p * 100
            print(f"   [{symbol}] Aero: ${aero_p:.6f} | Uni: ${uni_p:.6f} | Spread: {spread:.2f}%")
            
            if abs(spread) >= target_spread:
                mode = 1 if spread > 0 else 2
                print(f"🔥 PROFITABLE WINDOW: Executing {symbol} Mode {mode}...")
                self._execute(token, mode, amount_eth)
                
        except Exception as e:
            pass

    def _execute(self, token, mode, amount_eth):
        try:
            config = (
                Web3.to_checksum_address(token),
                Web3.to_checksum_address("0x2626664c2603336E57B271c5C0b26F421741e481"),
                Web3.to_checksum_address("0xcF77a3Ba9A5CA399B7C97c7a1C7f6F1a4f79D2f8"),
                Web3.to_checksum_address("0x4200DD381b31aEf6683db6B902084cB0FFECe40Da"),
                10000, # 1% Uni Fee
                mode,
                True # USDC Hop
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
            print(f"🚀 SENT FLASH ARB: {tx_hash.hex()}")
        except Exception as e:
            print(f"Execution Error: {e}")

if __name__ == "__main__":
    bot = MultiTokenArbBot()
    bot.scan_and_execute(1.5, 0.25)
