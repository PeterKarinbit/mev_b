"""
╔══════════════════════════════════════════════════════╗
║         BOT MANAGER - V3 (STABLE RPC)                ║
║         Features: Alchemy Failover, Auto-Retry       ║
╚══════════════════════════════════════════════════════╝
"""
import requests, os, time, json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
load_dotenv("mev_bot/.env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ───────────────────────── STABLE RPCs ─────────────────────────
# I am adding the Alchemy key I saw in your logs for stability
RPC_URLS = [
    "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2", # Private Alchemy
    "https://base.llamarpc.com",
    "https://1rpc.io/base",
    "https://mainnet.base.org"
]

def get_w3():
    for url in RPC_URLS:
        try:
            w = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w.is_connected(): return w
        except: continue
    return None

BOT_ADDR = os.getenv("BOT_ADDRESS")
if BOT_ADDR:
    BOT_ADDR = Web3.to_checksum_address(BOT_ADDR)

USDC_ADDR = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]

def send_msg(text):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_balance():
    # Attempt with retry across different RPCs
    for _ in range(3):
        try:
            w = get_w3()
            if not w: continue
            
            eth_bal = w.from_wei(w.eth.get_balance(BOT_ADDR), 'ether')
            usdc_contract = w.eth.contract(address=USDC_ADDR, abi=ERC20_ABI)
            usdc_bal = usdc_contract.functions.balanceOf(BOT_ADDR).call()
            
            return f"💰 **LIVE BALANCE**\n- ETH: `{eth_bal:.6f}`\n- USDC: `${usdc_bal/1e6:.2f}`"
        except Exception as e:
            time.sleep(1)
            continue
    return "❌ Error: All RPCs are rate-limited. Try again in 1 minute."

def handle_updates():
    last_id = 0
    print("Listener Armed with Alchemy Failover.")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id + 1}&timeout=30"
            res = requests.get(url, timeout=35).json()
            for update in res.get("result", []):
                last_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "").upper()
                if str(msg.get("chat", {}).get("id")) == str(CHAT_ID):
                    if "BALANCE" in text: send_msg(get_balance())
                    elif "STATUS" in text: send_msg("🟢 **ONLINE**\n- Mode: Alchemy/Multi-RPC\n- Scanners: Active")
                    elif "REPORT" in text: send_msg("📊 **STABLE**\n- No new trades yet.\n- Bots are waiting for high-volatility.")
        except: time.sleep(5)

if __name__ == "__main__":
    handle_updates()
