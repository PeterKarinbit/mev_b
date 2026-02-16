#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time
import threading
from queue import Queue
from decimal import Decimal

load_dotenv("mev_bot/.env")

class OptimizedArbitrage:
    def __init__(self):
        # Optimized RPC list with rotation
        self.rpc_list = [
            "https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f",
            "https://base.gateway.tenderly.co", 
            "https://1rpc.io/base",
            "https://mainnet.base.org",
            "https://base.publicnode.com"
        ]
        
        # Initialize Web3 instances
        self.w3_instances = []
        for rpc in self.rpc_list:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    self.w3_instances.append(w3)
                    print(f"✅ Connected: {rpc[:50]}...")
            except:
                continue
        
        print(f"📡 Active RPCs: {len(self.w3_instances)}/{len(self.rpc_list)}")
        
        self.current_rpc = 0
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # High-frequency tokens
        self.target_tokens = [
            {'symbol': 'VIRTUAL', 'address': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b', 'decimals': 18},
            {'symbol': 'DEGEN', 'address': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed', 'decimals': 18},
            {'symbol': 'AERO', 'address': '0x9401813063411C64a1C02154D495638C4C34a210', 'decimals': 18},
            {'symbol': 'TOSHI', 'address': '0xAC1Bd2486aAf3b5C0df3625023906C7f8673329D', 'decimals': 18}
        ]
        
        # Trading parameters
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        self.max_gas_price_gwei = 0.5  # $0.50 gas limit
        self.min_profit_usd = 10  # Minimum $10 profit
        
        # Cache for performance
        self.price_cache = {}
        self.cache_timeout = 5  # 5 seconds cache
        
    def get_w3(self):
        """Get next available Web3 instance with rotation"""
        max_retries = len(self.w3_instances)
        
        for _ in range(max_retries):
            try:
                w3 = self.w3_instances[self.current_rpc]
                # Test if still responsive
                if w3.is_connected():
                    self.current_rpc = (self.current_rpc + 1) % len(self.w3_instances)
                    return w3
                else:
                    # Try to reconnect
                    self.current_rpc = (self.current_rpc + 1) % len(self.w3_instances)
            except:
                self.current_rpc = (self.current_rpc + 1) % len(self.w3_instances)
                continue
        
        raise Exception("All RPCs failed")
    
    def get_cached_price(self, token_address, dex_name):
        """Get cached price or fetch new one"""
        cache_key = f"{token_address}_{dex_name}"
        current_time = time.time()
        
        if cache_key in self.price_cache:
            cached_time, cached_price = self.price_cache[cache_key]
            if current_time - cached_time < self.cache_timeout:
                return cached_price
        
        # Fetch new price
        price = self.get_token_price(token_address, dex_name)
        if price:
            self.price_cache[cache_key] = (current_time, price)
        
        return price
    
    def get_token_price(self, token_address, dex_name):
        """Get token price with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                w3 = self.get_w3()
                
                if dex_name == 'aerodrome':
                    # Aerodrome V2 pricing
                    factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
                    pool_abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"}]
                    
                    factory = w3.eth.contract(address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da", abi=factory_abi)
                    pool_addr = factory.functions.getPool(token_address, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", False).call()
                    
                    if pool_addr and pool_addr != "0x0000000000000000000000000000000000000000000":
                        pool = w3.eth.contract(address=pool_addr, abi=pool_abi)
                        reserves = pool.functions.getReserves().call()
                        if reserves:
                            return reserves[1] / reserves[0]  # token per USDC
                
                else:
                    # Uniswap V3 pricing (simplified)
                    factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
                    pool_abi = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
                    
                    if dex_name == 'uniswap':
                        factory_addr = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
                    else:  # sushiswap
                        factory_addr = "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
                    
                    factory = w3.eth.contract(address=factory_addr, abi=factory_abi)
                    pool_addr = factory.functions.getPool(token_address, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 3000).call()
                    
                    if pool_addr and pool_addr != "0x0000000000000000000000000000000000000000000":
                        pool = w3.eth.contract(address=pool_addr, abi=pool_abi)
                        slot0 = pool.functions.slot0().call()
                        if slot0:
                            sqrt_price = slot0[0]
                            return (sqrt_price / (2**96))**2
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"❌ Price fetch failed for {dex_name}: {e}")
                time.sleep(0.1)  # Brief delay between retries
        
        return None
    
    def find_opportunities_fast(self):
        """Fast opportunity finding with caching"""
        opportunities = []
        
        for token in self.target_tokens:
            print(f"\n📊 {token['symbol']}...")
            
            # Get prices from all DEXs (with caching)
            prices = {}
            dexes = ['uniswap', 'sushiswap', 'aerodrome']
            
            for dex in dexes:
                price = self.get_cached_price(token['address'], dex)
                if price:
                    prices[dex] = price
                    print(f"   {dex}: ${price:.6f}")
            
            # Find arbitrage
            if len(prices) >= 2:
                min_dex = min(prices, key=prices.get)
                max_dex = max(prices, key=prices.get)
                min_price = prices[min_dex]
                max_price = prices[max_dex]
                
                price_diff_pct = ((max_price - min_price) / min_price) * 100
                
                if price_diff_pct > 0.5:  # 0.5% minimum gap
                    # Calculate profit
                    tokens_bought = self.flash_loan_amount / min_price
                    sell_value = tokens_bought * max_price
                    gross_profit = sell_value - self.flash_loan_amount
                    flash_fee = self.flash_loan_amount * 0.0009
                    net_profit = gross_profit - flash_fee - 0.5  # $0.50 gas
                    
                    if net_profit > self.min_profit_usd:
                        opportunities.append({
                            'token': token['symbol'],
                            'token_address': token['address'],
                            'buy_dex': min_dex,
                            'sell_dex': max_dex,
                            'profit_pct': price_diff_pct,
                            'net_profit_usd': net_profit
                        })
                        
                        print(f"🚀 OPPORTUNITY: {price_diff_pct:.2f}% (${net_profit:.2f})")
        
        return opportunities
    
    def execute_trade_fast(self, opportunity):
        """Execute trade with optimized gas"""
        try:
            w3 = self.get_w3()
            
            # Check gas price
            gas_price = w3.eth.gas_price
            gas_cost_eth = (gas_price * 200000) / 1e18
            gas_cost_usd = gas_cost_eth * 3500  # Rough ETH price
            
            if gas_cost_usd > self.max_gas_price_gwei:
                print(f"⚠️ Gas too high: ${gas_cost_usd:.2f}")
                return False
            
            # Build transaction
            execute_sel = w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [self.flash_loan_amount, True, opportunity['token_address'], 3000, 3000]
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
            print(f"💰 Expected: ${opportunity['net_profit_usd']:.2f}")
            return True
            
        except Exception as e:
            print(f"❌ Trade failed: {e}")
            return False
    
    def run_optimized_bot(self):
        """Main bot loop with optimizations"""
        print("🤖 OPTIMIZED HIGH-FREQ ARBITRAGE")
        print("="*60)
        print(f"📡 RPCs: {len(self.w3_instances)} active")
        print(f"💰 Flash Loan: $500")
        print(f"⛽ Max Gas: $0.50")
        print(f"💵 Min Profit: $10")
        print(f"🎯 Tokens: {len(self.target_tokens)}")
        
        successful_trades = 0
        total_profit = 0
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                
                opportunities = self.find_opportunities_fast()
                
                for opp in opportunities:
                    print(f"\n🎯 EXECUTING: {opp['token']} ({opp['profit_pct']:.2f}%)")
                    
                    if self.execute_trade_fast(opp):
                        successful_trades += 1
                        total_profit += opp['net_profit_usd']
                        print(f"🎉 TRADE #{successful_trades}!")
                        print(f"💰 Total: ${total_profit:.2f}")
                        
                        # Clear cache after successful trade
                        self.price_cache.clear()
                
                print(f"⏳ Waiting 5 seconds...")
                time.sleep(5)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Bot stopped by user")
                print(f"📊 Results: {successful_trades} trades, ${total_profit:.2f} profit")
                break
            except Exception as e:
                print(f"❌ Loop error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    bot = OptimizedArbitrage()
    bot.run_optimized_bot()
