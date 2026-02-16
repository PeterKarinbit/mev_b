#!/usr/bin/env python3
"""
Debug the failed FELIX transaction
"""

from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def debug_transaction():
    # Connect to Base network
    rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Failed transaction hash
    tx_hash = "0xa5120ca3b26b0132b62eccc2983c0d7eb4ac6a92b283436c5f41f6892f167d49"
    
    print("🔍 DEBUGGING FAILED TRANSACTION")
    print(f"   Hash: {tx_hash}")
    
    try:
        # Get transaction
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        print(f"\n📊 TRANSACTION DETAILS:")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Gas Limit: {tx['gas']:,}")
        print(f"   Gas Used: {receipt['gasUsed']:,}")
        print(f"   Gas Price: {tx['gasPrice'] / 10**9:.4f} gwei")
        print(f"   Status: {'SUCCESS' if receipt['status'] == 1 else 'FAILED'}")
        print(f"   Block: {receipt['blockNumber']}")
        
        # Try to get revert reason
        try:
            # This might work if we have the transaction data
            if tx['input'] != '0x':
                w3.eth.call({
                    'to': tx['to'],
                    'from': tx['from'],
                    'data': tx['input'],
                    'gas': tx['gas'],
                    'gasPrice': tx['gasPrice'],
                    'value': tx['value']
                }, receipt['blockNumber'] - 1)
        except Exception as e:
            print(f"\n❌ Revert Reason: {e}")
        
        print(f"\n💡 POSSIBLE ISSUES:")
        print(f"   1. Contract doesn't have executeArbitrage function")
        print(f"   2. Wrong function parameters")
        print(f"   3. Contract doesn't support FELIX token")
        print(f"   4. Insufficient liquidity")
        print(f"   5. Slippage too high")
        print(f"   6. Contract logic error")
        
        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. Check contract ABI")
        print(f"   2. Verify function exists")
        print(f"   3. Test with smaller amount")
        print(f"   4. Use direct DEX swaps instead")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")

if __name__ == "__main__":
    debug_transaction()
