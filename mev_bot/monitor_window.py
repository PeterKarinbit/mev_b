#!/usr/bin/env python3
"""
🔄 CONTINUOUS WINDOW MONITORING
- Real-time FELIX arbitrage tracking
- Alert when spread > 10%
- Auto-execute when profitable
"""

import requests
import time
from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment
try:
    load_dotenv("mev_bot/.env")
except:
    pass

class FELIXWindowMonitor:
    def __init__(self):
        # Connect to Base
        rpc_url = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/dtH8l3xOI69SRiPRUWCDM")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        self.account = os.getenv("BOT_ADDRESS")
        self.min_spread = 10.0  # Alert at 10% spread
        self.execute_threshold = 15.0  # Execute at 15% spread
        
        print(f"🔄 FELIX Window Monitor Started")
        print(f"Account: {self.account}")
        print(f"Min alert spread: {self.min_spread}%")
        print(f"Auto-execute threshold: {self.execute_threshold}%")
    
    def get_current_spread(self):
        """Get current FELIX spread"""
        try:
            # Quick API call
            url = "https://api.dexscreener.com/latest/dex/tokens/0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', {})
                
                if isinstance(pairs, dict):
                    pairs = list(pairs.values())
                
                base_pairs = [p for p in pairs if p.get('chainId') == 'base']
                
                if base_pairs:
                    prices = {}
                    for pair in base_pairs:
                        dex = pair.get('dexId', 'Unknown')
                        price_native = float(pair.get('priceNative', 0))
                        volume = float(pair.get('volume', {}).get('h24', 0))
                        
                        if price_native > 0 and volume > 1000:  # Minimum volume
                            prices[dex] = price_native
                    
                    if len(prices) >= 2:
                        # Find best spread
                        price_list = list(prices.values())
                        min_price = min(price_list)
                        max_price = max(price_list)
                        spread = ((max_price - min_price) / min_price) * 100
                        
                        return {
                            'spread': spread,
                            'min_price': min_price,
                            'max_price': max_price,
                            'prices': prices,
                            'active': True
                        }
            
            return {'spread': 0, 'active': False}
            
        except Exception as e:
            print(f"❌ API error: {e}")
            return {'spread': 0, 'active': False}
    
    def calculate_profit_potential(self, spread):
        """Calculate profit for different amounts"""
        profits = {}
        
        for eth_amount in [0.1, 0.5, 1.0, 5.0]:
            gross_profit = eth_amount * (spread / 100)
            flash_fee = eth_amount * 0.0009
            gas_cost = 0.0001  # ~$0.25 on Base
            slippage = eth_amount * 0.002  # 0.2%
            
            net_profit = gross_profit - flash_fee - gas_cost - slippage
            profit_usd = net_profit * 2500
            
            profits[eth_amount] = {
                'net_profit': net_profit,
                'profit_usd': profit_usd,
                'profitable': net_profit > 0.01
            }
        
        return profits
    
    def check_gas_conditions(self):
        """Check if gas conditions are favorable"""
        gas_price = self.w3.eth.gas_price / 10**9
        balance = self.w3.eth.get_balance(self.account) / 10**18
        
        return {
            'gas_price': gas_price,
            'balance': balance,
            'favorable': gas_price < 0.01 and balance > 0.005
        }
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print(f"\n🔍 Starting continuous monitoring...")
        print(f"Press Ctrl+C to stop")
        print(f"-" * 50)
        
        while True:
            try:
                # Get current spread
                current_data = self.get_current_spread()
                spread = current_data['spread']
                active = current_data['active']
                
                # Get gas conditions
                gas_conditions = self.check_gas_conditions()
                
                # Calculate profits
                profits = self.calculate_profit_potential(spread)
                
                # Display status
                timestamp = time.strftime('%H:%M:%S')
                status = "🟢 ACTIVE" if active else "🔴 INACTIVE"
                
                print(f"\r{timestamp} | Spread: {spread:.2f}% | Status: {status} | Gas: {gas_conditions['gas_price']:.4f} gwei", end="", flush=True)
                
                # Check alerts
                if active and spread >= self.min_spread:
                    print(f"\n\n🚨 ALERT: {spread:.2f}% spread detected!")
                    
                    if spread >= self.execute_threshold and gas_conditions['favorable']:
                        print(f"🎯 EXECUTE TRIGGERED!")
                        print(f"   Spread: {spread:.2f}%")
                        print(f"   Gas: {gas_conditions['gas_price']:.4f} gwei")
                        print(f"   Balance: {gas_conditions['balance']:.6f} ETH")
                        
                        # Show profit potential
                        print(f"\n💰 PROFIT POTENTIAL:")
                        for amount, profit_data in profits.items():
                            if profit_data['profitable']:
                                print(f"   {amount} ETH: ${profit_data['profit_usd']:.2f}")
                        
                        print(f"\n⚡ EXECUTE NOW: python execute_now_lightning.py")
                        
                        # Optional: Auto-execute (commented for safety)
                        # if spread >= 20.0:
                        #     print(f"🤖 AUTO-EXECUTING...")
                        #     # Auto-execution logic here
                        
                    else:
                        print(f"⏳ Waiting for better conditions...")
                        print(f"   Need: >{self.execute_threshold}% spread + favorable gas")
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                print(f"\n\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def show_current_status(self):
        """Show current status once"""
        current_data = self.get_current_spread()
        gas_conditions = self.check_gas_conditions()
        profits = self.calculate_profit_potential(current_data['spread'])
        
        print(f"\n📊 CURRENT STATUS:")
        print(f"   Spread: {current_data['spread']:.2f}%")
        print(f"   Status: {'🟢 ACTIVE' if current_data['active'] else '🔴 INACTIVE'}")
        print(f"   Gas: {gas_conditions['gas_price']:.4f} gwei")
        print(f"   Balance: {gas_conditions['balance']:.6f} ETH")
        print(f"   Favorable: {'✅' if gas_conditions['favorable'] else '❌'}")
        
        if current_data['active'] and current_data['spread'] > 5:
            print(f"\n💰 PROFIT POTENTIAL ({current_data['spread']:.2f}%):")
            for amount, profit_data in profits.items():
                if profit_data['profitable']:
                    print(f"   {amount} ETH: ${profit_data['profit_usd']:.2f}")

if __name__ == "__main__":
    import sys
    
    monitor = FELIXWindowMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        # Show current status once
        monitor.show_current_status()
    else:
        # Start continuous monitoring
        monitor.monitor_loop()
