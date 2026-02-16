#!/usr/bin/env python3
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time

load_dotenv("mev_bot/.env")

class SimpleArbitrage:
    def __init__(self):
        # Your Alchemy RPC
        self.w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM"))
        
        if not self.w3.is_connected():
            print("❌ Failed to connect to Alchemy")
            return
        
        print("✅ Connected to Alchemy RPC")
        
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # Simple token addresses
        self.USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        self.WETH = "0x4200000000000000000000000000000000000006"
        self.VIRTUAL = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
        
        # DEX factories
        self.UNISWAP_FACTORY = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
        self.AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
        
        # Flash loan amount
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        
    def get_virtual_price_uniswap(self):
        """Get VIRTUAL price on Uniswap V3"""
        try:
            # Factory ABI
            factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
            
            # Pool ABI  
            pool_abi = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
            
            # Get factory
            factory = self.w3.eth.contract(address=self.UNISWAP_FACTORY, abi=factory_abi)
            
            # Get VIRTUAL/USDC pool (3000 fee)
            pool_addr = factory.functions.getPool(self.VIRTUAL, self.USDC, 3000).call()
            
            if not pool_addr or pool_addr == "0x0000000000000000000000000000000000000000000":
                print("   ❌ No VIRTUAL/USDC pool on Uniswap")
                return None
            
            print(f"   ✅ Uniswap VIRTUAL/USDC pool: {pool_addr}")
            
            # Get pool
            pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
            slot0 = pool.functions.slot0().call()
            
            if slot0:
                sqrt_price = slot0[0]
                # Convert sqrt price to actual price
                price = (sqrt_price / (2**96))**2
                # Adjust for decimals (VIRTUAL has 18, USDC has 6)
                price_usdc = price * (10**6) / (10**18)
                
                print(f"   📊 Uniswap VIRTUAL price: ${price_usdc:.6f}")
                return price_usdc
                
        except Exception as e:
            print(f"   ❌ Uniswap error: {e}")
            return None
    
    def get_virtual_price_aerodrome(self):
        """Get VIRTUAL price on Aerodrome V2"""
        try:
            # Factory ABI
            factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
            
            # Pool ABI
            pool_abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
            
            # Get factory
            factory = self.w3.eth.contract(address=self.AERODROME_FACTORY, abi=factory_abi)
            
            # Get VIRTUAL/USDC pool
            pool_addr = factory.functions.getPool(self.VIRTUAL, self.USDC, False).call()
            
            if not pool_addr or pool_addr == "0x0000000000000000000000000000000000000000000":
                print("   ❌ No VIRTUAL/USDC pool on Aerodrome")
                return None
            
            print(f"   ✅ Aerodrome VIRTUAL/USDC pool: {pool_addr}")
            
            # Get pool
            pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
            reserves = pool.functions.getReserves().call()
            token0 = pool.functions.token0().call()
            
            if reserves:
                # Determine which reserve is USDC vs VIRTUAL
                if token0.lower() == self.USDC.lower():
                    usdc_reserve = reserves[0]
                    virtual_reserve = reserves[1]
                else:
                    usdc_reserve = reserves[1] 
                    virtual_reserve = reserves[0]
                
                # Calculate price: USDC per VIRTUAL
                price_usdc = usdc_reserve / virtual_reserve
                # Adjust for decimals
                price_usdc = price_usdc * (10**6) / (10**18)
                
                print(f"   📊 Aerodrome VIRTUAL price: ${price_usdc:.6f}")
                return price_usdc
                
        except Exception as e:
            print(f"   ❌ Aerodrome error: {e}")
            return None
    
    def check_arbitrage(self):
        """Check for VIRTUAL arbitrage between Uniswap and Aerodrome"""
        print("\n🔍 CHECKING VIRTUAL ARBITRAGE")
        print("="*60)
        
        # Get prices
        uni_price = self.get_virtual_price_uniswap()
        aero_price = self.get_virtual_price_aerodrome()
        
        if uni_price and aero_price:
            # Calculate arbitrage
            if abs(uni_price - aero_price) > 0.001:  # $0.001 difference
                if uni_price < aero_price:
                    buy_dex = "Uniswap"
                    sell_dex = "Aerodrome" 
                    buy_price = uni_price
                    sell_price = aero_price
                else:
                    buy_dex = "Aerodrome"
                    sell_dex = "Uniswap"
                    buy_price = aero_price
                    sell_price = uni_price
                
                price_diff = abs(sell_price - buy_price)
                profit_pct = (price_diff / buy_price) * 100
                
                print(f"\n🚀 ARBITRAGE OPPORTUNITY!")
                print(f"   Buy {buy_dex}: ${buy_price:.6f}")
                print(f"   Sell {sell_dex}: ${sell_price:.6f}")
                print(f"   Difference: ${price_diff:.6f} ({profit_pct:.2f}%)")
                
                # Calculate profit with 500 USDC
                virtual_bought = self.flash_loan_amount / buy_price
                sell_value = virtual_bought * sell_price
                gross_profit = sell_value - self.flash_loan_amount
                flash_fee = self.flash_loan_amount * 0.0009  # 0.09%
                net_profit = gross_profit - flash_fee - 0.5  # $0.50 gas
                
                print(f"   💰 Net profit: ${net_profit:.2f}")
                
                if net_profit > 5:  # $5 minimum
                    return True, net_profit
                else:
                    print(f"   ⚠️ Profit too low: ${net_profit:.2f}")
                    return False, 0
            else:
                print(f"   ❌ No significant price difference: ${abs(uni_price - aero_price):.6f}")
                return False, 0
        else:
            print(f"   ❌ Could not get both prices")
            return False, 0
    
    def test_flash_loan(self):
        """Test flash loan with VIRTUAL"""
        try:
            print(f"\n🎯 TESTING FLASH LOAN")
            print("="*60)
            print(f"   Flash Loan: $500 USDC")
            print(f"   Token: VIRTUAL")
            
            # Build transaction
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,  # 500 USDC
                    True,  # buy first
                    self.VIRTUAL,  # VIRTUAL token
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
            
            print(f"   ✅ SIMULATION SUCCESS!")
            print(f"   Contract response: {result.hex()[:50]}...")
            return True
            
        except Exception as e:
            print(f"   ❌ SIMULATION FAILED: {e}")
            return False
    
    def run_simple_bot(self):
        """Run simple arbitrage bot"""
        print("🤖 SIMPLE ARBITRAGE BOT - NO DEXSCREENER")
        print("="*60)
        print(f"💰 Flash Loan: $500 USDC")
        print(f"🎯 Token: VIRTUAL only")
        print(f"📡 DEXs: Uniswap + Aerodrome")
        
        scan_count = 0
        successful_tests = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                
                # Check arbitrage
                has_opportunity, profit = self.check_arbitrage()
                
                if has_opportunity:
                    print(f"\n🎯 OPPORTUNITY FOUND! Profit: ${profit:.2f}")
                    
                    # Test flash loan
                    if self.test_flash_loan():
                        successful_tests += 1
                        print(f"   🎉 Ready to execute! Test #{successful_tests}")
                        
                        # Here you would execute real trade
                        print(f"   💰 EXECUTE TRADE NOW FOR ${profit:.2f} PROFIT!")
                
                print(f"⏳ Waiting 5 seconds...")
                time.sleep(5)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Bot stopped by user")
                print(f"📊 Results: {successful_tests} opportunities found")
                break
            except Exception as e:
                print(f"❌ Loop error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    bot = SimpleArbitrage()
    bot.run_simple_bot()
