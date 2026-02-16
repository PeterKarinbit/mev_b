#!/usr/bin/env python3
"""
⚡ FELIX/WETH Flash Loan Arbitrage Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Uses Balancer flash loan (0 fee on Base!)
- ZERO capital from wallet — only gas consumed
- Checks window → executes if profitable
- Profit accumulates in contract

Usage:
  python felix_flash_execute.py --check       # Check window only
  python felix_flash_execute.py --execute     # Check + execute if profitable
  python felix_flash_execute.py --withdraw    # Withdraw profits from contract
"""

import os
import sys
import json
import time
import requests
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ═══════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS = os.getenv("BOT_ADDRESS")
FELIX_ARB_CONTRACT = os.getenv("FELIX_ARB_CONTRACT", "")

WETH = "0x4200000000000000000000000000000000000006"
FELIX_TOKEN = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"

# Contract ABI (minimal — only what we need)
ABI = json.loads("""[
    {
        "inputs": [{"type": "uint256", "name": "amount"}, {"type": "bytes", "name": "params"}],
        "name": "execute",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"type": "address", "name": "token"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"type": "address", "name": "token"}],
        "name": "getBalance",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]""")


class FelixFlashExecutor:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise Exception("❌ Cannot connect to Base RPC")

        self.account = Web3.to_checksum_address(BOT_ADDRESS)
        self.contract = None
        if FELIX_ARB_CONTRACT:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(FELIX_ARB_CONTRACT),
                abi=ABI
            )

    # ═══════════════════════════════════════════════════
    #  CHECK ARBITRAGE WINDOW
    # ═══════════════════════════════════════════════════
    def check_window(self):
        """Check FELIX price spreads across DEXs"""
        print("═" * 60)
        print("🔍 FELIX-WETH ARBITRAGE WINDOW CHECK")
        print("═" * 60)

        # Wallet status
        balance = self.w3.eth.get_balance(self.account)
        gas_price = self.w3.eth.gas_price
        print(f"\n💳 Wallet: {balance / 10**18:.6f} ETH (${balance / 10**18 * 2500:.2f})")
        print(f"⛽ Gas: {gas_price / 10**9:.6f} gwei")
        print(f"   Execute cost (~200k gas): ${(gas_price * 200000) / 10**18 * 2500:.4f}")

        # Contract balance (if deployed)
        if self.contract:
            try:
                weth_bal = self.contract.functions.getBalance(
                    Web3.to_checksum_address(WETH)
                ).call()
                print(f"📦 Contract WETH balance: {weth_bal / 10**18:.6f} ETH")
            except Exception as e:
                print(f"⚠️ Contract check failed: {e}")

        # Get DEX prices
        print(f"\n📊 Fetching FELIX prices...")
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{FELIX_TOKEN}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            pairs = data.get('pairs', [])
            if isinstance(pairs, dict):
                pairs = list(pairs.values())

            base_pairs = [p for p in pairs if p.get('chainId') == 'base'] if pairs else []

            # Filter real pairs (liquidity > $500)
            real_pairs = []
            for p in base_pairs:
                liq = float(p.get('liquidity', {}).get('usd', 0))
                vol = float(p.get('volume', {}).get('h24', 0))
                price_usd = float(p.get('priceUsd', 0))
                dex = p.get('dexId', 'unknown')
                pair_addr = p.get('pairAddress', '')
                quote = p.get('quoteToken', {}).get('symbol', '?')

                if liq > 2000 and price_usd > 0:
                    real_pairs.append({
                        'dex': dex,
                        'pair': pair_addr,
                        'price_usd': price_usd,
                        'liq': liq,
                        'vol': vol,
                        'quote': quote
                    })
                    print(f"   {dex:12s} | ${price_usd:.8f} | liq ${liq:>10,.0f} | vol ${vol:>10,.0f} | {quote}")

            # Find best spread
            if len(real_pairs) >= 2:
                best = self._find_best_spread(real_pairs)
                if best:
                    return best
                else:
                    print("\n❌ No profitable spread found")
                    return None
            else:
                print("\n❌ Need 2+ real pairs")
                return None

        except Exception as e:
            print(f"\n❌ API Error: {e}")
            return None

    def _find_best_spread(self, pairs):
        """Find best arb opportunity"""
        best = None
        max_spread = 0

        for i, buy in enumerate(pairs):
            for j, sell in enumerate(pairs):
                if i != j and sell['price_usd'] > buy['price_usd']:
                    spread = ((sell['price_usd'] - buy['price_usd']) / buy['price_usd']) * 100

                    if spread > max_spread:
                        max_spread = spread
                        # Max trade = 30% of smaller pool liquidity
                        max_liq = min(buy['liq'], sell['liq'])
                        max_trade_usd = max_liq * 0.3
                        max_trade_eth = max_trade_usd / 2500

                        best = {
                            'spread': spread,
                            'buy_dex': buy['dex'],
                            'sell_dex': sell['dex'],
                            'buy_price': buy['price_usd'],
                            'sell_price': sell['price_usd'],
                            'buy_pair': buy['pair'],
                            'sell_pair': sell['pair'],
                            'max_trade_eth': max_trade_eth,
                            'buy_liq': buy['liq'],
                            'sell_liq': sell['liq'],
                            'buy_quote': buy['quote'],
                            'sell_quote': sell['quote'],
                        }

        if best:
            print(f"\n🎯 BEST OPPORTUNITY:")
            print(f"   Buy:  {best['buy_dex']:12s} @ ${best['buy_price']:.8f} (liq ${best['buy_liq']:,.0f})")
            print(f"   Sell: {best['sell_dex']:12s} @ ${best['sell_price']:.8f} (liq ${best['sell_liq']:,.0f})")
            print(f"   Spread: {best['spread']:.4f}%")
            print(f"   Max safe trade: ~{best['max_trade_eth']:.4f} ETH")

            gas_price = self.w3.eth.gas_price
            gas_cost_eth = (gas_price * 200000) / 10**18

            print(f"\n💰 PROFIT ESTIMATES:")
            for amt in [0.1, 0.3, 0.5, 1.0]:
                if amt <= best['max_trade_eth'] * 2:  # Allow somewhat above safe limit for flash loans
                    gross = amt * (best['spread'] / 100)
                    net = gross - gas_cost_eth
                    status = "✅" if net > 0 else "❌"
                    print(f"   {status} {amt} ETH → gross {gross:.6f} ETH, gas {gas_cost_eth:.6f}, net {net:.6f} ETH (${net * 2500:.2f})")

        return best

    # ═══════════════════════════════════════════════════
    #  EXECUTE ARBITRAGE
    # ═══════════════════════════════════════════════════
    def execute_arb(self, opportunity, amount_eth=None):
        """Execute flash loan arbitrage"""
        if not self.contract:
            print("❌ No contract address set! Deploy first.")
            print("   Set FELIX_ARB_CONTRACT in .env")
            return False

        if not opportunity:
            print("❌ No opportunity to execute")
            return False

        # Default amount: 30% of smaller pool liq (safe)
        if amount_eth is None:
            amount_eth = min(opportunity['max_trade_eth'], 0.5)
            amount_eth = max(amount_eth, 0.05)  # At least 0.05 ETH

        amount_wei = int(amount_eth * 10**18)

        # Determine mode and fee tiers
        buy_fee, sell_fee, mode = self._determine_route(opportunity)

        print(f"\n⚡ EXECUTING FLASH LOAN ARB")
        print(f"   Amount: {amount_eth} ETH (flash loan — NOT from wallet)")
        print(f"   Route: mode={mode}, buyFee={buy_fee}, sellFee={sell_fee}")
        print(f"   Buy:  {opportunity['buy_dex']}")
        print(f"   Sell: {opportunity['sell_dex']}")

        # Encode params: (uint24 buyFee, uint24 sellFee, uint8 mode)
        params = encode(['uint24', 'uint24', 'uint8'], [buy_fee, sell_fee, mode])

        # Build transaction (ONLY gas from wallet!)
        gas_price = self.w3.eth.gas_price
        nonce = self.w3.eth.get_transaction_count(self.account)

        tx = self.contract.functions.execute(amount_wei, params).build_transaction({
            'from': self.account,
            'gas': 250000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'value': 0,  # ZERO ETH sent — flash loan provides capital
            'chainId': 8453,
        })

        # Show gas cost
        gas_cost_eth = (tx['gas'] * tx['gasPrice']) / 10**18
        print(f"   Gas limit: {tx['gas']}")
        print(f"   Gas price: {tx['gasPrice'] / 10**9:.6f} gwei")
        print(f"   Max gas cost: {gas_cost_eth:.8f} ETH (${gas_cost_eth * 2500:.4f})")

        # Safety check
        balance = self.w3.eth.get_balance(self.account)
        if balance < tx['gas'] * tx['gasPrice']:
            print(f"   ❌ Not enough ETH for gas! Have {balance/10**18:.6f}, need {gas_cost_eth:.6f}")
            return False

        print(f"\n   🔐 Signing & sending...")

        # Sign and send
        signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"   📤 TX sent: {tx_hash.hex()}")
        print(f"   ⏳ Waiting for confirmation...")

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        if receipt.status == 1:
            actual_gas_cost = receipt.gasUsed * receipt.effectiveGasPrice
            print(f"\n   ✅ SUCCESS!")
            print(f"   Gas used: {receipt.gasUsed}")
            print(f"   Gas cost: {actual_gas_cost / 10**18:.8f} ETH (${actual_gas_cost / 10**18 * 2500:.4f})")
            print(f"   Block: {receipt.blockNumber}")

            # Check contract WETH balance (profit)
            try:
                weth_bal = self.contract.functions.getBalance(
                    Web3.to_checksum_address(WETH)
                ).call()
                if weth_bal > 0:
                    print(f"\n   💰 Contract WETH balance: {weth_bal / 10**18:.8f} ETH (${weth_bal / 10**18 * 2500:.4f})")
                    print(f"   Run with --withdraw to claim profits")
            except:
                pass

            return True
        else:
            print(f"\n   ❌ TRANSACTION REVERTED (no profit — no funds lost, only gas)")
            print(f"   Gas used: {receipt.gasUsed}")
            return False

    def _determine_route(self, opp):
        """Determine swap route parameters"""
        buy_dex = opp['buy_dex'].lower()
        sell_dex = opp['sell_dex'].lower()

        # Default Uni V3 fee tiers
        # Default Uni V3 fee tiers - On Base, FELIX/WETH is mainly in 1% pools
        buy_fee = 10000   # 1%
        sell_fee = 10000  # 1%
        mode = 0          # Uni → Uni

        # Check if Aerodrome is involved
        if 'aero' in buy_dex:
            mode = 1  # Aero buy → Uni sell
            buy_fee = 0
        elif 'aero' in sell_dex:
            mode = 2  # Uni buy → Aero sell
            sell_fee = 0

        # Try to determine fee tiers from pair info
        # Different Uni V3 pools = different fee tiers
        # Common: 100 (0.01%), 500 (0.05%), 3000 (0.3%), 10000 (1%)
        # For FELIX, most pools use 3000 or 10000
        if opp.get('buy_quote') == 'USDC':
            buy_fee = 10000  # FELIX/USDC tends to use 1% pools
        if opp.get('sell_quote') == 'USDC':
            sell_fee = 10000

        return buy_fee, sell_fee, mode

    # ═══════════════════════════════════════════════════
    #  WITHDRAW PROFITS
    # ═══════════════════════════════════════════════════
    def withdraw_profits(self):
        """Withdraw accumulated WETH profits from contract"""
        if not self.contract:
            print("❌ No contract address set!")
            return

        # Check balance first
        weth_bal = self.contract.functions.getBalance(
            Web3.to_checksum_address(WETH)
        ).call()

        felix_bal = self.contract.functions.getBalance(
            Web3.to_checksum_address(FELIX_TOKEN)
        ).call()

        print(f"\n📦 Contract Balances:")
        print(f"   WETH:  {weth_bal / 10**18:.8f} ETH (${weth_bal / 10**18 * 2500:.4f})")
        print(f"   FELIX: {felix_bal / 10**18:.2f}")

        if weth_bal == 0 and felix_bal == 0:
            print("   Nothing to withdraw")
            return

        # Withdraw WETH
        if weth_bal > 0:
            print(f"\n   Withdrawing {weth_bal / 10**18:.8f} WETH...")
            nonce = self.w3.eth.get_transaction_count(self.account)
            tx = self.contract.functions.withdraw(
                Web3.to_checksum_address(WETH)
            ).build_transaction({
                'from': self.account,
                'gas': 60000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'value': 0,
                'chainId': 8453,
            })
            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print(f"   ✅ WETH withdrawn! TX: {tx_hash.hex()}")
            else:
                print(f"   ❌ Withdraw failed")

        # Withdraw FELIX if any
        if felix_bal > 0:
            print(f"\n   Withdrawing {felix_bal / 10**18:.2f} FELIX...")
            nonce = self.w3.eth.get_transaction_count(self.account)
            tx = self.contract.functions.withdraw(
                Web3.to_checksum_address(FELIX_TOKEN)
            ).build_transaction({
                'from': self.account,
                'gas': 60000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'value': 0,
                'chainId': 8453,
            })
            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print(f"   ✅ FELIX withdrawn! TX: {tx_hash.hex()}")


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    executor = FelixFlashExecutor()

    if "--withdraw" in sys.argv:
        executor.withdraw_profits()

    elif "--execute" in sys.argv:
        opp = executor.check_window()
        if opp and opp['spread'] > 0.5:
            # Extract custom amount if given
            amount = None
            for arg in sys.argv:
                if arg.startswith("--amount="):
                    amount = float(arg.split("=")[1])

            confirm = input(f"\n⚡ Execute with flash loan? (y/n): ").strip().lower()
            if confirm == 'y':
                executor.execute_arb(opp, amount)
            else:
                print("Cancelled.")
        else:
            print("\n❌ Spread too small or no opportunity. Waiting...")

    else:
        # Default: check only
        opp = executor.check_window()
        if opp and opp['spread'] > 1.0:
            print(f"\n🚀 WINDOW IS OPEN! Run with --execute to trade")
        elif opp:
            print(f"\n⚠️ Marginal window. Spread: {opp['spread']:.4f}%")
        else:
            print(f"\n❌ No opportunity right now. Check again later.")

        print(f"\n📋 Commands:")
        print(f"   python felix_flash_execute.py --check       # This (check window)")
        print(f"   python felix_flash_execute.py --execute     # Check + execute")
        print(f"   python felix_flash_execute.py --withdraw    # Claim profits")
