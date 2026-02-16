#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time

load_dotenv("mev_bot/.env")

class WorkingArbitrage:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM"))
        print("✅ Connected to Alchemy")
        
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # Flash loan amount
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        
    def get_dexscreener_prices(self, token_address):
        """Get token prices from DexScreener API"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and len(data['pairs']) > 0:
                    prices = {}
                    for pair in data['pairs']:
                        dex_name = pair.get('dexId', '').lower()
                        price_usd = pair.get('priceUsd', 0)
                        volume = pair.get('volume', {}).get('h24', 0)
                        
                        if price_usd > 0 and volume > 1000:  # Minimum volume
                            prices[dex_name] = {
                                'price': price_usd,
                                'volume': volume,
                                'pair': pair
                            }
                    
                    return prices
        except Exception as e:
            print(f"   ❌ DexScreener error: {e}")
            return {}
    
    def find_arbitrage_opportunities(self):
        """Find arbitrage using DexScreener data"""
        print("\n🔍 FINDING ARBITRAGE OPPORTUNITIES")
        print("="*60)
        
        # High-volume tokens on Base
        tokens = {
            'VIRTUAL': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b',
            'DEGEN': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed',
            'AERO': '0x9401813063411C64a1c02154d495638c4c34A210',
            'TOSHI': '0xAC1bd2486AAF3B5C0DF3625023906C7F8673329d',
            'BRETT': '0x532f27101965dd1a3c95fef19C0693A8B59E5046',
            'MOCHI': '0xF6e9327233E388ea287BCA9eFe5498858A996D74'
        }
        
        opportunities = []
        
        for token_name, token_addr in tokens.items():
            print(f"\n📊 {token_name}:")
            
            # Get prices from all DEXs
            prices = self.get_dexscreener_prices(token_addr)
            
            if len(prices) >= 2:
                # Show all prices
                for dex_name, data in prices.items():
                    print(f"   {dex_name}: ${data['price']:.6f} (Vol: ${data['volume']:,.0f})")
                
                # Find best buy/sell prices
                dex_list = list(prices.keys())
                best_buy_dex = min(dex_list, key=lambda x: prices[x]['price'])
                best_sell_dex = max(dex_list, key=lambda x: prices[x]['price'])
                
                buy_price = prices[best_buy_dex]['price']
                sell_price = prices[best_sell_dex]['price']
                
                price_diff = sell_price - buy_price
                profit_pct = (price_diff / buy_price) * 100
                
                if profit_pct > 1.0:  # 1% minimum
                    # Calculate profit
                    tokens_bought = self.flash_loan_amount / buy_price
                    sell_value = tokens_bought * sell_price
                    gross_profit = sell_value - self.flash_loan_amount
                    flash_fee = self.flash_loan_amount * 0.0009
                    net_profit = gross_profit - flash_fee - 0.5  # gas
                    
                    if net_profit > 10:  # $10 minimum
                        opportunities.append({
                            'token': token_name,
                            'token_addr': token_addr,
                            'buy_dex': best_buy_dex,
                            'sell_dex': best_sell_dex,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'profit_pct': profit_pct,
                            'net_profit': net_profit,
                            'buy_volume': prices[best_buy_dex]['volume'],
                            'sell_volume': prices[best_sell_dex]['volume']
                        })
                        
                        print(f"   🚀 ARBITRAGE: {profit_pct:.2f}% (${net_profit:.2f})")
                        print(f"   Buy {best_buy_dex}, Sell {best_sell_dex}")
                else:
                    print(f"   ❌ No profitable spread: {profit_pct:.2f}%")
            else:
                print(f"   ❌ Not enough DEX data")
        
        return opportunities
    
    def execute_opportunity(self, opportunity):
        """Execute arbitrage opportunity"""
        try:
            print(f"\n🎯 EXECUTING: {opportunity['token']}")
            print(f"   Buy {opportunity['buy_dex']} @ ${opportunity['buy_price']:.6f}")
            print(f"   Sell {opportunity['sell_dex']} @ ${opportunity['sell_price']:.6f}")
            print(f"   Expected Profit: ${opportunity['net_profit']:.2f}")
            
            # Build transaction
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,
                    True,
                    opportunity['token_addr'],
                    3000,
                    3000
                ]
            )
            
            # Simulate first
            result = self.w3.eth.call({
                'from': self.bot_address,
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'value': 0
            })
            
            print(f"   ✅ SIMULATION SUCCESS!")
            
            # Check gas price
            gas_price = self.w3.eth.gas_price
            gas_cost_eth = (gas_price * 200000) / 1e18
            gas_cost_usd = gas_cost_eth * 3500  # Rough ETH price
            
            if gas_cost_usd > 0.5:
                print(f"   ⚠️ Gas too high: ${gas_cost_usd:.2f}")
                return False
            
            # Execute real trade
            tx_hash = self.w3.eth.send_transaction({
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.bot_address)
            })
            
            print(f"   🚀 TRADE SENT: {tx_hash.hex()}")
            print(f"   💰 PROFIT: ${opportunity['net_profit']:.2f}")
            print(f"   ⛽ GAS: ${gas_cost_usd:.2f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ EXECUTION FAILED: {e}")
            return False
    
    def run_once(self):
        """Run arbitrage scan once"""
        opportunities = self.find_arbitrage_opportunities()
        
        if opportunities:
            print(f"\n🎉 FOUND {len(opportunities)} OPPORTUNITIES!")
            
            # Sort by profit
            opportunities.sort(key=lambda x: x['net_profit'], reverse=True)
            
            # Show top 3
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"{i}. {opp['token']}: ${opp['net_profit']:.2f} ({opp['profit_pct']:.2f}%)")
            
            # Execute best one
            if opportunities:
                self.execute_opportunity(opportunities[0])
        else:
            print("\n❌ NO PROFITABLE ARBITRAGE FOUND")
    
    def run_continuous(self):
        """Run continuous arbitrage"""
        print("🤖 CONTINUOUS ARBITRAGE BOT")
        print("="*60)
        print(f"💰 Flash Loan: $500")
        print(f"⛽ Max Gas: $0.50")
        print(f"💵 Min Profit: $10")
        
        scan_count = 0
        total_profit = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                
                opportunities = self.find_arbitrage_opportunities()
                
                if opportunities:
                    opportunities.sort(key=lambda x: x['net_profit'], reverse=True)
                    best = opportunities[0]
                    
                    if self.execute_opportunity(best):
                        total_profit += best['net_profit']
                        print(f"🎉 TOTAL PROFIT: ${total_profit:.2f}")
                
                print(f"⏳ Waiting 15 seconds...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Bot stopped")
                print(f"📊 Total Profit: ${total_profit:.2f}")
                break

if __name__ == "__main__":
    bot = WorkingArbitrage()
    
    # Run once to test
    bot.run_once()
    
    # Uncomment for continuous
    # bot.run_continuous()
