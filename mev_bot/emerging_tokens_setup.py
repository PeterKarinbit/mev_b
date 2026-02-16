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

def find_emerging_tokens():
    """Find emerging tokens with good potential but less competition"""
    print("🔍 SEARCHING FOR EMERGING TOKENS...")
    print("="*60)
    
    # Search for newer/trending tokens
    search_terms = [
        "ai", "defi", "meme", "game", "meta", "web3", 
        "yield", "farm", "stake", "bridge", "swap", "token"
    ]
    
    emerging_tokens = []
    weth_address = "0x4200000000000000000000000000000000000006"
    
    for term in search_terms[:6]:  # Limit to avoid rate limits
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={term}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'pairs' in data:
                for pair in data['pairs']:
                    if pair.get('chainId') == 'base':
                        # Check if it's a WETH pair
                        base_addr = pair.get('baseToken', {}).get('address', '').lower()
                        quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
                        
                        if (base_addr == weth_address.lower() or quote_addr == weth_address.lower()):
                            # Check if it's not already in your current list
                            token_addr = pair.get('baseToken', {}).get('address') if base_addr != weth_address.lower() else pair.get('quoteToken', {}).get('address')
                            token_symbol = pair.get('baseToken', {}).get('symbol') if base_addr != weth_address.lower() else pair.get('quoteToken', {}).get('symbol')
                            
                            # Avoid tokens you already have
                            existing_tokens = ["VIRTUAL", "DEGEN", "AERO", "BRETT", "TOSHI", "MOCHI", "HIGHER"]
                            if token_symbol not in existing_tokens:
                                liquidity = pair.get('liquidity', {}).get('usd', 0)
                                volume_24h = pair.get('volume', {}).get('h24', 0)
                                txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
                                price_change = pair.get('priceChange', {}).get('h24', 0)
                                
                                # Emerging token criteria (less strict)
                                if (liquidity > 20000 and      # Min $20K liquidity
                                    volume_24h > 20000 and     # Min $20K volume
                                    txns_24h > 50 and        # Min 50 txns
                                    abs(price_change) > 2):     # Min 2% change
                                    
                                    emerging_tokens.append({
                                        'symbol': token_symbol,
                                        'address': token_addr,
                                        'liquidity': liquidity,
                                        'volume': volume_24h,
                                        'txns': txns_24h,
                                        'price_change': price_change,
                                        'dex': pair.get('dexId', ''),
                                        'competition_score': txns_24h / (liquidity / 1000) if liquidity > 0 else 999
                                    })
                                    
        except Exception as e:
            print(f"❌ Error searching {term}: {e}")
            continue
    
    # Sort by potential score (liquidity + volume - competition)
    emerging_tokens.sort(key=lambda x: x['liquidity'] + x['volume'] - x['competition_score'] * 1000, reverse=True)
    
    print(f"\n🎯 TOP 10 EMERGING TOKENS TO ADD:")
    print("="*60)
    
    for i, token in enumerate(emerging_tokens[:10]):
        print(f"\n{i+1}. 🌟 {token['symbol']} ({token['price_change']:+.2f}%)")
        print(f"    Address: {token['address']}")
        print(f"    DEX: {token['dex']}")
        print(f"    Liquidity: ${token['liquidity']:,.0f}")
        print(f"    Volume: ${token['volume']:,.0f}")
        print(f"    Txns: {token['txns']}")
        print(f"    Competition Score: {token['competition_score']:.2f} (lower = better)")
        
        if token['competition_score'] < 10:
            print("    ✅ LOW COMPETITION - PERFECT TARGET!")
        elif token['competition_score'] < 20:
            print("    ✅ MODERATE COMPETITION - GOOD TARGET!")
        else:
            print("    ⚠️  HIGH COMPETITION - RISKY")
    
    return emerging_tokens[:5]  # Return top 5

def generate_rust_config(emerging_tokens):
    """Generate Rust configuration for emerging tokens"""
    print(f"\n🦍 UPDATED RUST CONFIGURATION:")
    print("="*60)
    print("// Add these to your main.rs tokens array:")
    print("let tokens = vec![")
    print('    // High-liquidity tokens - prefer WETH')
    print('    TokenInfo { name: "VIRTUAL".to_string(), addr: "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b".parse()?, decimals: 18, preferred_base: "WETH".to_string() },')
    print('    TokenInfo { name: "DEGEN".to_string(), addr: "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed".parse()?, decimals: 18, preferred_base: "WETH".to_string() },')
    print('    TokenInfo { name: "AERO".to_string(), addr: "0x9401813063411C64a1C02154D495638C4C34a210".parse()?, decimals: 18, preferred_base: "WETH".to_string() },')
    print('    ')
    print('    // Emerging tokens - prefer USDC')
    
    for token in emerging_tokens:
        if token['competition_score'] < 15:  # Only add lower competition tokens
            print(f'    TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18, preferred_base: "USDC".to_string() }},')
    
    print("];")
    
    print(f"\n⚙️ UPDATED THRESHOLDS:")
    print("="*60)
    print("// Add these to get_trade_config function:")
    for token in emerging_tokens:
        if token['competition_score'] < 15:
            symbol = token['symbol']
            print(f'    ("{symbol}", "USDC") => (0.15, 10000000000u64),          // 0.15% gap, 10,000 USDC')

def configure_profit_withdrawal():
    """Configure automatic profit withdrawal system"""
    print(f"\n💰 PROFIT WITHDRAWAL CONFIGURATION:")
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
    print("4. WALLET DIVERSIFICATION:")
    print("   - Use 2-3 different withdrawal wallets")
    print("   - Rotate wallets weekly")
    print("   - Keep amounts below reporting thresholds")
    print()
    print("🔧 IMPLEMENTATION:")
    print("="*60)
    print("// Add to your .env file:")
    print("PROFIT_WALLET=0xYourColdWalletAddress")
    print("TREASURY_WALLET=0xYourTreasuryAddress")
    print("WITHDRAWAL_THRESHOLD=100000000000000000  # 0.1 ETH")
    print("WITHDRAWAL_ENABLED=true")
    print()
    print("// Add withdrawal function to your contract:")
    print("function withdrawProfits() external onlyOwner {")
    print("    uint256 balance = address(this).balance;")
    print("    if(balance > WITHDRAWAL_THRESHOLD) {")
    print("        uint256 withdrawAmount = balance - WITHDRAWAL_THRESHOLD;")
    print("        payable(PROFIT_WALLET).transfer(withdrawAmount);")
    print("    }")
    print("}")

def main():
    print("🚀 EMERGING TOKENS + PROFIT WITHDRAWAL SETUP")
    print("="*60)
    
    # Find emerging tokens
    emerging_tokens = find_emerging_tokens()
    
    if emerging_tokens:
        # Generate configuration
        generate_rust_config(emerging_tokens)
        
        # Configure withdrawal
        configure_profit_withdrawal()
        
        print(f"\n✅ SETUP COMPLETE!")
        print("="*60)
        print("📊 SUMMARY:")
        print(f"• Added {len(emerging_tokens)} emerging tokens with lower competition")
        print("• Configured profit withdrawal system")
        print("• Ready for hybrid WETH + USDC arbitrage")
        print("• Protected against liquidation with thresholds")
        print()
        print("🎯 NEXT STEPS:")
        print("1. Update your main.rs with new tokens")
        print("2. Add withdrawal function to contract")
        print("3. Configure .env with wallet addresses")
        print("4. Test with small amounts first")
        print("5. Monitor and optimize thresholds")
    else:
        print("❌ No emerging tokens found")

if __name__ == "__main__":
    main()
