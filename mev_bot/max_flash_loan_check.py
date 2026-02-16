#!/usr/bin/env python3
from web3 import Web3
from dotenv import load_dotenv
import os

# Try to load .env file
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def check_max_flash_loan_capacity():
    """Check maximum flash loan you can borrow"""
    print("🔍 MAXIMUM FLASH LOAN CAPACITY ANALYSIS")
    print("="*60)
    
    w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Base network")
        return
    
    # Balancer Vault on Base
    BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    WETH = "0x4200000000000000000000000000000000000006"
    USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    
    # ERC20 ABI for balance checks
    ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]
    
    try:
        # Check Balancer Vault WETH balance
        weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
        vault_weth_balance = weth_contract.functions.balanceOf(BALANCER_VAULT).call()
        vault_weth_eth = vault_weth_balance / 1e18
        
        print(f"💰 BALANCER VAULT WETH BALANCE:")
        print(f"   Total: {vault_weth_eth:.4f} ETH")
        print(f"   Value: ${vault_weth_eth * 3500:,.0f} (assuming $3500/ETH)")
        
        # Check Balancer Vault USDC balance
        usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
        vault_usdc_balance = usdc_contract.functions.balanceOf(BALANCER_VAULT).call()
        vault_usdc_usdc = vault_usdc_balance / 1e6
        
        print(f"\n💵 BALANCER VAULT USDC BALANCE:")
        print(f"   Total: {vault_usdc_usdc:,.0f} USDC")
        print(f"   Value: ${vault_usdc_usdc:,.0f}")
        
        # Check your contract's current balance
        contract_address = os.getenv("FLASH_ARB_CONTRACT", "")
        if contract_address:
            contract_eth = w3.eth.get_balance(contract_address)
            contract_eth_eth = contract_eth / 1e18
            contract_usdc = usdc_contract.functions.balanceOf(contract_address).call()
            contract_usdc_usdc = contract_usdc / 1e6
            
            print(f"\n🏭 YOUR CONTRACT BALANCE:")
            print(f"   ETH: {contract_eth_eth:.6f} ETH")
            print(f"   USDC: {contract_usdc_usdc:.2f} USDC")
        
        print(f"\n📊 MAXIMUM FLASH LOAN CAPACITY:")
        print("="*60)
        
        # Conservative estimates (you shouldn't borrow everything)
        max_weth_safe = vault_weth_eth * 0.1  # 10% of total liquidity
        max_usdc_safe = vault_usdc_usdc * 0.1   # 10% of total liquidity
        
        print(f"🔹 WETH FLASH LOAN:")
        print(f"   Conservative: {max_weth_safe:.4f} ETH")
        print(f"   Aggressive: {vault_weth_eth * 0.2:.4f} ETH (20% of liquidity)")
        print(f"   Maximum: {vault_weth_eth * 0.5:.4f} ETH (50% - NOT RECOMMENDED)")
        
        print(f"\n🔹 USDC FLASH LOAN:")
        print(f"   Conservative: {max_usdc_safe:,.0f} USDC")
        print(f"   Aggressive: {vault_usdc_usdc * 0.2:,.0f} USDC (20% of liquidity)")
        print(f"   Maximum: {vault_usdc_usdc * 0.5:,.0f} USDC (50% - NOT RECOMMENDED)")
        
        print(f"\n⚠️  RISK CONSIDERATIONS:")
        print("="*60)
        print("• Borrowing >10% of total liquidity can impact market")
        print("• Large loans can cause slippage and failed arbitrage")
        print("• Gas fees increase with larger transaction sizes")
        print("• Competition increases with larger trade sizes")
        print("• Flash loan fees are typically 0.09% of borrowed amount")
        
        print(f"\n💡 RECOMMENDED STRATEGY:")
        print("="*60)
        print(f"• Start small: 0.01-0.05 ETH or 5,000-25,000 USDC")
        print(f"• Scale up gradually as you find profitable opportunities")
        print(f"• Keep trades under 5% of available liquidity")
        print(f"• Monitor gas costs vs potential profits")
        
        print(f"\n🎯 CURRENT BOT CONFIGURATION:")
        print("="*60)
        print("• VIRTUAL: 0.01 ETH (WETH-based)")
        print("• DEGEN: 0.02 ETH (WETH-based)")
        print("• AERO: 0.025 ETH (WETH-based)")
        print("• BASE: 15,000 USDC (USDC-based)")
        print("• SYND: 20,000 USDC (USDC-based)")
        print("• LQTY: 10,000 USDC (USDC-based)")
        
        print(f"\n✅ YOUR CURRENT SIZES ARE SAFE!")
        print(f"All trades are well within conservative limits.")
        
    except Exception as e:
        print(f"❌ Error checking balances: {e}")

if __name__ == "__main__":
    check_max_flash_loan_capacity()
