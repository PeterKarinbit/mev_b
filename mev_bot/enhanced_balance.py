#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv("mev_bot/.env")

# RPC URLs
RPC_URLS = [
    "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2",
    "https://mainnet.base.org",
    "https://base.llamarpc.com"
]

# Contract addresses
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"

# ERC20 ABI for balance checks
ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]

def get_full_balance():
    """Check ETH, USDC, and transaction history"""
    
    # Your wallet address
    wallet_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
    contract_address = os.getenv("FLASH_ARB_CONTRACT", "")
    
    print("🔍 WALLET BALANCE & TRANSACTION ANALYSIS")
    print("="*60)
    print(f"Wallet: {wallet_address}")
    if contract_address:
        print(f"Contract: {contract_address}")
    print()
    
    for url in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(url))
            if w3.is_connected():
                print(f"📡 Connected to: {url}")
                
                # Check ETH balance
                eth_balance_wei = w3.eth.get_balance(wallet_address)
                eth_balance = w3.from_wei(eth_balance_wei, 'ether')
                print(f"💰 ETH Balance: {eth_balance} ETH")
                
                # Check USDC balance
                usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
                usdc_balance = usdc_contract.functions.balanceOf(wallet_address).call()
                usdc_balance_usdc = usdc_balance / 1e6  # USDC has 6 decimals
                print(f"💵 USDC Balance: {usdc_balance_usdc:,.2f} USDC")
                
                # Check contract balance (if exists)
                if contract_address:
                    contract_eth = w3.eth.get_balance(contract_address)
                    contract_eth = w3.from_wei(contract_eth, 'ether')
                    print(f"🏭 Contract ETH: {contract_eth} ETH")
                    
                    contract_usdc = usdc_contract.functions.balanceOf(contract_address).call()
                    contract_usdc_usdc = contract_usdc / 1e6
                    print(f"🏭 Contract USDC: {contract_usdc_usdc:,.2f} USDC")
                
                print()
                
                # Check recent transactions (last 10)
                print("📜 RECENT TRANSACTIONS:")
                latest_block = w3.eth.get_block('latest')
                current_block = latest_block['number']
                
                # Scan last 50 blocks for transactions
                tx_count = 0
                for block_offset in range(min(50, current_block)):
                    try:
                        block = w3.eth.get_block(current_block - block_offset, full_transactions=True)
                        if block and block.get('transactions'):
                            for tx in block['transactions']:
                                if tx.get('from', '').lower() == wallet_address.lower() or tx.get('to', '').lower() == wallet_address.lower():
                                    tx_count += 1
                                    if tx_count <= 5:  # Show last 5 transactions
                                        tx_hash = tx.get('hash', 'N/A')
                                        tx_from = tx.get('from', 'N/A')
                                        tx_to = tx.get('to', 'N/A')
                                        tx_value = w3.from_wei(tx.get('value', 0), 'ether')
                                        block_num = tx.get('blockNumber', 'N/A')
                                        
                                        print(f"  Tx {tx_count}: {tx_hash}")
                                        print(f"    From: {tx_from}")
                                        print(f"    To: {tx_to}")
                                        print(f"    Value: {tx_value} ETH")
                                        print(f"    Block: {block_num}")
                                        print()
                    except:
                        continue
                
                if tx_count == 0:
                    print("  No recent transactions found")
                
                return
                
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {e}")
            continue
    
    print("❌ All RPC connections failed")

def check_profit_tracking():
    """Check if there are any profit tracking mechanisms"""
    print("\n💡 PROFIT TRACKING ANALYSIS:")
    print("="*60)
    
    # Check if profits are being sent to a separate wallet
    wallet_address = os.getenv("BOT_ADDRESS", "")
    contract_address = os.getenv("FLASH_ARB_CONTRACT", "")
    
    print(f"Current Bot Wallet: {wallet_address}")
    print(f"Flash Loan Contract: {contract_address}")
    
    # Common profit wallet patterns (check if any are in your .env)
    profit_wallet = os.getenv("PROFIT_WALLET", "")
    treasury_wallet = os.getenv("TREASURY_WALLET", "")
    
    if profit_wallet:
        print(f"💎 Profit Wallet Found: {profit_wallet}")
    else:
        print("❌ No separate profit wallet configured")
    
    if treasury_wallet:
        print(f"🏦 Treasury Wallet Found: {treasury_wallet}")
    else:
        print("❌ No treasury wallet configured")
    
    print("\n📊 SWAP DETECTION:")
    print("• ETH balance changes = WETH flash loan arbitrage")
    print("• USDC balance changes = USDC flash loan arbitrage") 
    print("• Contract balance = Profits being accumulated")
    print("• Check transaction history for swap details")

if __name__ == "__main__":
    get_full_balance()
    check_profit_tracking()
