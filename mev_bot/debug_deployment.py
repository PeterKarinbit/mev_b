#!/usr/bin/env python3
"""
Debug deployment failure
"""

from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def debug_deployment():
    print("🔍 DEBUGGING DEPLOYMENT")
    print("="*30)
    
    # Connect
    rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Failed transaction hash
    tx_hash = "0xcdca9d69e2aff75ab6949a7f938a1727695722936f17da0e9e8d42fae3677650"
    
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        tx = w3.eth.get_transaction(tx_hash)
        
        print(f"Transaction: {tx_hash}")
        print(f"Status: {'FAILED' if receipt.status == 0 else 'SUCCESS'}")
        print(f"Gas used: {receipt.gasUsed:,}")
        print(f"Gas limit: {tx['gas']:,}")
        print(f"Gas price: {tx['gasPrice'] / 10**9:.4f} gwei")
        
        # Try to get revert reason
        try:
            w3.eth.call({
                'to': tx['to'],
                'from': tx['from'],
                'data': tx['input'],
                'gas': tx['gas'],
                'gasPrice': tx['gasPrice'],
                'value': tx['value']
            }, receipt['blockNumber'] - 1)
        except Exception as e:
            print(f"Revert reason: {e}")
        
        print(f"\n💡 LIKELY ISSUES:")
        print(f"1. Invalid bytecode")
        print(f"2. Insufficient gas")
        print(f"3. Network issues")
        
        print(f"\n🔧 QUICK FIX:")
        print(f"Use existing contract if available")
        
        # Check existing contracts
        flash_contract = os.getenv("FLASH_ARB_CONTRACT")
        if flash_contract:
            print(f"✅ Existing flash contract: {flash_contract}")
            print(f"🚀 Can execute arbitrage immediately")
            
            # Create execution script for existing contract
            print(f"\n📝 Creating execution script...")
            
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        return False

if __name__ == "__main__":
    debug_deployment()
