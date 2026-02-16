#!/usr/bin/env python3
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time

load_dotenv("mev_bot/.env")

class FindAnyArbitrage:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM"))
        print("✅ Connected to Alchemy")
        
        self.flash_loan_contract = os.getenv("FLASH_ARB_CONTRACT")
        self.bot_address = os.getenv("BOT_ADDRESS", "0xF2B94CA9bCf9458392D207db8Ff94272F761AdDC")
        
        # ALL LIQUID TOKENS ON BASE
        self.tokens = {
            'WETH': '0x4200000000000000000000000000000000000006',
            'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
            'VIRTUAL': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b',
            'DEGEN': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed',
            'AERO': '0x9401813063411C64a1c02154d495638c4c34A210',
            'TOSHI': '0xAC1bd2486AAF3B5C0DF3625023906C7F8673329d',
            'BRETT': '0x532f27101965dd1a3c95fef19C0693A8B59E5046',
            'MOCHI': '0xF6e9327233E388ea287BCA9eFe5498858A996D74'
        }
        
        # DEX FACTORIES
        self.dexes = {
            'uniswap': '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
            'aerodrome': '0x420DD381b31aEf6683db6B902084cB0FFECe40Da',
            'sushiswap': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4'
        }
        
        self.flash_loan_amount = 500 * 10**6  # 500 USDC
        
    def get_price_aerodrome(self, token_addr):
        """Get token/USDC price on Aerodrome V2"""
        try:
            factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"stable","type":"bool"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
            pool_abi = [{"inputs":[],"name":"getReserves","outputs":[{"name":"","type":"uint112"},{"name":"","type":"uint112"},{"name":"","type":"uint32"}],"type":"function"},{"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"}]
            
            factory = self.w3.eth.contract(address=self.dexes['aerodrome'], abi=factory_abi)
            usdc_addr = self.tokens['USDC']
            
            pool_addr = factory.functions.getPool(token_addr, usdc_addr, False).call()
            if not pool_addr or pool_addr == "0x0000000000000000000000000000000000000000000":
                return None
            
            pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
            reserves = pool.functions.getReserves().call()
            token0 = pool.functions.token0().call()
            
            if reserves:
                if token0.lower() == usdc_addr.lower():
                    usdc_res, token_res = reserves[0], reserves[1]
                else:
                    token_res, usdc_res = reserves[0], reserves[1]
                
                if token_res > 0:
                    price = usdc_res / token_res
                    return price
        except:
            return None
    
    def get_price_uniswap(self, token_addr):
        """Get token/USDC price on Uniswap V3"""
        try:
            factory_abi = [{"inputs":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"type":"function"}]
            pool_abi = [{"inputs":[],"name":"slot0","outputs":[{"name":"sqrtPriceX96","type":"uint160"},{"name":"","type":"int24"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint16"},{"name":"","type":"uint8"},{"name":"","type":"bool"}],"type":"function"}]
            
            factory = self.w3.eth.contract(address=self.dexes['uniswap'], abi=factory_abi)
            usdc_addr = self.tokens['USDC']
            
            pool_addr = factory.functions.getPool(token_addr, usdc_addr, 3000).call()
            if not pool_addr or pool_addr == "0x0000000000000000000000000000000000000000000":
                return None
            
            pool = self.w3.eth.contract(address=pool_addr, abi=pool_abi)
            slot0 = pool.functions.slot0().call()
            
            if slot0:
                sqrt_price = slot0[0]
                price = (sqrt_price / (2**96))**2
                return price
        except:
            return None
    
    def find_all_opportunities(self):
        """Find arbitrage for ALL tokens"""
        print("\n🔍 SCANNING ALL TOKENS FOR ARBITRAGE")
        print("="*60)
        
        opportunities = []
        
        for token_name, token_addr in self.tokens.items():
            if token_name in ['USDC', 'WETH']:
                continue  # Skip base tokens
                
            print(f"\n📊 {token_name}:")
            
            # Get prices on both DEXs
            aero_price = self.get_price_aerodrome(token_addr)
            uni_price = self.get_price_uniswap(token_addr)
            
            if aero_price and uni_price:
                print(f"   Aerodrome: ${aero_price:.6f}")
                print(f"   Uniswap: ${uni_price:.6f}")
                
                # Check for arbitrage
                price_diff = abs(aero_price - uni_price)
                min_price = min(aero_price, uni_price)
                
                if price_diff > 0.001 and min_price > 0:  # 0.001 difference
                    profit_pct = (price_diff / min_price) * 100
                    
                    if profit_pct > 0.5:  # 0.5% minimum
                        # Calculate profit
                        tokens_bought = self.flash_loan_amount / max(aero_price, uni_price)
                        sell_value = tokens_bought * min(aero_price, uni_price)
                        gross_profit = sell_value - self.flash_loan_amount
                        flash_fee = self.flash_loan_amount * 0.0009
                        net_profit = gross_profit - flash_fee - 0.5  # gas
                        
                        if net_profit > 5:  # $5 minimum
                            buy_dex = "Aerodrome" if aero_price < uni_price else "Uniswap"
                            sell_dex = "Uniswap" if aero_price < uni_price else "Aerodrome"
                            
                            opportunities.append({
                                'token': token_name,
                                'token_addr': token_addr,
                                'buy_dex': buy_dex,
                                'sell_dex': sell_dex,
                                'buy_price': min(aero_price, uni_price),
                                'sell_price': max(aero_price, uni_price),
                                'net_profit': net_profit,
                                'profit_pct': profit_pct
                            })
                            
                            print(f"   🚀 ARBITRAGE: {profit_pct:.2f}% (${net_profit:.2f})")
                            print(f"   Buy {buy_dex}, Sell {sell_dex}")
            else:
                print(f"   ❌ No price data")
        
        return opportunities
    
    def execute_best_opportunity(self, opportunities):
        """Execute the best opportunity"""
        if not opportunities:
            print("❌ No profitable opportunities found")
            return False
        
        # Sort by profit
        opportunities.sort(key=lambda x: x['net_profit'], reverse=True)
        best = opportunities[0]
        
        print(f"\n🎯 BEST OPPORTUNITY:")
        print(f"   Token: {best['token']}")
        print(f"   Profit: ${best['net_profit']:.2f} ({best['profit_pct']:.2f}%)")
        print(f"   Buy: {best['buy_dex']} @ ${best['buy_price']:.6f}")
        print(f"   Sell: {best['sell_dex']} @ ${best['sell_price']:.6f}")
        
        try:
            execute_sel = self.w3.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
            execute_data = encode(
                ['uint256', 'bool', 'address', 'uint24', 'uint24'],
                [
                    self.flash_loan_amount,
                    True,
                    best['token_addr'],
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
            print(f"   🚀 EXECUTE TRADE NOW!")
            return True
            
        except Exception as e:
            print(f"   ❌ EXECUTION FAILED: {e}")
            return False
    
    def run_scan_once(self):
        """Just scan once and show results"""
        opportunities = self.find_all_opportunities()
        
        if opportunities:
            print(f"\n🎉 FOUND {len(opportunities)} OPPORTUNITIES!")
            for opp in opportunities:
                print(f"   {opp['token']}: ${opp['net_profit']:.2f} ({opp['profit_pct']:.2f}%)")
            
            # Try to execute best one
            self.execute_best_opportunity(opportunities)
        else:
            print("\n❌ NO ARBITRAGE OPPORTUNITIES FOUND")
    
    def run_continuous(self):
        """Run continuous scanning"""
        print("🤖 CONTINUOUS ARBITRAGE SCANNER")
        print("="*60)
        print(f"💰 Flash Loan: $500")
        print(f"🎯 Tokens: {len(self.tokens)}")
        print(f"📡 DEXs: Aerodrome + Uniswap")
        
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n🔍 Scan #{scan_count}")
                self.run_scan_once()
                
                print(f"⏳ Waiting 10 seconds...")
                time.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Scanner stopped")
                break

if __name__ == "__main__":
    bot = FindAnyArbitrage()
    
    # Run once first
    bot.run_scan_once()
    
    # Uncomment for continuous scanning
    # bot.run_continuous()
