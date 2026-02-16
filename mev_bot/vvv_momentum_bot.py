"""
vvv_momentum_bot.py
===================

This bot captures strong upward trends on the VVV/WETH pair on Aerodrome (Base).
It is tuned for current market conditions where VVV is pumping hard.

STRATEGY:
- Enters when 5m price change >= 2.5% and buy volume dominates.
- Exits on take-profit (split 50/50 @ +12%/+25%) or stop-loss (-8%).
- Uses Aerodrome V2 Router for execution.

SETUP:
1. pip install web3 python-dotenv aiohttp
2. Create .env with:
   PRIVATE_KEY=0xyour_private_key
   RPC_URL=https://mainnet.base.org
3. Configure settings in the 'CONFIG' section below.

⚠️ WARNING: Trading low-cap tokens is risky. Use the DRY_RUN mode first.
"""

import os
import asyncio
import json
import logging
import time
import aiohttp
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG SECTION
# ══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    # Token & Pair Addresses
    "VVV_TOKEN": "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf",
    "PAIR_ADDR": "0x01784ef301d79e4b2df3a21ad9a536d4cf09a5ce",
    "AERO_ROUTER": "0xcF77a3Ba9A5CA399B7C97c7d454e5b1Beb874E43",
    "WETH": "0x4200000000000000000000000000000000000006",
    
    # Trade settings
    "BUY_SIZE_ETH": 0.1,             # Amount of WETH to spend
    "SLIPPAGE_PCT": 1.5,             # Slippage tolerance %
    "DRY_RUN": True,                 # If True, won't send actual transactions
    
    # Strategy settings
    "POLL_INTERVAL": 10,             # Seconds between checks
    "MIN_PRICE_CHANGE_5M": 2.5,      # Entry trigger: % gain in 5m
    "MIN_LIQUIDITY_USD": 3000000,    # Safety check: pool liquidity
    "TAKE_PROFIT_1": 12.0,           # Sell 50% at +12%
    "TAKE_PROFIT_2": 25.0,           # Sell remaining at +25%
    "STOP_LOSS": 8.0,                # Sell all if -8% from entry
    "MAX_HOLD_TIME_MINS": 45,        # Auto-exit after 45 mins
    
    # Gas settings
    "MAX_GWEI": 0.1,                 # Max gas price on Base (adjust as needed)
    "GAS_LIMIT": 250000,
}

# ══════════════════════════════════════════════════════════════════════════════
#  LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("vvv_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger("VVVMomentum")

# ══════════════════════════════════════════════════════════════════════════════
#  MINIMAL ABIS
# ══════════════════════════════════════════════════════════════════════════════
ERC20_ABI = [
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

ROUTER_ABI = [
    {"inputs": [{"name": "amountOutMin", "type": "uint256"}, {"components": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "stable", "type": "bool"}, {"name": "factory", "type": "address"}], "name": "routes", "type": "tuple[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "name": "swapExactETHForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"}, {"components": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "stable", "type": "bool"}, {"name": "factory", "type": "address"}], "name": "routes", "type": "tuple[]"}, {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}], "name": "swapExactTokensForETH", "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"}
]

@dataclass
class Position:
    entry_price: float
    amount_tokens: int
    timestamp: float
    tp_1_hit: bool = False

class VVVMomentumBot:
    def __init__(self):
        load_dotenv()
        self.rpc_url = os.getenv("RPC_URL", "https://mainnet.base.org")
        self.priv_key = os.getenv("BOT_PRIVATE_KEY")
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.priv_key:
            raise ValueError("BOT_PRIVATE_KEY missing from .env")
        
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.account = self.w3.eth.account.from_key(self.priv_key)
        
        self.router = self.w3.eth.contract(address=Web3.to_checksum_address(CONFIG["AERO_ROUTER"]), abi=ROUTER_ABI)
        self.vvv = self.w3.eth.contract(address=Web3.to_checksum_address(CONFIG["VVV_TOKEN"]), abi=ERC20_ABI)
        
        self.current_position: Optional[Position] = None
        self.last_high_5m = 0.0
        
        # Factory for Aerodrome V2 pairs is standard
        self.AERO_FACTORY = "0x4200DD381b31aEf6683db6B902084cB0FFECe40Da"

    async def fetch_dex_stats(self) -> Optional[Dict[str, Any]]:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CONFIG['PAIR_ADDR']}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("pair")
            return None
        except Exception as e:
            logger.error(f"Error fetching DexScreener data: {e}")
            return None

    def check_entry_conditions(self, stats: Dict[str, Any]) -> bool:
        if self.current_position:
            return False
            
        m5_change = float(stats.get("priceChange", {}).get("m5", 0))
        m5_buys = int(stats.get("volume", {}).get("m5", 0)) # Using volume as proxy for buy pressure
        # Dexscreener usually provides buys/sells in transaction counts
        buys_count = int(stats.get("txns", {}).get("m5", {}).get("buys", 0))
        sells_count = int(stats.get("txns", {}).get("m5", {}).get("sells", 0))
        
        liquidity = float(stats.get("liquidity", {}).get("usd", 0))
        current_price = float(stats.get("priceUsd", 0))
        
        logger.info(f"Checking Entry: 5m Change: {m5_change:.2f}% | Buys: {buys_count} | Sells: {sells_count} | Liq: ${liquidity/1e6:.1f}M")
        
        # Rule 1: Price trend
        cond_price = m5_change >= CONFIG["MIN_PRICE_CHANGE_5M"]
        # Rule 2: Volume trend
        cond_vol = buys_count > sells_count
        # Rule 3: Breaking high (simple proxy)
        cond_high = current_price > self.last_high_5m
        # Rule 4: Liquidity safety
        cond_liq = liquidity >= CONFIG["MIN_LIQUIDITY_USD"]
        
        self.last_high_5m = max(self.last_high_5m, current_price)
        
        return all([cond_price, cond_vol, cond_high, cond_liq])

    async def execute_buy(self, price_usd: float):
        eth_amt = Web3.to_wei(CONFIG["BUY_SIZE_ETH"], "ether")
        logger.info(f"⚡ BUYING {CONFIG['BUY_SIZE_ETH']} ETH worth of VVV...")
        
        if CONFIG["DRY_RUN"]:
            logger.info("🧪 [DRY RUN] Would execute Aerodrome swap WETH -> VVV")
            # Fake token amount for simulation
            self.current_position = Position(
                entry_price=price_usd,
                amount_tokens=int(1000 * 1e18), 
                timestamp=time.time()
            )
            return

        try:
            # Building routes for Aerodrome
            routes = [(
                Web3.to_checksum_address(CONFIG["WETH"]),
                Web3.to_checksum_address(CONFIG["VVV_TOKEN"]),
                False, # unstable pool
                Web3.to_checksum_address(self.AERO_FACTORY)
            )]
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
            max_prio = self.w3.to_wei(0.001, 'gwei') # Base typical prio
            max_fee = base_fee + max_prio
            
            tx = self.router.functions.swapExactETHForTokens(
                0,
                routes,
                self.account.address,
                int(time.time()) + 60
            ).build_transaction({
                "from": self.account.address,
                "value": eth_amt,
                "gas": CONFIG["GAS_LIMIT"],
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_prio,
                "nonce": nonce,
                "chainId": 8453
            })
            
            signed = self.w3.eth.account.sign_transaction(tx, self.priv_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            logger.info(f"📤 Purchase TX sent: {tx_hash.hex()}")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if receipt.status == 1:
                # Get actual balance
                bal = self.vvv.functions.balanceOf(self.account.address).call()
                self.current_position = Position(entry_price=price_usd, amount_tokens=bal, timestamp=time.time())
                logger.info(f"✅ Purchase SUCCESSful. Tokens: {bal/1e18:,.2f}")
                await self.send_notification(f"ENTRY: Bought VVV at ${price_usd}")
            else:
                logger.error("❌ Purchase REVERTED")

        except Exception as e:
            logger.error(f"Execution Error (Buy): {e}")

    async def execute_sell(self, percent: float, price_usd: float):
        if not self.current_position:
            return
            
        sell_amt = int(self.current_position.amount_tokens * (percent / 100))
        logger.info(f"⚡ SELLING {percent}% ({sell_amt/1e18:,.2f}) units...")

        if CONFIG["DRY_RUN"]:
            logger.info(f"🧪 [DRY RUN] Would SELL {percent}% of VVV position at ${price_usd}")
            if percent >= 100 or self.current_position.tp_1_hit:
                self.current_position = None
            else:
                self.current_position.tp_1_hit = True
            return

        try:
            # Check allowance
            allowance = self.vvv.functions.allowance(self.account.address, self.router.address).call()
            if allowance < sell_amt:
                logger.info("Approving router...")
                tx_app = self.vvv.functions.approve(self.router.address, 2**256-1).build_transaction({
                    "from": self.account.address, "gas": 60000, "gasPrice": self.w3.eth.gas_price, "nonce": self.w3.eth.get_transaction_count(self.account.address), "chainId": 8453
                })
                signed_app = self.w3.eth.account.sign_transaction(tx_app, self.priv_key)
                self.w3.eth.send_raw_transaction(signed_app.rawTransaction)
                time.sleep(5)

            routes = [(
                Web3.to_checksum_address(CONFIG["VVV_TOKEN"]),
                Web3.to_checksum_address(CONFIG["WETH"]),
                False,
                Web3.to_checksum_address(self.AERO_FACTORY)
            )]
            
            base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
            max_prio = self.w3.to_wei(0.001, 'gwei')
            max_fee = base_fee + max_prio

            tx = self.router.functions.swapExactTokensForETH(
                sell_amt, 0, routes, self.account.address, int(time.time()) + 60
            ).build_transaction({
                "from": self.account.address,
                "gas": CONFIG["GAS_LIMIT"],
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_prio,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "chainId": 8453
            })
            
            signed = self.w3.eth.account.sign_transaction(tx, self.priv_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                logger.info("✅ Sell SUCCESSful")
                if percent >= 100:
                    self.current_position = None
                    await self.send_notification(f"EXIT: Sold remaining VVV at ${price_usd}")
                else:
                    self.current_position.amount_tokens -= sell_amt
                    self.current_position.tp_1_hit = True
                    await self.send_notification(f"TAKE PROFIT: Sold 50% VVV at ${price_usd}")
            else:
                logger.error("❌ Sell REVERTED")
        except Exception as e:
            logger.error(f"Execution Error (Sell): {e}")

    async def send_notification(self, msg: str):
        logger.info(f"🔔 NOTIFICATION: {msg}")
        if self.tg_token and self.tg_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
                payload = {"chat_id": self.tg_chat_id, "text": f"🚀 VVV BOT: {msg}"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            logger.error(f"Telegram error: {await resp.text()}")
            except Exception as e:
                logger.error(f"Failed to send Telegram msg: {e}")

    async def manage_position(self, current_price: float):
        if not self.current_position:
            return
            
        profit_pct = ((current_price - self.current_position.entry_price) / self.current_position.entry_price) * 100
        logger.info(f"Position Status: Price: ${current_price:.4f} | Profit: {profit_pct:.2f}%")
        
        # Exit Rule 1: Stop Loss
        if profit_pct <= -CONFIG["STOP_LOSS"]:
            logger.warning("🔴 STOP LOSS HIT!")
            await self.execute_sell(100, current_price)
            return

        # Exit Rule 2: Take Profit 1
        if profit_pct >= CONFIG["TAKE_PROFIT_1"] and not self.current_position.tp_1_hit:
            logger.info("🟢 TAKE PROFIT 1 HIT!")
            await self.execute_sell(50, current_price)
            
        # Exit Rule 3: Take Profit 2
        if profit_pct >= CONFIG["TAKE_PROFIT_2"]:
            logger.info("🚀 TAKE PROFIT 2 HIT!")
            await self.execute_sell(100, current_price)
            return
            
        # Exit Rule 4: Timer
        hold_time_mins = (time.time() - self.current_position.timestamp) / 60
        if hold_time_mins >= CONFIG["MAX_HOLD_TIME_MINS"]:
            logger.warning("⏰ TIME EXIT HIT!")
            await self.execute_sell(100, current_price)

    async def run(self):
        logger.info("🚀 VVV Momentum Bot Starting...")
        logger.info(f"   Target: VVV/WETH on Aerodrome (Base)")
        logger.info(f"   Wallet: {self.account.address}")
        logger.info(f"   Mode: {'🧪 DRY RUN' if CONFIG['DRY_RUN'] else '🔥 LIVE TRADING'}")
        
        while True:
            stats = await self.fetch_dex_stats()
            if stats:
                current_price = float(stats.get("priceUsd", 0))
                
                if not self.current_position:
                    if self.check_entry_conditions(stats):
                        await self.execute_buy(current_price)
                else:
                    await self.manage_position(current_price)
            else:
                logger.warning("Empty data from DexScreener, retrying...")
            
            await asyncio.sleep(CONFIG["POLL_INTERVAL"])

if __name__ == "__main__":
    bot = VVVMomentumBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"FATAL ERROR: {e}")
