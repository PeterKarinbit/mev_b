#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time

load_dotenv("mev_bot/.env")

class CorrectArbitrage:
    def __init__(self):
        # Your Alchemy RPC
        self.w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM"))
        
        if not self.w3.is_connected():
            print("❌ Failed to connect to Alchemy")
            return
        
        print("✅ Connected to Alchemy RPC")
        
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # High-liquidity tokens for SAME-TOKEN arbitrage
        self.target_tokens = [
            {'symbol': 'USDC', 'address': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', 'decimals': 6},
            {'symbol': 'WETH', 'address': '0x4200000000000000000000000000000000000006', 'decimals': 18},
            {'symbol': 'VIRTUAL', 'address': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b', 'decimals': 18},
            {'symbol': 'DEGEN', 'address': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed', 'decimals': 18}
        ]
        
        # DEX configs for SAME-TOKEN arbitrage
        self.dexes = {
            'uniswap': {
                'factory': '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
                'router': '0x2626663106344D31dCC2e4aA7F7e9a7c576a2C0'
            },
            'sushiswap': {
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'aerodrome': {
                'factory': '0x420DD381b31aEf6683db6B902084cB0FFECe40Da',
                'router': '0xcF77a3Ba9A5CA399B7C97c74d54e5b1Beb874EC'
            }
        }
        
        # Trading parameters
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        self.max_gas_price_usd = 0.5
        self.min_profit_usd = 10
        
    def get_token_price_on_dex(self, token_address, dex_name):
        """Get SAME token price on specific DEX"""
        try:
            if dex_name == 'aerodrome':
                # Aerodrome V2 - get token/USDC price
                factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
                pool_abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"}]
                
                factory = self.w3.eth.contract(address=self.dexes[dex_name]['factory'], abi=factory_abi)
                pool_addr = factory.functions.getPool(token_address, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", False).call()
                
                if pool_addr and pool_addr != "0x0000000000000000000000000000000000000000000":
                    pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
                    reserves = pool.functions.getReserves().call()
                    if reserves:
                        # Return USDC per token
                        return reserves[0] / reserves[1]  # USDC per token
            
            else:
                # Uniswap V3/SushiSwap - get token/USDC price
                factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
                pool_abi = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
                
                factory = self.w3.eth.contract(address=self.dexes[dex_name]['factory'], abi=factory_abi)
                pool_addr = factory.functions.getPool(token_address, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 3000).call()
                
                if pool_addr and pool_addr != "0x0000000000000000000000000000000000000000000":
                    pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
                    slot0 = pool.functions.slot0().call()
                    if slot0:
                        sqrt_price = slot0[0]
                        price = (sqrt_price / (2**96))**2
                        return price  # USDC per token
                        
        except Exception as e:
            print(f"   ❌ {dex_name} error: {str(e)[:50]}...")
            return None
    
    def find_same_token_arbitrage(self):
        """Find SAME token arbitrage across DEXs"""
        print("\n🔍 SCANNING FOR SAME-TOKEN ARBITRAGE")
        print("="*60)
        
        opportunities = []
        
        for token in self.target_tokens:
            if token['symbol'] == 'USDC':
                continue  # Skip base token
                
            print(f"\n📊 {token['symbol']} across DEXs:")
            
            # Get price on all DEXs
            prices = {}
            for dex_name in self.dexes.keys():
                price = self.get_token_price_on_dex(token['address'], dex_name)
                if price:
                    prices[dex_name] = price
                    print(f"   {dex_name}: ${price:.6f} per token")
            
            # Find arbitrage (SAME token, different DEXs)
            if len(prices) >= 2:
                min_dex = min(prices, key=prices.get)
                max_dex = max(prices, key=prices.get)
                min_price = prices[min_dex]
                max_price = prices[max_dex]
                
                price_diff_pct = ((max_price - min_price) / min_price) * 100
                
                if price_diff_pct > 0.5:  # 0.5% minimum gap
                    # Calculate profit with 500 USDC
                    tokens_bought = self.flash_loan_amount / max_price  # Buy on expensive DEX
                    sell_value = tokens_bought * min_price  # Sell on cheap DEX
                    gross_profit = sell_value - self.flash_loan_amount
                    flash_fee = self.flash_loan_amount * 0.0009
                    net_profit = gross_profit - flash_fee - self.max_gas_price_usd
                    
                    if net_profit > self.min_profit_usd:
                        opportunities.append({
                            'token': token['symbol'],
                            'token_address': token['address'],
                            'buy_dex': max_dex,  # Buy where expensive
                            'sell_dex': min_dex,  # Sell where cheap
                            'buy_price': max_price,
                            'sell_price': min_price,
                            'profit_pct': price_diff_pct,
                            'net_profit_usd': net_profit
                        })
                        
                        print(f"🚀 ARBITRAGE: {token['symbol']}")
                        print(f"   Buy {max_dex}: ${max_price:.6f}")
                        print(f"   Sell {min_dex}: ${min_price:.6f}")
                        print(f"   Profit: {price_diff_pct:.2f}% (${net_profit:.2f})")
        
        return opportunities
    
    def simulate_correct_arbitrage(self, opportunity):
        """Simulate correct SAME-TOKEN arbitrage"""
        try:
            print(f"\n🎯 SIMULATING: {opportunity['token']}")
            print(f"   Flash Loan: $500 USDC")
            print(f"   Strategy: Buy {opportunity['buy_dex']}, Sell {opportunity['sell_dex']}")
            
            # Use the working signature from debug_deep.py
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,  # 500 USDC
                    True,  # buy first
                    opportunity['token_address'],  # SAME token
                    3000,  # fee tier
                    3000   # fee tier
                ]
            )
            
            # Simulate call
            result = self.w3.eth.call({
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
    
    def run_correct_bot(self):
        """Main bot with correct arbitrage logic"""
        print("🤖 CORRECTED ARBITRAGE BOT")
        print("="*60)
        print(f"💰 Flash Loan: $500 USDC")
        print(f"🎯 Strategy: SAME token across different DEXs")
        print(f"⛽ Max Gas: ${self.max_gas_price_usd}")
        print(f"💵 Min Profit: ${self.min_profit_usd}")
        
        successful_trades = 0
        total_profit = 0
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                
                opportunities = self.find_same_token_arbitrage()
                
                for opp in opportunities:
                    if self.simulate_correct_arbitrage(opp):
                        print(f"🎉 READY TO EXECUTE!")
                        print(f"💰 Expected Profit: ${opp['net_profit_usd']:.2f}")
                        
                        # Here you would execute the real trade
                        # For now, just show the opportunity
                        successful_trades += 1
                        total_profit += opp['net_profit_usd']
                        
                        print(f"📊 Total Opportunities Found: {successful_trades}")
                        print(f"💰 Potential Total Profit: ${total_profit:.2f}")
                
                print(f"⏳ Waiting 10 seconds...")
                time.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Bot stopped by user")
                print(f"📊 Results: {successful_trades} opportunities, ${total_profit:.2f} potential profit")
                break
            except Exception as e:
                print(f"❌ Loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = CorrectArbitrage()
    bot.run_correct_bot()
