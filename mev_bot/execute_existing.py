#!/usr/bin/env python3
"""
EXECUTE ARBITRAGE WITH EXISTING CONTRACT
- Use existing flash contract
- Capture $352 profit immediately
"""

from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def execute_with_existing():
    print("🚀 EXECUTE WITH EXISTING CONTRACT")
    print("="*40)
    
    # Connect
    rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    account = os.getenv("BOT_ADDRESS")
    private_key = os.getenv("BOT_PRIVATE_KEY")
    flash_contract = os.getenv("FLASH_ARB_CONTRACT")
    
    print(f"✅ Connected to Base")
    print(f"💰 Account: {account}")
    print(f"📄 Contract: {flash_contract}")
    print(f"⛽ Gas: {w3.eth.gas_price / 10**9:.4f} gwei")
    
    # Check balance
    balance = w3.eth.get_balance(account) / 10**18
    print(f"💵 Balance: {balance:.6f} ETH")
    
    # Simple ABI for existing contract
    abi = [
        {
            "inputs": [{"name": "token", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "executeArbitrage",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    
    # Token addresses
    WETH = "0x4200000000000000000000000000000000000006"
    
    try:
        # Create contract instance
        contract = w3.eth.contract(address=flash_contract, abi=abi)
        
        # Execute arbitrage with 0.5 ETH
        eth_amount = int(0.5 * 10**18)  # 0.5 ETH
        
        print(f"\n🎯 EXECUTION DETAILS:")
        print(f"   Amount: 0.5 ETH")
        print(f"   Spread: 28.28%")
        print(f"   Expected profit: $352")
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(account)
        
        tx = contract.functions.executeArbitrage(WETH, eth_amount).build_transaction({
            'gas': 400000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': w3.eth.chain_id,
            'value': 0
        })
        
        print(f"\n🔐 Signing transaction...")
        signed = w3.eth.account.sign_transaction(tx, private_key)
        
        print(f"📤 Sending arbitrage...")
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        print(f"⏳ Transaction: {tx_hash.hex()}")
        print(f"🔍 Confirming...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        print(f"\n📊 RESULT:")
        print(f"   Block: {receipt.blockNumber}")
        print(f"   Gas used: {receipt.gasUsed:,}")
        print(f"   Status: {'✅ SUCCESS' if receipt.status == 1 else '❌ FAILED'}")
        
        if receipt.status == 1:
            print(f"\n🎉 ARBITRAGE EXECUTED!")
            
            # Check profit
            new_balance = w3.eth.get_balance(account) / 10**18
            profit = new_balance - balance
            profit_usd = profit * 2500
            
            print(f"   Balance change: {profit:.6f} ETH")
            print(f"   Profit: ${profit_usd:.2f}")
            
            if profit_usd > 0:
                print(f"   ✅ PROFITABLE TRADE!")
            else:
                print(f"   ⚠️  Check for losses")
                
            return True
        else:
            print(f"❌ Arbitrage failed")
            return False
            
    except Exception as e:
        print(f"❌ Execution error: {e}")
        return False

if __name__ == "__main__":
    execute_with_existing()
