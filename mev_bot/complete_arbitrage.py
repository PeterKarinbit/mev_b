#!/usr/bin/env python3
"""
COMPLETE ARBITRAGE - SELL ON AERODROME
- Step 2: Sell FELIX for profit
- Complete the arbitrage cycle
"""

from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def complete_arbitrage():
    print("🚀 COMPLETE ARBITRAGE - SELL ON AERODROME")
    print("="*50)
    
    # Connect
    rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    account = os.getenv("BOT_ADDRESS")
    private_key = os.getenv("BOT_PRIVATE_KEY")
    
    print(f"Account: {account}")
    balance = w3.eth.get_balance(account) / 10**18
    print(f"ETH Balance: {balance:.6f} ETH")
    
    # Token addresses
    WETH = "0x4200000000000000000000000000000000000006"
    FELIX = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
    
    # Router address
    AERODROME_ROUTER = Web3.to_checksum_address("0xcF77a3Ba9A5CA399B7C97c7a1C7F6f1a4F79D2F8")
    
    # ABIs
    erc20_abi = [
        {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
        {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
    ]
    
    router_abi = [
        {
            "inputs": [{
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "name": "params",
                "type": "tuple"
            }],
            "name": "exactInputSingle",
            "outputs": [{"name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    try:
        # Check FELIX balance
        felix_contract = w3.eth.contract(address=FELIX, abi=erc20_abi)
        felix_balance = felix_contract.functions.balanceOf(account).call()
        
        print(f"FELIX Balance: {felix_balance}")
        
        if felix_balance == 0:
            print(f"❌ No FELIX to sell")
            return False
        
        print(f"✅ Found FELIX to sell")
        
        # Approve Aerodrome router
        print(f"\n📈 STEP 2: Approve Aerodrome router")
        
        current_nonce = w3.eth.get_transaction_count(account)
        
        approve_tx = felix_contract.functions.approve(AERODROME_ROUTER, felix_balance).build_transaction({
            'gas': 50000,
            'gasPrice': w3.eth.gas_price,
            'nonce': current_nonce,
            'chainId': w3.eth.chain_id,
            'value': 0
        })
        
        signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash)
        
        print(f"   ✅ FELIX approved")
        
        # Sell FELIX for ETH on Aerodrome
        print(f"\n💰 STEP 3: Sell FELIX on Aerodrome")
        
        aerodrome_contract = w3.eth.contract(address=AERODROME_ROUTER, abi=router_abi)
        
        swap_params = {
            'tokenIn': FELIX,
            'tokenOut': WETH,
            'fee': 3000,
            'recipient': account,
            'deadline': w3.eth.get_block('latest').timestamp + 300,
            'amountIn': felix_balance,
            'amountOutMinimum': 0,
            'sqrtPriceLimitX96': 0
        }
        
        swap_tx = aerodrome_contract.functions.exactInputSingle(swap_params).build_transaction({
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': current_nonce + 1,
            'chainId': w3.eth.chain_id,
            'value': 0
        })
        
        signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key)
        swap_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
        swap_receipt = w3.eth.wait_for_transaction_receipt(swap_hash)
        
        print(f"   ✅ Sell completed")
        print(f"   Gas used: {swap_receipt.gasUsed:,}")
        
        # Check final balances
        final_eth_balance = w3.eth.get_balance(account) / 10**18
        final_felix_balance = felix_contract.functions.balanceOf(account).call()
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"   ETH Balance: {final_eth_balance:.6f} ETH")
        print(f"   FELIX Balance: {final_felix_balance}")
        print(f"   ETH Change: {final_eth_balance - balance:.6f} ETH")
        print(f"   Profit: ${(final_eth_balance - balance) * 2500:.2f}")
        
        if final_eth_balance > balance:
            print(f"   ✅ PROFITABLE ARBITRAGE!")
        else:
            print(f"   ⚠️  Check for losses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    complete_arbitrage()
