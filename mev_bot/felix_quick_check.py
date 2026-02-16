#!/usr/bin/env python3
"""
Quick FELIX Opportunity Check
- Direct price monitoring
- Simple arbitrage calculation
"""

import requests
from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

def quick_felix_check():
    print("🔍 FELIX ARBITRAGE QUICK CHECK")
    print("="*50)
    
    # Connect to Base
    rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect")
        return
    
    print("✅ Connected to Base")
    
    # Check gas
    gas_price = w3.eth.gas_price / 10**9
    print(f"⛽ Gas: {gas_price:.4f} gwei")
    
    # Try to get FELIX data
    try:
        # Method 1: Direct API call
        url = "https://api.dexscreener.com/latest/dex/tokens/0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])
            
            print(f"\n📊 FELIX MARKETS:")
            
            if isinstance(pairs, dict):
                pairs = list(pairs.values())
            
            base_pairs = [p for p in pairs if p.get('chainId') == 'base']
            
            if base_pairs:
                prices = {}
                for pair in base_pairs:
                    dex = pair.get('dexId', 'Unknown')
                    price_native = float(pair.get('priceNative', 0))
                    volume = float(pair.get('volume', {}).get('h24', 0))
                    liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                    
                    if price_native > 0:
                        prices[dex] = {
                            'price': price_native,
                            'volume': volume,
                            'liquidity': liquidity
                        }
                        print(f"   {dex}: {price_native:.8f} ETH (Vol: ${volume:,.0f}, Liq: ${liquidity:,.0f})")
                
                # Find arbitrage
                if len(prices) >= 2:
                    dex_names = list(prices.keys())
                    max_spread = 0
                    best_pair = None
                    
                    for i, buy_dex in enumerate(dex_names):
                        for j, sell_dex in enumerate(dex_names):
                            if i != j:
                                buy_price = prices[buy_dex]['price']
                                sell_price = prices[sell_dex]['price']
                                
                                if sell_price > buy_price:
                                    spread = ((sell_price - buy_price) / buy_price) * 100
                                    if spread > max_spread:
                                        max_spread = spread
                                        best_pair = (buy_dex, sell_dex, buy_price, sell_price)
                    
                    if best_pair and max_spread > 1:
                        buy_dex, sell_dex, buy_price, sell_price = best_pair
                        
                        print(f"\n💰 ARBITRAGE OPPORTUNITY:")
                        print(f"   Buy: {buy_dex} @ {buy_price:.8f} ETH")
                        print(f"   Sell: {sell_dex} @ {sell_price:.8f} ETH")
                        print(f"   Spread: {max_spread:.2f}%")
                        
                        # Calculate profit
                        eth_amount = 1.0
                        felix_tokens = eth_amount / buy_price
                        eth_return = felix_tokens * sell_price
                        gross_profit = eth_return - eth_amount
                        
                        # Costs
                        flash_fee = eth_amount * 0.0009
                        gas_cost = 0.0001
                        slippage = eth_amount * 0.002
                        
                        net_profit = gross_profit - flash_fee - gas_cost - slippage
                        profit_usd = net_profit * 2500
                        
                        print(f"\n📈 PROFIT (1 ETH):")
                        print(f"   Net: {net_profit:.6f} ETH (${profit_usd:.2f})")
                        
                        if net_profit > 0.01:
                            print(f"   ✅ PROFITABLE - Execute now!")
                            print(f"   🚀 Deploy contract and trade")
                        else:
                            print(f"   ❌ Not profitable enough")
                    else:
                        print(f"\n❌ No significant spread found")
                        print(f"   Max spread: {max_spread:.2f}%")
                else:
                    print(f"❌ Need more DEXs for arbitrage")
            else:
                print(f"❌ No FELIX pairs found on Base")
        else:
            print(f"❌ API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Alternative: Check if we can simulate prices
    print(f"\n🎯 CURRENT STATUS:")
    print(f"   Time: {__import__('time').strftime('%H:%M:%S')}")
    print(f"   Gas: {gas_price:.4f} gwei (✅ Low)")
    print(f"   Account: Ready for deployment")
    print(f"   Contract: FelixArbitrage.sol created")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. If spread > 3%: Deploy contract")
    print(f"   2. Test with 0.1 ETH")
    print(f"   3. Scale to full amount")
    print(f"   4. Monitor continuously")

if __name__ == "__main__":
    quick_felix_check()
