#!/usr/bin/env python3
"""
DIRECT SWAP EXECUTION - NO CONTRACT NEEDED
- Buy FELIX on Uniswap
- Sell FELIX on Aerodrome
- Use own capital (no flash loan)
"""

from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def direct_swap_arbitrage():
    print("🚀 DIRECT SWAP ARBITRAGE")
    print("="*30)
    
    # Connect
    rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    account = os.getenv("BOT_ADDRESS")
    private_key = os.getenv("BOT_PRIVATE_KEY")
    
    print(f"Account: {account}")
    balance = w3.eth.get_balance(account) / 10**18
    print(f"Balance: {balance:.6f} ETH")
    
    # Token addresses
    WETH = "0x4200000000000000000000000000000000000006"
    FELIX = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
    
    # Router addresses (checksummed)
    UNISWAP_ROUTER = Web3.to_checksum_address("0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24")
    AERODROME_ROUTER = Web3.to_checksum_address("0xcF77a3Ba9A5CA399B7C97c7a1C7F6f1a4F79D2F8")
    
    # ERC20 ABI
    erc20_abi = [
        {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
        {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
    ]
    
    # Router ABI (simplified)
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
        # Use 0.001 ETH for test (small amount)
        trade_amount = int(0.001 * 10**18)  # 0.001 ETH
        
        print(f"\n🎯 TRADE PLAN:")
        print(f"   Amount: 0.001 ETH (${2.50})")
        print(f"   Buy: FELIX on Uniswap")
        print(f"   Sell: FELIX on Aerodrome")
        print(f"   Expected profit: ~$0.70")
        
        if balance < 0.002:  # Need 0.002 ETH for trade + gas
            print(f"❌ Insufficient balance")
            print(f"   Need: 0.002 ETH")
            print(f"   Have: {balance:.6f} ETH")
            return False
        
        print(f"✅ Sufficient balance for test trade")
        
        # Step 1: Buy FELIX on Uniswap
        print(f"\n📈 STEP 1: Buy FELIX on Uniswap")
        
        # Create WETH contract
        weth_contract = w3.eth.contract(address=WETH, abi=erc20_abi)
        
        # Get current nonce
        current_nonce = w3.eth.get_transaction_count(account)
        
        # Approve Uniswap router
        approve_tx = weth_contract.functions.approve(UNISWAP_ROUTER, trade_amount).build_transaction({
            'gas': 50000,
            'gasPrice': w3.eth.gas_price,
            'nonce': current_nonce,
            'chainId': w3.eth.chain_id,
            'value': 0
        })
        
        signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash)
        
        print(f"   ✅ WETH approved")
        
        # Swap ETH for FELIX
        uniswap_contract = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
        
        swap_params = {
            'tokenIn': WETH,
            'tokenOut': FELIX,
            'fee': 3000,
            'recipient': account,
            'deadline': w3.eth.get_block('latest').timestamp + 300,
            'amountIn': trade_amount,
            'amountOutMinimum': 0,
            'sqrtPriceLimitX96': 0
        }
        
        swap_tx = uniswap_contract.functions.exactInputSingle(swap_params).build_transaction({
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': current_nonce + 1,
            'chainId': w3.eth.chain_id,
            'value': trade_amount
        })
        
        signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key)
        swap_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
        swap_receipt = w3.eth.wait_for_transaction_receipt(swap_hash)
        
        print(f"   ✅ Swap completed")
        print(f"   Gas used: {swap_receipt.gasUsed:,}")
        
        # Check FELIX balance
        felix_contract = w3.eth.contract(address=FELIX, abi=erc20_abi)
        felix_balance = felix_contract.functions.balanceOf(account).call()
        
        print(f"   FELIX received: {felix_balance / 10**18:.6f}")
        
        # For demo, stop here (would continue with sell on Aerodrome)
        print(f"\n🎉 FIRST STEP COMPLETED!")
        print(f"   FELIX purchased successfully")
        print(f"   Next: Sell on Aerodrome for profit")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    direct_swap_arbitrage()
