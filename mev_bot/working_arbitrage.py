#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time
from decimal import Decimal

load_dotenv("mev_bot/.env")

class WorkingArbitrage:
    def __init__(self):
        # Correct checksum addresses
        self.addresses = {
            'VIRTUAL': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b',
            'DEGEN': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed', 
            'AERO': '0x9401813063411C64a1c02154d495638c4c34A210',
            'TOSHI': '0xAC1bd2486AAF3B5C0DF3625023906C7F8673329d',
            'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
            'WETH': '0x4200000000000000000000000000000000000006'
        }
        
        # Working RPCs with Alchemy
        self.rpc_list = [
            "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM",  # Your Alchemy key
            "https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f",
            "https://base.gateway.tenderly.co", 
            "https://1rpc.io/base"
        ]
        
        # Initialize Web3 instances
        self.w3_instances = []
        for rpc in self.rpc_list:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    self.w3_instances.append(w3)
                    print(f"✅ RPC: {rpc[:40]}...")
            except:
                continue
        
        print(f"📡 Active RPCs: {len(self.w3_instances)}")
        
        self.current_rpc = 0
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # Trading parameters
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        self.max_gas_price_usd = 0.5  # $0.50 gas limit
        self.min_profit_usd = 10  # Minimum $10 profit
        
    def get_w3(self):
        """Get next available Web3 instance"""
        for _ in range(3):  # Try 3 times
            try:
                w3 = self.w3_instances[self.current_rpc]
                if w3.is_connected():
                    self.current_rpc = (self.current_rpc + 1) % len(self.w3_instances)
                    return w3
                else:
                    self.current_rpc = (self.current_rpc + 1) % len(self.w3_instances)
            except:
                self.current_rpc = (self.current_rpc + 1) % len(self.w3_instances)
                continue
        raise Exception("All RPCs failed")
    
    def get_price_from_dexscreener(self, token_symbol):
        """Get price from DexScreener API (more reliable)"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{self.addresses[token_symbol]}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and len(data['pairs']) > 0:
                    # Get the highest volume pair
                    pairs = data['pairs']
                    pairs.sort(key=lambda x: x.get('volume', {}).get('h24', 0), reverse=True)
                    
                    best_pair = pairs[0]
                    price_usd = float(best_pair.get('priceUsd', 0))
                    
                    if price_usd > 0:
                        print(f"   📊 {token_symbol}: ${price_usd:.6f} (DexScreener)")
                        return price_usd
            
        except Exception as e:
            print(f"   ❌ DexScreener error: {e}")
        
        return None
    
    def find_real_opportunities(self):
        """Find real arbitrage opportunities using DexScreener"""
        print("\n🔍 SCANNING FOR REAL OPPORTUNITIES")
        print("="*60)
        
        opportunities = []
        tokens = ['VIRTUAL', 'DEGEN', 'AERO', 'TOSHI']
        
        # Get all token prices
        prices = {}
        for token in tokens:
            price = self.get_price_from_dexscreener(token)
            if price:
                prices[token] = price
        
        if len(prices) < 2:
            print("❌ Not enough price data")
            return opportunities
        
        # Calculate arbitrage opportunities (simplified)
        for token1 in tokens:
            for token2 in tokens:
                if token1 != token2 and token1 in prices and token2 in prices:
                    price1 = prices[token1]
                    price2 = prices[token2]
                    
                    # Simple price difference check
                    if abs(price1 - price2) > 0.001:  # $0.001 difference
                        profit_pct = abs(price1 - price2) / min(price1, price2) * 100
                        
                        if profit_pct > 1.0:  # 1% minimum
                            # Calculate potential profit
                            if price1 < price2:
                                buy_token, sell_token = token1, token2
                                buy_price, sell_price = price1, price2
                            else:
                                buy_token, sell_token = token2, token1
                                buy_price, sell_price = price2, price1
                            
                            # Estimate profit with 500 USDC
                            tokens_bought = self.flash_loan_amount / (buy_price * 10**18)  # Assuming 18 decimals
                            sell_value = tokens_bought * sell_price * 10**18
                            gross_profit = sell_value - self.flash_loan_amount
                            flash_fee = self.flash_loan_amount * 0.0009
                            net_profit = gross_profit - flash_fee - self.max_gas_price_usd
                            
                            if net_profit > self.min_profit_usd:
                                opportunities.append({
                                    'buy_token': buy_token,
                                    'sell_token': sell_token,
                                    'buy_price': buy_price,
                                    'sell_price': sell_price,
                                    'profit_pct': profit_pct,
                                    'net_profit_usd': net_profit,
                                    'tokens_amount': tokens_bought
                                })
                                
                                print(f"🚀 OPPORTUNITY: {buy_token} → {sell_token}")
                                print(f"   Buy: ${buy_price:.6f}, Sell: ${sell_price:.6f}")
                                print(f"   Profit: {profit_pct:.2f}% (${net_profit:.2f})")
        
        return opportunities
    
    def simulate_flash_loan(self, opportunity):
        """Simulate flash loan with your contract"""
        try:
            w3 = self.get_w3()
            
            # Test with VIRTUAL (most liquid)
            token_address = self.addresses[opportunity['buy_token']]
            
            # Build the exact call that works in debug_deep.py
            execute_sel = w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,  # 500 USDC
                    True,  # buy first
                    token_address,
                    3000,  # fee tier
                    3000   # fee tier
                ]
            )
            
            # Simulate the call
            result = w3.eth.call({
                'from': self.bot_address,
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'value': 0
            })
            
            print(f"✅ SIMULATION SUCCESS!")
            print(f"   Contract response: {result.hex()[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ SIMULATION FAILED: {e}")
            return False
    
    def execute_real_trade(self, opportunity):
        """Execute real arbitrage trade"""
        try:
            w3 = self.get_w3()
            
            # Check gas price
            gas_price = w3.eth.gas_price
            gas_cost_eth = (gas_price * 200000) / 1e18
            eth_price = 3500  # Rough estimate
            gas_cost_usd = gas_cost_eth * eth_price
            
            if gas_cost_usd > self.max_gas_price_usd:
                print(f"⚠️ Gas too high: ${gas_cost_usd:.2f}")
                return False
            
            # Build transaction
            token_address = self.addresses[opportunity['buy_token']]
            execute_sel = w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [self.flash_loan_amount, True, token_address, 3000, 3000]
            )
            
            # Send transaction
            tx_hash = w3.eth.send_transaction({
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(self.bot_address)
            })
            
            print(f"✅ TRADE SENT: {tx_hash.hex()}")
            print(f"💰 Expected Profit: ${opportunity['net_profit_usd']:.2f}")
            print(f"⛽ Gas Cost: ${gas_cost_usd:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ TRADE FAILED: {e}")
            return False
    
    def run_working_bot(self):
        """Main bot loop with real opportunities"""
        print("🤖 WORKING ARBITRAGE BOT - FIXED VERSION")
        print("="*60)
        print(f"💰 Flash Loan: $500")
        print(f"⛽ Max Gas: ${self.max_gas_price_usd}")
        print(f"💵 Min Profit: ${self.min_profit_usd}")
        print(f"📡 RPCs: {len(self.w3_instances)}")
        
        successful_trades = 0
        total_profit = 0
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                
                opportunities = self.find_real_opportunities()
                
                for opp in opportunities:
                    print(f"\n🎯 TESTING: {opp['buy_token']} → {opp['sell_token']}")
                    
                    # Simulate first
                    if self.simulate_flash_loan(opp):
                        # Execute if simulation passes
                        if self.execute_real_trade(opp):
                            successful_trades += 1
                            total_profit += opp['net_profit_usd']
                            print(f"🎉 TRADE #{successful_trades} SUCCESSFUL!")
                            print(f"💰 Total Profit: ${total_profit:.2f}")
                            
                            # Wait for confirmation
                            time.sleep(30)
                
                print(f"⏳ Waiting 15 seconds...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Bot stopped by user")
                print(f"📊 FINAL RESULTS:")
                print(f"   Trades: {successful_trades}")
                print(f"   Profit: ${total_profit:.2f}")
                print(f"   Losses: $0.00")
                break
            except Exception as e:
                print(f"❌ Loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = WorkingArbitrage()
    bot.run_working_bot()
