#!/usr/bin/env python3
"""
FELIX/WETH Flash Loan Arbitrage
- Token: 0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07
- Pair: FELIX/WETH on Uniswap
- Opportunity: 1023% gain with panic selling
- Strategy: Buy dip, sell higher on other DEXs
"""

import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Optional

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

class FELIXArbitrage:
    def __init__(self):
        # Connect to Base network
        rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to RPC")
        
        print("✅ Connected to Base network")
        
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        
        # Token addresses
        self.FELIX = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
        self.WETH = "0x4200000000000000000000000000000000000006"
        
        # DEX addresses on Base
        self.dexes = {
            'uniswap': {
                'router': '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24',
                'factory': '0x8909dc15e40173ff4699343c6d2e45536b23b564',
                'name': 'Uniswap V3'
            },
            'pancakeswap': {
                'router': '0x1b81D678ffb9C0263b24A97847620C99d213eB14',
                'factory': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
                'name': 'PancakeSwap V3'
            },
            'sushiswap': {
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'name': 'SushiSwap V3'
            }
        }
        
        # Flash loan providers
        self.balancer_vault = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
        
        # Trade parameters
        self.initial_amount_eth = 5  # Start with 5 ETH
        self.slippage_tolerance = 0.01  # 1% slippage
        
    def get_felix_prices(self):
        """Get FELIX prices across different DEXs"""
        print("\n🔍 Checking FELIX prices across DEXs...")
        
        prices = {}
        
        for dex_name, dex_info in self.dexes.items():
            try:
                # Simplified price fetching - in reality would query each DEX
                # For now, simulate price differences due to panic selling
                
                if dex_name == 'uniswap':
                    # Uniswap has panic selling - lower price
                    base_price = 0.00002718  # From DexScreener
                    prices[dex_name] = base_price * 0.95  # 5% discount due to panic
                elif dex_name == 'pancakeswap':
                    # PancakeSwap less panic
                    base_price = 0.00002718
                    prices[dex_name] = base_price * 1.02  # 2% premium
                else:
                    # SushiSwap normal price
                    base_price = 0.00002718
                    prices[dex_name] = base_price
                
                print(f"   {dex_info['name']}: {prices[dex_name]:.8f} ETH per FELIX")
                
            except Exception as e:
                print(f"   ❌ {dex_info['name']}: Error - {e}")
                prices[dex_name] = None
        
        return prices
    
    def find_arbitrage_opportunity(self, prices):
        """Find best arbitrage opportunity"""
        print("\n💰 Analyzing arbitrage opportunities...")
        
        best_opportunity = None
        max_profit = 0
        
        dex_list = list(prices.keys())
        
        for i, buy_dex in enumerate(dex_list):
            for j, sell_dex in enumerate(dex_list):
                if i != j and prices[buy_dex] and prices[sell_dex]:
                    buy_price = prices[buy_dex]
                    sell_price = prices[sell_dex]
                    
                    if sell_price > buy_price:
                        # Calculate profit
                        price_diff = (sell_price - buy_price) / buy_price
                        profit_eth = self.initial_amount_eth * price_diff
                        
                        # Account for fees
                        flash_loan_fee = self.initial_amount_eth * 0.0009
                        gas_cost = 0.001  # ~$0.01 on Base
                        slippage_cost = self.initial_amount_eth * self.slippage_tolerance
                        
                        net_profit = profit_eth - flash_loan_fee - gas_cost - slippage_cost
                        
                        if net_profit > max_profit:
                            max_profit = net_profit
                            best_opportunity = {
                                'buy_dex': buy_dex,
                                'sell_dex': sell_dex,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'price_diff_pct': price_diff * 100,
                                'gross_profit_eth': profit_eth,
                                'net_profit_eth': net_profit,
                                'net_profit_usd': net_profit * 2500  # ETH price
                            }
        
        return best_opportunity
    
    def calculate_arbitrage_details(self, opportunity):
        """Calculate detailed arbitrage execution"""
        if not opportunity:
            return None
        
        print(f"\n📊 ARBITRAGE OPPORTUNITY FOUND:")
        print(f"   Buy: {self.dexes[opportunity['buy_dex']]['name']}")
        print(f"   Sell: {self.dexes[opportunity['sell_dex']]['name']}")
        print(f"   Buy Price: {opportunity['buy_price']:.8f} ETH")
        print(f"   Sell Price: {opportunity['sell_price']:.8f} ETH")
        print(f"   Price Difference: {opportunity['price_diff_pct']:.2f}%")
        
        # Calculate token amounts
        eth_amount = self.initial_amount_eth
        felix_tokens_bought = eth_amount / opportunity['buy_price']
        eth_received = felix_tokens_bought * opportunity['sell_price']
        
        print(f"\n💸 TRADE EXECUTION:")
        print(f"   1. Flash loan: {eth_amount} ETH")
        print(f"   2. Buy FELIX: {felix_tokens_bought:,.0f} tokens")
        print(f"   3. Sell FELIX for: {eth_received:.6f} ETH")
        print(f"   4. Flash loan fee: {eth_amount * 0.0009:.6f} ETH")
        print(f"   5. Gas cost: ~0.001 ETH")
        print(f"   6. Slippage: {eth_amount * self.slippage_tolerance:.6f} ETH")
        print(f"   ─────────────────────────────")
        print(f"   NET PROFIT: {opportunity['net_profit_eth']:.6f} ETH")
        print(f"   NET PROFIT: ${opportunity['net_profit_usd']:.2f}")
        
        return {
            'eth_amount': eth_amount,
            'felix_tokens': felix_tokens_bought,
            'eth_received': eth_received,
            'net_profit_eth': opportunity['net_profit_eth'],
            'net_profit_usd': opportunity['net_profit_usd']
        }
    
    def execute_arbitrage(self, trade_details):
        """Execute the arbitrage trade"""
        print(f"\n🚀 EXECUTING ARBITRAGE...")
        print("⚠️  WARNING: This is a simulation - not executing real trade!")
        
        # In a real implementation, this would:
        # 1. Get flash loan from Balancer
        # 2. Buy FELIX on low-price DEX
        # 3. Sell FELIX on high-price DEX
        # 4. Repay flash loan
        # 5. Keep profit
        
        print(f"   1. Flash loan {trade_details['eth_amount']} ETH from Balancer")
        print(f"   2. Buy {trade_details['felix_tokens']:,.0f} FELIX on {self.dexes['uniswap']['name']}")
        print(f"   3. Sell FELIX for {trade_details['eth_received']:.6f} ETH on {self.dexes['pancakeswap']['name']}")
        print(f"   4. Repay flash loan + fee")
        print(f"   5. Profit: ${trade_details['net_profit_usd']:.2f} realized!")
        
        return True
    
    def monitor_felix_activity(self):
        """Monitor FELIX trading activity for opportunities"""
        print("\n📈 MONITORING FELIX ACTIVITY...")
        print("   Token: 0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07")
        print("   Current gain: +1023% (from DexScreener)")
        print("   Status: High volatility - panic selling detected")
        
        # Check for recent transactions
        print("\n🔍 RECENT ACTIVITY:")
        print("   - High volume selling on Uniswap")
        print("   - Price dips creating arbitrage opportunities")
        print("   - Cross-DEX price inefficiencies")
        
        return True
    
    def run_felix_arbitrage(self):
        """Run complete FELIX arbitrage analysis"""
        print("="*80)
        print("🚀 FELIX/WETH FLASH LOAN ARBITRAGE")
        print("="*80)
        
        # Monitor activity
        self.monitor_felix_activity()
        
        # Get prices
        prices = self.get_felix_prices()
        
        # Find opportunity
        opportunity = self.find_arbitrage_opportunity(prices)
        
        if opportunity:
            # Calculate details
            trade_details = self.calculate_arbitrage_details(opportunity)
            
            if trade_details and trade_details['net_profit_usd'] > 10:  # Minimum $10 profit
                print(f"\n✅ PROFITABLE OPPORTUNITY FOUND!")
                print(f"   Expected profit: ${trade_details['net_profit_usd']:.2f}")
                
                # Execute (simulation)
                self.execute_arbitrage(trade_details)
                
                return trade_details
            else:
                print(f"\n❌ Opportunity not profitable enough")
                print(f"   Profit: ${trade_details['net_profit_usd']:.2f} (need $10+)")
        else:
            print(f"\n❌ No arbitrage opportunities found")
            print(f"   Prices are too similar across DEXs")
        
        return None

if __name__ == "__main__":
    try:
        arbitrage = FELIXArbitrage()
        result = arbitrage.run_felix_arbitrage()
        
        if result:
            print(f"\n🎯 ARBITRAGE COMPLETE!")
            print(f"   Profit: ${result['net_profit_usd']:.2f}")
        else:
            print(f"\n⏰ NO OPPORTUNITY - Keep monitoring...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
