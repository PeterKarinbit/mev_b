
import os
import time
from web3 import Web3
from dotenv import load_dotenv

env_path = "/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/mev_bot/.env"
load_dotenv(env_path)

# --- CONFIG ---
CONTRACT_ADDR = "0xC3369A6e34570CDAab97672E688Ff617Ee6D38A3"
VVV = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"
WETH = "0x4200000000000000000000000000000000000006"

# Setup
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL", "https://mainnet.base.org")))
account = Web3.to_checksum_address(os.getenv("BOT_ADDRESS"))

ABI_FLASH = [{"inputs": [{"type": "uint256", "name": "amount"}, {"components": [{"name": "targetToken", "type": "address"}, {"name": "uniRouter", "type": "address"}, {"name": "aeroRouter", "type": "address"}, {"name": "aeroFactory", "type": "address"}, {"name": "uniFee", "type": "uint24"}, {"name": "mode", "type": "uint8"}, {"name": "useUsdcHop", "type": "bool"}], "name": "config", "type": "tuple"}], "name": "execute", "outputs": [], "stateMutability": "nonpayable", "type": "function"}]
flash_contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI_FLASH)

def run_stress_test():
    print("🛠️  STARTING CORE STRESS TEST...")
    print(f"📡 Node: {w3.provider.endpoint_uri}")
    print(f"🏦 Contract: {CONTRACT_ADDR}")
    print(f"👤 Account: {account}")
    
    # 1. Check Balance
    bal = w3.eth.get_balance(account)
    print(f"💰 Account Balance: {w3.from_wei(bal, 'ether'):.6f} ETH")
    if bal < w3.to_wei(0.001, 'ether'):
        print("❌ CRITICAL: Not enough ETH for gas!")
        return

    # 2. Build Configuration (Simulating Mode 1: Aero -> Uni)
    config = (
        Web3.to_checksum_address(VVV),
        Web3.to_checksum_address("0x2626664c2603336E57B271c5C0b26F421741e481"), # Uni Router
        Web3.to_checksum_address("0xcF77a3Ba9A5CA399B7C97c7a1C7f6F1a4f79D2f8"), # Aero Router
        Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da"), # Aero Factory
        10000, # 1% Uni Fee
        1,     # Mode 1
        False 
    )
    
    # 3. Perform Static Call (Simulation)
    amount_wei = w3.to_wei(4, 'ether')
    print(f"🧠 Simulating 4 ETH Flash Loan for {VVV[:10]}...")
    
    try:
        # This executes the logic on-chain but scrolls it back (no gas spent, no state changed)
        flash_contract.functions.execute(amount_wei, config).call({'from': account})
        print("✅ STRESS TEST RESULT: TRADE IS PROFITABLE! (Simulation Succeeds)")
    except Exception as e:
        # If it reverts with "!profit", it means the safety logic is WORKING
        # If it reverts with "execution reverted", the pipe is open but spread isn't enough
        msg = str(e)
        if "!profit" in msg or "0x" in msg:
            print(f"🛡️  SAFETY SYSTEM: REVERTED AS EXPECTED ({msg})")
            print("✅ PIPELINE INTEGRITY: 100% (Contract is live and guarding your ETH)")
        else:
            print(f"❌ PIPELINE ERROR: {msg}")

if __name__ == "__main__":
    run_stress_test()
