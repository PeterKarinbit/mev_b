#!/usr/bin/env python3
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time

load_dotenv("mev_bot/.env")

class SimpleWorkingArbitrage:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM"))
        print("✅ Connected to Alchemy")
        
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # Just focus on VIRTUAL - highest volume
        self.VIRTUAL = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
        self.USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        
        # DEX addresses
        self.UNISWAP_V3_ROUTER = "0x2626663106344D31dCC2e4aA7F7e9a7c576a2C0"
        self.AERODROME_ROUTER = "0xcF77a3Ba9A5CA399B7C97c74d54e5b1Beb874EC"
        
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        
    def get_virtual_price_uniswap(self):
        """Get VIRTUAL price from Uniswap V3 using router"""
        try:
            # Simple router call to get amount out
            router_abi = [
                {"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"components":[{"name":"token","type":"address"},{"name":"amount","type":"uint256"},{"name":"weight","type":"uint256"}],"name":"path","type":"tuple[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"type":"function","stateMutability":"view"}
            ]
            
            router = self.w3.eth.contract(address=self.UNISWAP_V3_ROUTER, abi=router_abi)
            
            # Try to swap 1 USDC for VIRTUAL
            path = [self.USDC, self.VIRTUAL]
            amount_in = 1 * 10**6  # 1 USDC
            
            amounts = router.functions.getAmountsOut(amount_in, path).call()
            
            if amounts and len(amounts) >= 2:
                virtual_out = amounts[1]
                price = amount_in / virtual_out  # USDC per VIRTUAL
                print(f"   📊 Uniswap: 1 VIRTUAL = ${price:.6f} USDC")
                return price
                
        except Exception as e:
            print(f"   ❌ Uniswap error: {str(e)[:50]}...")
            return None
    
    def get_virtual_price_aerodrome(self):
        """Get VIRTUAL price from Aerodrome using router"""
        try:
            # Aerodrome V2 router ABI
            router_abi = [
                {"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"components":[{"name":"token","type":"address"},{"name":"amount","type":"uint256"},{"name":"weight","type":"uint256"}],"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"type":"function","stateMutability":"view"}
            ]
            
            router = self.w3.eth.contract(address=self.AERODROME_ROUTER, abi=router_abi)
            
            # Try to swap 1 USDC for VIRTUAL
            path = [self.USDC, self.VIRTUAL]
            amount_in = 1 * 10**6  # 1 USDC
            
            amounts = router.functions.getAmountsOut(amount_in, path).call()
            
            if amounts and len(amounts) >= 2:
                virtual_out = amounts[1]
                price = amount_in / virtual_out  # USDC per VIRTUAL
                print(f"   📊 Aerodrome: 1 VIRTUAL = ${price:.6f} USDC")
                return price
                
        except Exception as e:
            print(f"   ❌ Aerodrome error: {str(e)[:50]}...")
            return None
    
    def check_arbitrage(self):
        """Check VIRTUAL arbitrage"""
        print("\n🔍 CHECKING VIRTUAL ARBITRAGE")
        print("="*60)
        
        # Get prices
        uni_price = self.get_virtual_price_uniswap()
        aero_price = self.get_virtual_price_aerodrome()
        
        if uni_price and aero_price:
            price_diff = abs(uni_price - aero_price)
            min_price = min(uni_price, aero_price)
            max_price = max(uni_price, aero_price)
            
            if price_diff > 0.001:  # $0.001 difference
                profit_pct = (price_diff / min_price) * 100
                
                print(f"\n📊 PRICE COMPARISON:")
                print(f"   Uniswap: ${uni_price:.6f}")
                print(f"   Aerodrome: ${aero_price:.6f}")
                print(f"   Difference: ${price_diff:.6f} ({profit_pct:.3f}%)")
                
                if profit_pct > 0.5:  # 0.5% minimum
                    # Calculate profit with 500 USDC
                    virtual_bought = self.flash_loan_amount / max_price
                    sell_value = virtual_bought * min_price
                    gross_profit = sell_value - self.flash_loan_amount
                    flash_fee = self.flash_loan_amount * 0.0009
                    net_profit = gross_profit - flash_fee - 0.5  # gas
                    
                    print(f"\n🚀 ARBITRAGE OPPORTUNITY:")
                    print(f"   Buy where expensive: ${max_price:.6f}")
                    print(f"   Sell where cheap: ${min_price:.6f}")
                    print(f"   Net profit: ${net_profit:.2f}")
                    
                    if net_profit > 5:  # $5 minimum
                        return True, net_profit, max_price > min_price
                    else:
                        print(f"   ⚠️ Profit too low: ${net_profit:.2f}")
                        return False, 0, False
                else:
                    print(f"   ❌ Spread too small: {profit_pct:.3f}%")
                    return False, 0, False
            else:
                print(f"   ❌ No significant difference: ${price_diff:.6f}")
                return False, 0, False
        else:
            print(f"   ❌ Could not get prices")
            return False, 0, False
    
    def test_flash_loan(self, buy_first):
        """Test flash loan execution"""
        try:
            print(f"\n🎯 TESTING FLASH LOAN")
            print(f"   Strategy: {'Buy first' if buy_first else 'Sell first'}")
            
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,
                    buy_first,
                    self.VIRTUAL,
                    3000,
                    3000
                ]
            )
            
            result = self.w3.eth.call({
                'from': self.bot_address,
                'to': self.flash_loan_contract,
                'data': '0x' + (execute_sel + execute_data).hex(),
                'value': 0
            })
            
            print(f"   ✅ SIMULATION SUCCESS!")
            print(f"   Contract response: {result.hex()[:30]}...")
            return True
            
        except Exception as e:
            print(f"   ❌ SIMULATION FAILED: {e}")
            return False
    
    def run_scan(self):
        """Run arbitrage scan"""
        print("🤖 SIMPLE VIRTUAL ARBITRAGE")
        print("="*60)
        print(f"💰 Flash Loan: $500 USDC")
        print(f"🎯 Token: VIRTUAL")
        print(f"📡 DEXs: Uniswap + Aerodrome")
        
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                
                has_opportunity, profit, buy_first = self.check_arbitrage()
                
                if has_opportunity:
                    print(f"\n🎯 OPPORTUNITY! Profit: ${profit:.2f}")
                    
                    if self.test_flash_loan(buy_first):
                        print(f"\n🚀 READY TO EXECUTE!")
                        print(f"💰 EXECUTE NOW FOR ${profit:.2f} PROFIT!")
                        
                        # Here you would execute real transaction
                        # For now, just show it's ready
                
                print(f"⏳ Waiting 10 seconds...")
                time.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Scanner stopped")
                break

if __name__ == "__main__":
    bot = SimpleWorkingArbitrage()
    bot.run_scan()
