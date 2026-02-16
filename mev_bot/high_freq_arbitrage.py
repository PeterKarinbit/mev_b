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

class HighFreqArbitrage:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # DEX configurations on Base
        self.dexes = {
            'uniswap': {
                'factory': '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
                'router': '0x2626663106344D31dCC2e4aA7F7e9a7c576a2C0',
                'fee': 3000
            },
            'sushiswap': {
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4', 
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'fee': 3000
            },
            'aerodrome': {
                'factory': '0x420DD381b31aEf6683db6B902084cB0FFECe40Da',
                'router': '0xcF77a3Ba9A5CA399B7C97c74d54e5b1Beb874EC',
                'fee': 0  # V2 has different fee structure
            }
        }
        
        # High-volume tokens for arbitrage
        self.target_tokens = [
            {'symbol': 'WETH', 'address': '0x4200000000000000000000000000000000000006', 'decimals': 18},
            {'symbol': 'USDC', 'address': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', 'decimals': 6},
            {'symbol': 'VIRTUAL', 'address': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b', 'decimals': 18},
            {'symbol': 'DEGEN', 'address': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed', 'decimals': 18},
            {'symbol': 'AERO', 'address': '0x9401813063411C64a1C02154D495638C4C34a210', 'decimals': 18},
            {'symbol': 'TOSHI', 'address': '0xAC1Bd2486aAf3b5C0df3625023906C7f8673329D', 'decimals': 18}
        ]
        
        # Flash loan parameters
        self.flash_loan_amount = 500 * 10**6  # 500 USDC in wei
        self.max_gas_price_gwei = 0.5  # $0.50 gas limit
        self.min_profit_usd = 10  # Minimum $10 profit per trade
        
    def get_token_price(self, token_address, base_token='USDC', dex_name='uniswap'):
        """Get token price from specific DEX"""
        try:
            dex_config = self.dexes[dex_name]
            
            if dex_name == 'aerodrome':
                # Aerodrome V2 pricing
                factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
                pool_abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"}]
            else:
                # Uniswap V3/SushiSwap pricing
                factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
                pool_abi = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
            
            factory = self.w3.eth.contract(address=dex_config['factory'], abi=factory_abi)
            
            if base_token == 'USDC':
                base_address = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
            else:
                base_address = '0x4200000000000000000000000000000000000006'
            
            # Get pool address
            if dex_name == 'aerodrome':
                pool_addr = factory.functions.getPool(token_address, base_address, False).call()
            else:
                pool_addr = factory.functions.getPool(token_address, base_address, dex_config['fee']).call()
            
            if not pool_addr or pool_addr == "0x0000000000000000000000000000000000000000000":
                return None
            
            # Get price from pool
            pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
            
            if dex_name == 'aerodrome':
                reserves = pool.functions.getReserves().call()
                if reserves:
                    token0 = pool.functions.token0().call()
                    if token0.lower() == base_address.lower():
                        price = reserves[1] / reserves[0]  # token per base
                    else:
                        price = reserves[0] / reserves[1]  # token per base
                    return price
            else:
                slot0 = pool.functions.slot0().call()
                if slot0:
                    sqrt_price = slot0[0]
                    price = (sqrt_price / (2**96))**2
                    return price
            
        except Exception as e:
            print(f"❌ Error getting {dex_name} price: {e}")
            return None
    
    def find_arbitrage_opportunities(self):
        """Find profitable arbitrage opportunities across DEXs"""
        print("🔍 SCANNING FOR ARBITRAGE OPPORTUNITIES")
        print("="*60)
        
        opportunities = []
        
        for token in self.target_tokens:
            if token['symbol'] in ['USDC', 'WETH']:
                continue  # Skip base tokens
                
            print(f"\n📊 Analyzing {token['symbol']}...")
            
            # Get prices from all DEXs
            prices = {}
            for dex_name in self.dexes.keys():
                price = self.get_token_price(token['address'], 'USDC', dex_name)
                if price:
                    prices[dex_name] = price
                    print(f"   {dex_name}: ${price:.6f}")
            
            # Find arbitrage opportunities
            if len(prices) >= 2:
                min_dex = min(prices, key=prices.get)
                max_dex = max(prices, key=prices.get)
                min_price = prices[min_dex]
                max_price = prices[max_dex]
                
                price_diff = max_price - min_price
                profit_pct = (price_diff / min_price) * 100
                
                # Calculate potential profit with 500 USDC
                if min_price > 0:
                    tokens_bought = self.flash_loan_amount / (min_price * 10**token['decimals'])
                    sell_value = tokens_bought * max_price * 10**token['decimals']
                    gross_profit = sell_value - self.flash_loan_amount
                    flash_fee = self.flash_loan_amount * 0.0009  # 0.09% Balancer fee
                    gas_cost_usd = 0.5  # $0.50 gas limit
                    net_profit = gross_profit - flash_fee - gas_cost_usd
                    
                    if net_profit > self.min_profit_usd:
                        opportunities.append({
                            'token': token['symbol'],
                            'token_address': token['address'],
                            'buy_dex': min_dex,
                            'sell_dex': max_dex,
                            'buy_price': min_price,
                            'sell_price': max_price,
                            'profit_pct': profit_pct,
                            'net_profit_usd': net_profit,
                            'tokens_amount': tokens_bought
                        })
                        
                        print(f"🚀 OPPORTUNITY FOUND!")
                        print(f"   Buy: {min_dex} @ ${min_price:.6f}")
                        print(f"   Sell: {max_dex} @ ${max_price:.6f}")
                        print(f"   Profit: {profit_pct:.2f}% (${net_profit:.2f})")
        
        return opportunities
    
    def simulate_arbitrage_trade(self, opportunity):
        """Simulate the arbitrage trade"""
        print(f"\n🎯 SIMULATING ARBITRAGE TRADE")
        print("="*60)
        print(f"Token: {opportunity['token']}")
        print(f"Buy: {opportunity['buy_dex']} @ ${opportunity['buy_price']:.6f}")
        print(f"Sell: {opportunity['sell_dex']} @ ${opportunity['sell_price']:.6f}")
        print(f"Expected Profit: ${opportunity['net_profit_usd']:.2f}")
        
        try:
            # Build flash loan call
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,
                    True,  # buy first
                    opportunity['token_address'],
                    3000,  # fee tier
                    3000   # fee tier
                ]
            )
            
            # Simulate the call
            result = self.w3.eth.call({
                'from': self.bot_address,
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'value': 0
            })
            
            print(f"✅ SIMULATION SUCCESS!")
            print(f"Result: {result.hex()[:50]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ SIMULATION FAILED: {e}")
            return False
    
    def execute_real_trade(self, opportunity):
        """Execute real arbitrage trade"""
        print(f"\n🚀 EXECUTING REAL TRADE")
        print("="*60)
        
        try:
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,
                    True,
                    opportunity['token_address'],
                    3000,
                    3000
                ]
            )
            
            # Check current gas price
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = gas_price / 1e9
            gas_cost_eth = (gas_price * 200000) / 1e18  # 200k gas estimate
            eth_price = 3500  # Rough estimate
            gas_cost_usd = gas_cost_eth * eth_price
            
            if gas_cost_usd > self.max_gas_price_gwei:
                print(f"⚠️ Gas too high: ${gas_cost_usd:.2f} > ${self.max_gas_price_gwei}")
                return False
            
            # Send transaction
            tx_hash = self.w3.eth.send_transaction({
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.bot_address)
            })
            
            print(f"✅ TRADE SENT: {tx_hash.hex()}")
            print(f"Expected Profit: ${opportunity['net_profit_usd']:.2f}")
            print(f"Gas Cost: ${gas_cost_usd:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ TRADE FAILED: {e}")
            return False
    
    def run_arbitrage_bot(self):
        """Main arbitrage bot loop"""
        print("🤖 HIGH-FREQ ARBITRAGE BOT - 500 USDC FLASH LOANS")
        print("="*60)
        print(f"💰 Flash Loan Amount: $500")
        print(f"⛽ Max Gas Cost: $0.50")
        print(f"💵 Min Profit: $10")
        print(f"📊 Monitoring {len(self.target_tokens)} tokens")
        
        successful_trades = 0
        total_profit = 0
        
        while True:
            try:
                opportunities = self.find_arbitrage_opportunities()
                
                for opp in opportunities:
                    print(f"\n🎯 OPPORTUNITY: {opp['token']}")
                    print(f"Profit: ${opp['net_profit_usd']:.2f} ({opp['profit_pct']:.2f}%)")
                    
                    # Simulate first
                    if self.simulate_arbitrage_trade(opp):
                        # Execute if simulation passes
                        if self.execute_real_trade(opp):
                            successful_trades += 1
                            total_profit += opp['net_profit_usd']
                            print(f"🎉 TRADE #{successful_trades} SUCCESSFUL!")
                            print(f"💰 Total Profit: ${total_profit:.2f}")
                
                print(f"\n⏳ Waiting 10 seconds...")
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = HighFreqArbitrage()
    bot.run_arbitrage_bot()
