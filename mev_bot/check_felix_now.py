#!/usr/bin/env python3
"""
Check FELIX Arbitrage Opportunity - REAL TIME
- Current prices across DEXs
- Profit calculation
- Opportunity window analysis
"""

import requests
import json
from web3 import Web3
from dotenv import load_dotenv
import os
import time

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

class FELIXOpportunityChecker:
    def __init__(self):
        # Connect to Base network
        rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to RPC")
        
        print("✅ Connected to Base network")
        
        # Token addresses
        self.FELIX = "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
        self.WETH = "0x4200000000000000000000000000000000000006"
        
        # DEX routers
        self.uniswap_router = "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"
        self.pancakeswap_router = "0x1b81D678ffb9C0263b24A97847620C99d213eB14"
        self.sushiswap_router = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
        
    def get_dexscreener_data(self):
        """Get real-time data from DexScreener"""
        try:
            url = "https://api.dexscreener.com/latest/dex/tokens/0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pairs = data.get('pairs', {})
            base_pairs = [p for p in pairs.values() if p.get('chainId') == 'base']
            
            print(f"\n📊 DEXSCREENER DATA:")
            print(f"   Found {len(base_pairs)} FELIX pairs on Base")
            
            dex_prices = {}
            for pair in base_pairs:
                dex_name = pair.get('dexId', 'Unknown')
                price_usd = float(pair.get('priceUsd', 0))
                price_native = float(pair.get('priceNative', 0))
                volume_24h = float(pair.get('volume', {}).get('h24', 0))
                liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                
                if price_native > 0:
                    dex_prices[dex_name] = {
                        'price_usd': price_usd,
                        'price_native': price_native,
                        'volume_24h': volume_24h,
                        'liquidity': liquidity
                    }
                    
                    print(f"   {dex_name}:")
                    print(f"     Price: ${price_usd:.6f} ({price_native:.8f} ETH)")
                    print(f"     Volume 24h: ${volume_24h:,.0f}")
                    print(f"     Liquidity: ${liquidity:,.0f}")
            
            return dex_prices
            
        except Exception as e:
            print(f"❌ DexScreener error: {e}")
            return {}
    
    def get_coingecko_data(self):
        """Get FELIX data from CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=coinbase-wrapped-staked-eth&vs_currencies=usd,eth"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            cbeth_data = data.get('coinbase-wrapped-staked-eth', {})
            price_usd = cbeth_data.get('usd', 0)
            price_eth = cbeth_data.get('eth', 0)
            
            print(f"\n💱 COINGECKO DATA:")
            print(f"   cbETH Price: ${price_usd:.2f}")
            print(f"   ETH Price: ${1/price_eth:.2f}" if price_eth > 0 else "   ETH Price: N/A")
            
            return price_usd, price_eth
            
        except Exception as e:
            print(f"❌ CoinGecko error: {e}")
            return 0, 0
    
    def analyze_arbitrage_opportunity(self, dex_prices):
        """Analyze arbitrage opportunities"""
        print(f"\n🔍 ARBITRAGE ANALYSIS:")
        
        if len(dex_prices) < 2:
            print("   ❌ Need at least 2 DEXs for arbitrage")
            return None
        
        # Find best buy/sell opportunities
        dex_list = list(dex_prices.keys())
        best_opportunity = None
        max_spread = 0
        
        for i, buy_dex in enumerate(dex_list):
            for j, sell_dex in enumerate(dex_list):
                if i != j:
                    buy_price = dex_prices[buy_dex]['price_native']
                    sell_price = dex_prices[sell_dex]['price_native']
                    
                    if sell_price > buy_price:
                        spread_pct = ((sell_price - buy_price) / buy_price) * 100
                        
                        if spread_pct > max_spread:
                            max_spread = spread_pct
                            best_opportunity = {
                                'buy_dex': buy_dex,
                                'sell_dex': sell_dex,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'spread_pct': spread_pct,
                                'buy_liquidity': dex_prices[buy_dex]['liquidity'],
                                'sell_liquidity': dex_prices[sell_dex]['liquidity']
                            }
        
        if best_opportunity:
            print(f"   ✅ BEST OPPORTUNITY FOUND:")
            print(f"   Buy: {best_opportunity['buy_dex']} @ {best_opportunity['buy_price']:.8f} ETH")
            print(f"   Sell: {best_opportunity['sell_dex']} @ {best_opportunity['sell_price']:.8f} ETH")
            print(f"   Spread: {best_opportunity['spread_pct']:.2f}%")
            print(f"   Buy Liquidity: ${best_opportunity['buy_liquidity']:,.0f}")
            print(f"   Sell Liquidity: ${best_opportunity['sell_liquidity']:,.0f}")
            
            # Calculate profit for 1 ETH
            eth_amount = 1.0
            felix_tokens = eth_amount / best_opportunity['buy_price']
            eth_returned = felix_tokens * best_opportunity['sell_price']
            gross_profit = eth_returned - eth_amount
            
            # Costs
            flash_loan_fee = eth_amount * 0.0009  # 0.09%
            gas_cost = 0.0001  # ~$0.25 on Base
            slippage = eth_amount * 0.002  # 0.2% slippage
            
            net_profit = gross_profit - flash_loan_fee - gas_cost - slippage
            
            print(f"\n💰 PROFIT CALCULATION (1 ETH):")
            print(f"   FELIX received: {felix_tokens:,.0f}")
            print(f"   ETH returned: {eth_returned:.6f}")
            print(f"   Gross profit: {gross_profit:.6f} ETH")
            print(f"   Flash loan fee: {flash_loan_fee:.6f} ETH")
            print(f"   Gas cost: {gas_cost:.6f} ETH")
            print(f"   Slippage: {slippage:.6f} ETH")
            print(f"   ─────────────────────────────")
            print(f"   NET PROFIT: {net_profit:.6f} ETH (${net_profit * 2500:.2f})")
            
            return {
                'opportunity': best_opportunity,
                'profit_eth': net_profit,
                'profit_usd': net_profit * 2500,
                'profitable': net_profit > 0.01  # Minimum 0.01 ETH profit
            }
        else:
            print("   ❌ No profitable arbitrage opportunities found")
            return None
    
    def check_market_conditions(self):
        """Check overall market conditions"""
        print(f"\n🌍 MARKET CONDITIONS:")
        
        # Check gas price
        gas_price = self.w3.eth.gas_price
        gas_price_gwei = gas_price / 10**9
        print(f"   Gas price: {gas_price_gwei:.4f} gwei")
        print(f"   Gas status: {'✅ Low' if gas_price_gwei < 0.01 else '⚠️ High'}")
        
        # Check network congestion
        latest_block = self.w3.eth.get_block('latest')
        block_time = latest_block.timestamp - self.w3.eth.get_block(latest_block.number - 1).timestamp
        print(f"   Block time: {block_time} seconds")
        print(f"   Network: {'✅ Fast' if block_time < 3 else '⚠️ Slow'}")
        
        # Opportunity window assessment
        print(f"\n⏰ OPPORTUNITY WINDOW:")
        print(f"   Time: {time.strftime('%H:%M:%S UTC')}")
        print(f"   Status: {'✅ ACTIVE' if gas_price_gwei < 0.01 else '⚠️ WAIT'}")
    
    def run_opportunity_check(self):
        """Run complete opportunity check"""
        print("="*80)
        print("🔍 FELIX ARBITRAGE OPPORTUNITY CHECK")
        print("="*80)
        
        # Get market data
        dex_prices = self.get_dexscreener_data()
        cbeth_price, cbeth_eth = self.get_coingecko_data()
        
        # Analyze opportunities
        opportunity = self.analyze_arbitrage_opportunity(dex_prices)
        
        # Check market conditions
        self.check_market_conditions()
        
        # Summary
        print(f"\n📋 SUMMARY:")
        if opportunity and opportunity['profitable']:
            print(f"   ✅ OPPORTUNITY ACTIVE")
            print(f"   Expected profit: ${opportunity['profit_usd']:.2f} per 1 ETH")
            print(f"   Spread: {opportunity['opportunity']['spread_pct']:.2f}%")
            print(f"   Action: DEPLOY CONTRACT AND EXECUTE")
        else:
            print(f"   ❌ OPPORTUNITY NOT PROFITABLE")
            print(f"   Reason: Low spread or high costs")
            print(f"   Action: WAIT FOR BETTER CONDITIONS")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if opportunity and opportunity['profitable']:
            print(f"   1. Deploy FelixArbitrage contract")
            print(f"   2. Test with 0.1 ETH first")
            print(f"   3. Scale to 1 ETH trades")
            print(f"   4. Monitor for spread changes")
        else:
            print(f"   1. Monitor FELIX price movements")
            print(f"   2. Set up price alerts")
            print(f"   3. Wait for panic selling events")
            print(f"   4. Be ready for volatility")
        
        print(f"\n" + "="*80)
        
        return opportunity

if __name__ == "__main__":
    try:
        checker = FELIXOpportunityChecker()
        opportunity = checker.run_opportunity_check()
        
        if opportunity and opportunity['profitable']:
            print(f"\n🚀 READY TO EXECUTE!")
            print(f"   Run: python deploy_felix.py")
        else:
            print(f"\n⏰ MONITORING MODE")
            print(f"   Check again in 5-10 minutes")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
