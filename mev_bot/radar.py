"""
╔══════════════════════════════════════════════════════╗
║         MULTI-PROTOCOL LIQUIDATION RADAR             ║
║         Protocols: AAVE V3 (ARMED), MOONWELL         ║
║         Mode: FULL AUTO EXECUTION (AAVE)             ║
╚══════════════════════════════════════════════════════╝
"""
from web3 import Web3
import json, time, os, requests, eth_abi
from dotenv import load_dotenv

load_dotenv()

# Config
PRIVATE_KEY      = os.getenv("BOT_PRIVATE_KEY")
BOT_ADDRESS      = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("FLASH_ARB_CONTRACT"))
TG_TOKEN         = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT          = os.getenv("TELEGRAM_CHAT_ID")
RPC_URL          = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Assets
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

# Protocols
AAVE_POOL = Web3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5")
AAVE_ABI = json.loads('[{"inputs":[{"name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"name":"totalCollateralBase","type":"uint256"},{"name":"totalDebtBase","type":"uint256"},{"name":"availableBorrowsBase","type":"uint256"},{"name":"currentLiquidationThreshold","type":"uint256"},{"name":"ltv","type":"uint256"},{"name":"healthFactor","type":"uint256"}],"type":"function"}]')
MOON_COMP = Web3.to_checksum_address("0xfBb21302264E2b10239d49931Cc71e687D037920")
MOON_ABI = json.loads('[{"inputs":[{"name":"account","type":"address"}],"name":"getAccountLiquidity","outputs":[{"name":"error","type":"uint256"},{"name":"liquidity","type":"uint256"},{"name":"shortfall","type":"uint256"}],"type":"function"}]')
EXEC_ABI = json.loads('[{"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"params","type":"bytes"}],"name":"execute","outputs":[],"type":"function"}]')

# Handle pathing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, "targets.txt")

def send_tg(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT, "text": f"💀 RADAR: {msg}"})
    except: pass

def fire_aave_liquidation(victim, debt_raw):
    print(f"!!! FIRING LIQUIDATION ON {victim} !!!")
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=EXEC_ABI)
    # params: bool isLiq, address collateralAsset, uint24 fee, bool buyAero, address victim
    # Assuming USDC debt, WETH collateral for now (most common)
    params = eth_abi.encode(['bool', 'address', 'uint24', 'bool', 'address'], [True, WETH, 3000, False, victim])
    
    tx = contract.functions.execute(USDC, int(debt_raw), params).build_transaction({
        'from': BOT_ADDRESS,
        'nonce': w3.eth.get_transaction_count(BOT_ADDRESS),
        'gas': 1200000,
        'maxFeePerGas': int(w3.eth.gas_price * 1.5),
        'maxPriorityFeePerGas': w3.to_wei('0.1', 'gwei'),
    })
    
    try:
        # Simulate
        w3.eth.call(tx)
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        send_tg(f"🏹 LIQUIDATION ATTEMPT SENT!\nVictim: {victim}\nTx: {h.hex()}")
    except Exception as e:
        print(f"Simulation failed: {e}")

# Anti-Spam Logic
LAST_NOTIFIED = {} # {address: (timestamp, hf)}

def scan():
    # 1. Refresh Targets from targets.txt
    targets = set()
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r") as f:
            targets = set([line.strip() for line in f if line.strip()])
    
    aave = w3.eth.contract(address=AAVE_POOL, abi=AAVE_ABI)
    print(f"[{time.strftime('%H:%M:%S')}] Monitoring {len(targets)} active whales...")
    
    count = 0
    now = time.time()
    for user in list(targets):
        if count > 150: break
        try:
            user = Web3.to_checksum_address(user)
            d = aave.functions.getUserAccountData(user).call()
            hf = d[5] / 1e18
            debt_usd = d[1] / 1e8
            
            if debt_usd > 100:
                if hf < 1.0 and debt_usd > 500: 
                    fire_aave_liquidation(user, d[1])
                elif hf < 1.15 and debt_usd > 500:
                    # Check if we should notify
                    last_time, last_hf = LAST_NOTIFIED.get(user, (0, 99))
                    # Notify only if: 1. It's been > 1 hour OR 2. HF dropped significantly since last alert
                    if (now - last_time > 3600) or (hf < last_hf - 0.02):
                        print(f"  💀 [DANGER] Whale {user[:10]} | HF: {hf:.4f} | Debt: ${debt_usd:,.2f}")
                        send_tg(f"💀 DANGER: Whale {user[:10]} HF: {hf:.4f} | Debt: ${debt_usd:,.2f}")
                        LAST_NOTIFIED[user] = (now, hf)
                elif hf < 1.3:
                    print(f"  👁️ [WATCH] Whale {user[:10]} | HF: {hf:.4f} | Debt: ${debt_usd:,.2f}")
            count += 1
        except: continue

if __name__ == "__main__":
    print(__doc__)
    while True:
        scan()
        time.sleep(15)
