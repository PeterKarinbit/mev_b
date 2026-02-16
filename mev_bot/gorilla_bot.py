"""
╔══════════════════════════════════════════════════════╗
║         MEV NITRO GORILLA - V4 (WAR MODE)            ║
║         Modes: Threaded Sync (Hybrid), Nitro        ║
║         Status: Final Stable Release                ║
╚══════════════════════════════════════════════════════╝
"""
import json, time, os, asyncio, requests, eth_abi
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
load_dotenv("mev_bot/.env")

PRIVATE_KEY      = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS      = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
TG_TOKEN         = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT          = os.getenv("TELEGRAM_CHAT_ID")

# ──────────────────────── WAR CONFIG ────────────────────────
RPC_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
MIN_GAP_PERCENT = 0.5
NITRO_TIP = 0.6
FLASH_LOAN_AMT = 2000

TOKENS = {
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "DEGEN": "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
    "BRETT": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
    "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
    "SPAWN": "0x5f074d084c7a6598c1143c75ca77a3465941656c", # Verified from DexScreener
    "MOLTX": "0x5608b0d46654876b5c2c4aa0223592237083049b", # Verified
    "H1DR4": "0x9812eb121021bc5630327f426284fadd360824b2", # Virtuals Pair
    "TIBBIR": "0x2e864070a2f4da8e1e70e9a502f615364132c34f" # Ribbita
}

RESERVES_ABI = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
V3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
EXEC_ABI = [{"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"params","type":"bytes"}],"name":"execute","outputs":[],"type":"function"}]

DEC_CACHE = {
    "0x4200000000000000000000000000000000000006": 18, 
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": 6,
    "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b": 18 # VIRTUAL
}

import telebot
from telebot import types

# Initialize TeleBot
try:
    bot = telebot.TeleBot(TG_TOKEN)
except:
    print("❌ Telegram Bot Token Invalid")
    bot = None

# Stats Global
TOTAL_PROFIT = 0.0
LAST_PROFIT_TIME = None
START_TIME = time.time()

@bot.message_handler(commands=['status'])
def send_status(message):
    uptime = int(time.time() - START_TIME)
    h, m = divmod(uptime, 3600)
    m, s = divmod(m, 60)
    msg = f"""
🦍 **GORILLA STATUS: ONLINE**
⏱️ Uptime: {h}h {m}m {s}s
🎯 Targets: {len(PAIRS_TO_SCAN)} Pairs
⚡ Mode: War Mode (Hybrid Threaded)
💰 Total Profit: ${TOTAL_PROFIT:.2f}
    """
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['balance'])
def send_balance(message):
    try:
        eth = w3_sync.eth.get_balance(BOT_ADDRESS) / 10**18
        msg = f"💳 **WALLET BALANCE:**\nETH: {eth:.5f}"
        bot.reply_to(message, msg, parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Error checking balance.")

def start_telegram_listener():
    if bot:
        print("🎧 Telegram Listener Active...")
        bot.infinity_polling()

# Launch Listener Thread
import threading
threading.Thread(target=start_telegram_listener, daemon=True).start()

# Sync w3 instance
w3_sync = Web3(Web3.HTTPProvider(RPC_URL))
# Add new pairs to the scan logic
PAIRS_TO_SCAN = [
    ("USDC", "WETH"), ("WETH", "DEGEN"), ("WETH", "BRETT"),
    ("WETH", "SPAWN"), ("WETH", "MOLTX"), ("WETH", "TIBBIR"),
    ("VIRTUAL", "H1DR4") # Special Virtuals arb
]

# Sync w3 instance
w3_sync = Web3(Web3.HTTPProvider(RPC_URL))

def get_prices_sync(a1, a2):
    try:
        # Aero
        f_aero = w3_sync.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"s","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pa = f_aero.functions.getPool(a1, a2, False).call()
        if int(pa, 16) == 0: return None, None
        
        pool = w3_sync.eth.contract(address=pa, abi=RESERVES_ABI)
        res = pool.functions.getReserves().call()
        t0 = pool.functions.token0().call()
        ra, rb = (res[0], res[1]) if t0.lower() == a1.lower() else (res[1], res[0])
        aero_p = (rb / 10**DEC_CACHE.get(a2, 18)) / (ra / 10**DEC_CACHE.get(a1, 18))

        # Uni
        f_uni = w3_sync.eth.contract(address="0x33128a8fC17869897dcE68Ed026d694621f6FDfD", abi=[{"inputs":[{"name":"tA","type":"address"},{"name":"tB","type":"address"},{"name":"f","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}])
        pu = f_uni.functions.getPool(a1, a2, 3000).call()
        if int(pu, 16) == 0: return None, None
        
        pool_uni = w3_sync.eth.contract(address=pu, abi=V3_POOL_ABI)
        slot0 = pool_uni.functions.slot0().call()
        sq = slot0[0]
        uni_p = ((sq / (2**96)) ** 2) * (10**DEC_CACHE.get(a1, 18)) / (10**DEC_CACHE.get(a2, 18))
        
        return aero_p, uni_p
    except: return None, None

def attack_sync(a1, a2, gap, buysAero):
    try:
        contract = w3_sync.eth.contract(address=CONTRACT_ADDRESS, abi=EXEC_ABI)
        amt = FLASH_LOAN_AMT if gap < 3.0 else FLASH_LOAN_AMT * 2
        params = eth_abi.encode(['bool', 'address', 'uint24', 'bool', 'address'], [False, a2, 3000, buysAero, "0x0000000000000000000000000000000000000000"])
        
        tx = contract.functions.execute(a1, int(amt * 10**DEC_CACHE.get(a1, 18)), params).build_transaction({
            'from': BOT_ADDRESS,
            'nonce': w3_sync.eth.get_transaction_count(BOT_ADDRESS),
            'gas': 1000000,
            'maxFeePerGas': int(w3_sync.eth.gas_price * 1.5),
            'maxPriorityFeePerGas': w3_sync.to_wei(str(NITRO_TIP if gap < 2.0 else 1.5), 'gwei')
        })
        
        try:
            w3_sync.eth.call(tx) 
            signed = w3_sync.eth.account.sign_transaction(tx, PRIVATE_KEY)
            h = w3_sync.eth.send_raw_transaction(signed.raw_transaction)
            
            # Update Stats
            global TOTAL_PROFIT
            estimated_profit = amt * (gap/100) # Rough estimate
            TOTAL_PROFIT += estimated_profit
            
            msg = f"🚀 STRIKE: {a1}/{a2} Gap: {gap:.2f}% | Est. Profit: ${estimated_profit:.2f}"
            print(msg)
            try: bot.send_message(TG_CHAT, msg)
            except: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": msg})
        except: pass
    except: pass

async def hunt():
    # SEND STARTUP MSG
    try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": "🦍 GORILLA BOT: HUNTING STARTED [SILENT MODE 🔇]"})
    except: pass
    
    last_heartbeat = time.time()
    
    while True:
        try:
            # HEARTBEAT (Every 1 Hour)
            if time.time() - last_heartbeat > 3600:
                try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": "💓 GORILLA HEARTBEAT: Still Hunting..."})
                except: pass
                last_heartbeat = time.time()

            loop = asyncio.get_running_loop()
            tasks = []
            
            # HYPER-AGGRESSIVE THRESHOLD (Lowered to capture more frequent arbs)
            THRESHOLD = 0.6 # 0.6% gap is now enough to trigger
            
            for pair in PAIRS_TO_SCAN:
                # Run price check in thread (SILENTLY)
                a1, a2 = TOKENS[pair[0]], TOKENS[pair[1]]
                aero, uni = await loop.run_in_executor(None, get_prices_sync, a1, a2)
                
                if aero and uni:
                    gap = (abs(aero - uni) / min(aero, uni)) * 100
                    if gap >= THRESHOLD:
                        # NITRO MODE: Higher gas to beat the "little pesky boys"
                        priority_fee = 0.7 # Increased from 0.6
                        # The original code used run_in_executor, maintaining that pattern
                        await loop.run_in_executor(None, attack_sync, a1, a2, gap, aero < uni, 2000, priority_fee)
            
            await asyncio.sleep(0.5) 
        except Exception as e:
            # Only print actual CRITICAL errors, otherwise stay silent
            # print(f"Loop Error: {e}") 
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(hunt())
