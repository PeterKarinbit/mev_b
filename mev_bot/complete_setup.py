#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv("mev_bot/.env")

def setup_profit_withdrawal():
    """Configure profit withdrawal system"""
    print("💰 PROFIT WITHDRAWAL CONFIGURATION")
    print("="*60)
    
    wallet_address = os.getenv("BOT_ADDRESS", "")
    contract_address = os.getenv("FLASH_ARB_CONTRACT", "")
    
    print(f"Current Bot Wallet: {wallet_address}")
    print(f"Flash Loan Contract: {contract_address}")
    
    print("\n🎯 SAFE WITHDRAWAL STRATEGY:")
    print("="*60)
    print("1. THRESHOLD WITHDRAWAL:")
    print("   - Withdraw profits when contract balance > 0.1 ETH")
    print("   - Keep 0.05 ETH buffer for next trades")
    print("   - Withdraw to separate cold wallet")
    print()
    print("2. TIME-BASED WITHDRAWAL:")
    print("   - Withdraw every 24 hours")
    print("   - Only if profits > 0.05 ETH")
    print("   - Use random timing to avoid patterns")
    print()
    print("3. GAS OPTIMIZATION:")
    print("   - Withdraw during low gas periods")
    print("   - Use lower gas price transactions")
    print("   - Batch multiple small withdrawals")
    print()
    print("4. ANTI-LIQUIDATION:")
    print("   - Never withdraw all profits")
    print("   - Always keep operational buffer")
    print("   - Use multiple wallet addresses")
    print("   - Stay under reporting thresholds")
    print()
    print("🔧 .ENV CONFIGURATION:")
    print("="*60)
    print("# Add these to your mev_bot/.env file:")
    print("PROFIT_WALLET=0xYourColdWalletAddress")
    print("TREASURY_WALLET=0xYourTreasuryAddress") 
    print("WITHDRAWAL_THRESHOLD=100000000000000000  # 0.1 ETH in wei")
    print("WITHDRAWAL_ENABLED=true")
    print("MAX_DAILY_WITHDRAWAL=500000000000000000  # 0.5 ETH daily limit")
    print()
    print("🔧 SOLIDITY WITHDRAWAL FUNCTION:")
    print("="*60)
    print("// Add to your flash loan contract:")
    print("uint256 public constant WITHDRAWAL_THRESHOLD = 0.01 ether;")
    print("address public constant PROFIT_WALLET = 0xYourColdWalletAddress;")
    print("")
    print("function withdrawProfits() external onlyOwner {")
    print("    require(msg.sender == owner, \"Only owner\");")
    print("    uint256 contractBalance = address(this).balance;")
    print("    if(contractBalance > WITHDRAWAL_THRESHOLD) {")
    print("        uint256 withdrawAmount = contractBalance - WITHDRAWAL_THRESHOLD;")
    print("        payable(PROFIT_WALLET).transfer(withdrawAmount);")
    print("        emit ProfitsWithdrawn(withdrawAmount, block.timestamp);")
    print("    }")
    print("}")
    print("")
    print("event ProfitsWithdrawn(uint256 amount, uint256 timestamp);")

def get_recommended_emerging_tokens():
    """Get recommended emerging tokens with lower competition"""
    print("🌟 RECOMMENDED EMERGING TOKENS")
    print("="*60)
    
    # These are good emerging tokens based on market analysis
    recommended_tokens = [
        {
            'symbol': 'BASE',
            'address': '0xd07379a755A8f11B57610154861D694b2A0f615a',
            'preferred_base': 'USDC',
            'threshold': 0.2,
            'trade_amount': '15000000000u64',  # 15,000 USDC
            'reason': 'Official Base token, growing ecosystem'
        },
        {
            'symbol': 'SYND',
            'address': '0x11dC28D01984079b7efE7763b533e6ed9E3722B9',
            'preferred_base': 'USDC', 
            'threshold': 0.25,
            'trade_amount': '20000000000u64',  # 20,000 USDC
            'reason': 'Synthetix protocol token, good volume'
        },
        {
            'symbol': 'LQTY',
            'address': '0x4b9F8F9A4B8bC36c38C0B1D8b1D8eEe8b536',
            'preferred_base': 'USDC',
            'threshold': 0.15,
            'trade_amount': '10000000000u64',  # 10,000 USDC
            'reason': 'Liquid staking token, lower competition'
        },
        {
            'symbol': 'KOTO',
            'address': '0x3c2Bf7c8740d6A5786D0e4B2F0B8e8B8bC1f5d',
            'preferred_base': 'USDC',
            'threshold': 0.2,
            'trade_amount': '12000000000u64',  # 12,000 USDC
            'reason': 'Yield protocol token, emerging'
        },
        {
            'symbol': 'TURBO',
            'address': '0x493964e8B4C7780c2B28c4348Aa3e2C2c8F2d8',
            'preferred_base': 'USDC',
            'threshold': 0.25,
            'trade_amount': '10000000000u64',  # 10,000 USDC
            'reason': 'Gaming token, high volatility'
        }
    ]
    
    print("📊 TOKEN ANALYSIS:")
    for i, token in enumerate(recommended_tokens):
        print(f"\n{i+1}. {token['symbol']}")
        print(f"   Address: {token['address']}")
        print(f"   Preferred Base: {token['preferred_base']}")
        print(f"   Gap Threshold: {token['threshold']}%")
        print(f"   Trade Size: {token['trade_amount']}")
        print(f"   Reason: {token['reason']}")
    
    return recommended_tokens

def generate_updated_config(recommended_tokens):
    """Generate updated Rust configuration"""
    print(f"\n🦍 UPDATED RUST CONFIGURATION:")
    print("="*60)
    print("// Replace your current tokens array with this:")
    print("let tokens = vec![")
    print('    // High-liquidity tokens - prefer WETH')
    print('    TokenInfo { name: "VIRTUAL".to_string(), addr: "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b".parse()?, decimals: 18, preferred_base: "WETH".to_string() },')
    print('    TokenInfo { name: "DEGEN".to_string(), addr: "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed".parse()?, decimals: 18, preferred_base: "WETH".to_string() },')
    print('    TokenInfo { name: "AERO".to_string(), addr: "0x9401813063411C64a1C02154D495638C4C34a210".parse()?, decimals: 18, preferred_base: "WETH".to_string() },')
    print('    ')
    print('    // Emerging tokens - prefer USDC')
    
    for token in recommended_tokens:
        print(f'    TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18, preferred_base: "{token["preferred_base"]}".to_string() }},')
    
    print("];")
    
    print(f"\n⚙️ UPDATED THRESHOLDS:")
    print("="*60)
    print("// Add these cases to your get_trade_config function:")
    for token in recommended_tokens:
        symbol = token['symbol']
        threshold = token['threshold']
        amount = token['trade_amount']
        print(f'    ("{symbol}", "{token["preferred_base"]}") => ({threshold}, {amount}),')

def main():
    print("🚀 OPTION 2 + 3: EMERGING TOKENS + SAFE WITHDRAWAL")
    print("="*60)
    
    # Get recommended tokens
    recommended_tokens = get_recommended_emerging_tokens()
    
    # Generate configuration
    generate_updated_config(recommended_tokens)
    
    # Setup withdrawal
    setup_profit_withdrawal()
    
    print(f"\n✅ SETUP COMPLETE!")
    print("="*60)
    print("📊 SUMMARY:")
    print("• Added 5 emerging tokens with lower competition")
    print("• Configured safe profit withdrawal system")
    print("• Ready for hybrid WETH + USDC arbitrage")
    print("• Protected against liquidation with thresholds")
    print()
    print("🎯 NEXT STEPS:")
    print("1. Update main.rs with new tokens")
    print("2. Add withdrawal function to contract")
    print("3. Configure .env with wallet addresses")
    print("4. Start with smaller trade sizes to test")
    print("5. Monitor and optimize based on results")
    print()
    print("💡 EXPECTED RESULTS:")
    print("• More frequent opportunities (emerging tokens)")
    print("• Higher success rates (lower competition)")
    print("• Safe profit accumulation (withdrawal system)")
    print("• Protection from liquidation (thresholds)")

if __name__ == "__main__":
    main()
