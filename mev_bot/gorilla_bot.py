
import os
import asyncio
import time
import httpx
from web3 import Web3
from dotenv import load_dotenv

# Use absolute path for .env
env_path = "/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/mev_bot/.env"
load_dotenv(env_path)

# --- CONFIG ---
# Universal contract v2.0 deployed by Antigravity: 0xDd5C596fB7d3E895818b7bAFfbF021058477C38A
CONTRACT_ADDR = "0xDd5C596fB7d3E895818b7bAFfbF021058477C38A"
WETH = "0x4200000000000000000000000000000000000006"
RPC_URL = "https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f"

# Telegram Config
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# DEX Addresses
AERO_V2_ROUTER = "0xcF77a3Ba9A5CA399B7C97c7a1C7F6f1a4F79D2f8"
AERO_V2_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
AERO_V3_ROUTER = "0xbe6d8f0d05cC4be24d5167a3eF062215bE6D18a5"
AERO_V3_FACTORY = "0x5f6DEE43078a973b77d6Fe1dbb7E398fC7DddA6e"
PANCAKE_V3_ROUTER = "0x1b81D678ffb9C0263b24A97847620C99d213eB14"

TARGETS = {
    "ANTIHUNTER": {
        "address": "0xe2f3FaE4bc62E21826018364aa30ae45D430bb07",
        "aero_pool": "0xd8f6b657844804aAf904910D543Ed16df5C5a4f9", 
        "uni_pool": "0x21a138687a96298d44f5dc167ba4950c16d0fa680e8663540c0845834b4aac37",
        "uni_fee": 3000,
        "aero_fee": 2500, 
        "threshold": 1.15,
        "loan_eth": 20.0,
        "aero_type_val": 1, 
        "aero_router": PANCAKE_V3_ROUTER,
        "aero_is_token1": True,
        "uni_is_token1": True
    },
    "MORPHO": {
        "address": "0xBAa5CC21fd487B8Fcc2F632f3F4E8D37262a0842",
        "aero_pool": "0xB5F0b4aE66C14F7EFaA9aA1468E8FC536A3E288c",
        "uni_pool": "0x2F42Df4aF5312B492E9d7F7b2110D9c7bf2D9e4F",
        "uni_fee": 3000,
        "aero_fee": 200, 
        "threshold": 0.95,
        "loan_eth": 25.0,
        "aero_type_val": 2, 
        "aero_is_token1": True, 
        "uni_is_token1": True
    },
    "BNKR": {
        "address": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b",
        "aero_pool": "0xCDD442e2De893c07146B2F1072f8e077559f9aa4",
        "uni_pool": "0xAEC085E5A5CE8d96A7bDd3eB3A62445d4f6CE703",
        "uni_fee": 10000,
        "aero_fee": 200, 
        "threshold": 1.45,
        "loan_eth": 15.0,
        "aero_type_val": 2, 
        "aero_is_token0": True,
        "uni_is_token0": True
    },
    "VIRTUAL": {
        "address": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
        "aero_pool": "0x3f0296BF652e19bca772EC3dF08b32732F93014A",
        "uni_pool": "0x1D4daB3f27C7F656b6323C1D6Ef713b48A8f72F1",
        "uni_fee": 10000,
        "aero_fee": 100,
        "threshold": 1.25,
        "loan_eth": 8.0,
        "aero_type_val": 2, 
        "aero_is_token0": True, 
        "uni_is_token0": True
    },
    "VVV": {
        "address": "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf",
        "aero_pool": "0x01784ef301D79e4B2DF3a21ad9a536d4cF09A5Ce",
        "uni_pool": "0x1D2bdB7117a5A7D7fE4c1d95681a92e4Df13bB69",
        "uni_fee": 10000,
        "aero_fee": 0,
        "threshold": 1.55,
        "loan_eth": 2.0,
        "aero_type_val": 0, 
        "aero_is_token1": True,
        "uni_is_token1": True
    }
}

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))
priv_key = os.getenv("BOT_PRIVATE_KEY")

ABI_V2 = [{"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint256"},{"name":"_reserve1","type":"uint256"},{"name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"}]
ABI_V3 = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"tick","type":"int24"}],"stateMutability":"view","type":"function"}]
ABI_FLASH = [{"inputs": [{"type": "uint256", "name": "amount"}, {"components": [{"name": "targetToken", "type": "address"}, {"name": "uniRouter", "type": "address"}, {"name": "aeroRouter", "type": "address"}, {"name": "aeroFactory", "type": "address"}, {"name": "uniFee", "type": "uint24"}, {"name": "aeroFeeOrTS", "type": "uint24"}, {"name": "mode", "type": "uint8"}, {"name": "aeroType", "type": "uint8"}], "name": "config", "type": "tuple"}], "name": "execute", "outputs": [], "stateMutability": "nonpayable", "type": "function"}]

flash_contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI_FLASH)

async def send_tg(msg):
    if not TG_TOKEN or not TG_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"})
    except Exception as e:
        print(f"TG Send Error: {e}")

async def handle_tg_commands():
    if not TG_TOKEN: return
    last_update_id = 0
    print("🤖 Telegram Command Listener Active")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params={"offset": last_update_id + 1, "timeout": 30}, timeout=40)
                
                if resp.status_code == 409:
                    print("\n⚠️ TELEGRAM CONFLICT DETECTED!")
                    print("Another instance (likely Render) is processing commands. Disabling local listener.\n")
                    return # Exit the listener loop, let the other bot handle commands
                
                if resp.status_code != 200:
                    print(f"\nTG Error {resp.status_code}: {resp.text}")
                    await asyncio.sleep(10)
                    continue

                updates = resp.json().get("result", [])
                for update in updates:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    sender_id = str(msg.get("from", {}).get("id", ""))
                    
                    if sender_id != str(TG_CHAT_ID):
                        continue
                        
                    if text == "/balance":
                        bal = w3.eth.get_balance(account)
                        eth_bal = w3.from_wei(bal, "ether")
                        await send_tg(f"💰 <b>Wallet Balance:</b> {eth_bal:.6f} ETH\nAddress: <code>{account}</code>")
                    elif text == "/status":
                        targets_list = "\n".join([f"- {name}" for name in TARGETS.keys()])
                        await send_tg(f"🟢 <b>Bot Status:</b> RUNNING (Main)\n<b>Network:</b> Base\n<b>Targets:</b>\n{targets_list}")
                    elif text == "/report":
                        await send_tg("📊 <b>Daily Report:</b>\nMonitoring 5 pools.\nStatus: Healthy & Hunting")
                    elif text == "/targets":
                        t_msg = "🎯 <b>Current Thresholds:</b>\n"
                        for name, data in TARGETS.items():
                            t_msg += f"- {name}: {data['threshold']}% ({data['loan_eth']} ETH)\n"
                        await send_tg(t_msg)
                    elif text == "/ping":
                        await send_tg("🏓 Pong! Main Bot is alive.")
                        
        except Exception as e:
            pass
        await asyncio.sleep(2)

def get_v3_price(pool_addr, is_token0):
    try:
        pool = w3.eth.contract(address=Web3.to_checksum_address(pool_addr), abi=ABI_V3)
        s = pool.functions.slot0().call()
        p = (s[0] / 2**96)**2
        return p if is_token0 else (1/p)
    except: return 0

def get_v2_price(pool_addr, is_token0):
    try:
        pool = w3.eth.contract(address=Web3.to_checksum_address(pool_addr), abi=ABI_V2)
        r = pool.functions.getReserves().call()
        p = r[1] / r[0] if is_token0 else r[0] / r[1]
        return p
    except: return 0

async def execute_flash(name, data, mode, spread):
    default_aero_router = AERO_V3_ROUTER if data['aero_type_val'] >= 1 else AERO_V2_ROUTER
    aero_router = data.get('aero_router', default_aero_router)
    aero_factory = AERO_V3_FACTORY if data['aero_type_val'] >= 1 else AERO_V2_FACTORY
    
    config = (
        Web3.to_checksum_address(data['address']), 
        Web3.to_checksum_address("0x2626664c2603336E57B271c5C0b26F421741e481"), 
        Web3.to_checksum_address(aero_router), 
        Web3.to_checksum_address(aero_factory), 
        data['uni_fee'], 
        data.get('aero_fee', 0), 
        mode, 
        data['aero_type_val']
    )
    
    amount_wei = int(data['loan_eth'] * 10**18)
    msg = f"🔥 <b>ATTACKING {name}</b>\nSpread: {spread:+.2f}%\nLoan: {data['loan_eth']} ETH"
    print(msg.replace("<b>","").replace("</b>",""), flush=True)
    await send_tg(msg)
    
    try:
        bal = w3.eth.get_balance(account)
        if bal < w3.to_wei(0.003, 'ether'):
            await send_tg("⚠️ <b>OUT OF GAS!</b> Trade aborted.")
            return False

        flash_contract.functions.execute(amount_wei, config).call({'from': account})
        
        tx = flash_contract.functions.execute(amount_wei, config).build_transaction({
            'from': account, 'gas': 850000, 'nonce': w3.eth.get_transaction_count(account), 'chainId': 8453,
            'maxFeePerGas': w3.eth.get_block('latest')['baseFeePerGas'] + w3.to_wei(0.01, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei')
        })
        signed = w3.eth.account.sign_transaction(tx, priv_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        success_msg = f"💰 <b>SUCCESS! {name} TRADE FIRED</b>\nHash: <code>{tx_hash.hex()}</code>"
        print(success_msg.replace("<b>","").replace("</b>","").replace("<code>","").replace("</code>",""), flush=True)
        await send_tg(success_msg)
        return True
    except Exception as e:
        err_str = str(e)
        if "no data" in err_str: err_str = "Insufficient profit/Simulation failed"
        err_msg = f"🛡️ <b>REVERTED: {name}</b>\nReason: {err_str[:50]}"
        print(err_msg.replace("<b>","").replace("</b>",""), flush=True)
        return False

async def check_token(name, data):
    p1 = get_v3_price(data['aero_pool'], data.get('aero_is_token0', False)) if data['aero_type_val'] >= 1 else get_v2_price(data['aero_pool'], data.get('aero_is_token0', False))
    p2 = get_v3_price(data['uni_pool'], data.get('uni_is_token0', False))
    
    if p1 == 0 or p2 == 0: return
    
    spread = (p2 - p1) / p1 * 100
    print(f"📊 {name:10} | Aero: {p1:.10f} | Uni: {p2:.10f} | Spread: {spread:+.2f}%", end="\r")
    
    if spread >= data['threshold']:
        await execute_flash(name, data, 1, spread)
        await asyncio.sleep(5)
    elif spread <= -data['threshold'] :
        await execute_flash(name, data, 2, abs(spread))
        await asyncio.sleep(5)

async def main():
    start_msg = "🚀 <b>SPEED-DEMON v6.7 ONLINE</b>\nBot reset successful. Monitoring Base.\nTry <code>/status</code> to confirm targets."
    print(start_msg.replace("<b>","").replace("</b>",""), flush=True)
    await send_tg(start_msg)
    
    # Start TG listener in background
    asyncio.create_task(handle_tg_commands())
    
    while True:
        tasks = [check_token(name, data) for name, data in TARGETS.items()]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.01)

if __name__ == "__main__":
    asyncio.run(main())
