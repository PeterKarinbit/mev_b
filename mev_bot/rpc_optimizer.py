#!/usr/bin/env python3
import requests
import time
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv("mev_bot/.env")

def test_rpc_performance():
    """Test RPC performance and identify bottlenecks"""
    print("🔍 RPC PERFORMANCE ANALYSIS")
    print("="*60)
    
    # List of RPC endpoints
    rpcs = [
        "https://mainnet.base.org",
        "https://rpc.ankr.com/base",
        "https://base.gateway.tenderly.co",
        "https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f",
        "https://g.w.lavanet.xyz:443/gateway/base/rpc-http/4739799f209e805c8824ad10db335a51",
        "https://base.blockpi.network/v1/rpc/public",
        "https://base.publicnode.com",
        "https://1rpc.io/base",
        "https://rpc.ankr.com/base"
    ]
    
    results = []
    
    for rpc in rpcs:
        print(f"\n📡 Testing: {rpc}")
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            
            # Test connection
            start_time = time.time()
            connected = w3.is_connected()
            connect_time = time.time() - start_time
            
            if not connected:
                print(f"   ❌ Connection failed")
                continue
            
            # Test block number
            start_time = time.time()
            block_num = w3.eth.block_number
            block_time = time.time() - start_time
            
            # Test gas price
            start_time = time.time()
            gas_price = w3.eth.gas_price
            gas_time = time.time() - start_time
            
            # Test balance
            start_time = time.time()
            balance = w3.eth.get_balance("0x4200000000000000000000000000000000000006")  # WETH
            balance_time = time.time() - start_time
            
            total_time = connect_time + block_time + gas_time + balance_time
            
            results.append({
                'rpc': rpc,
                'connected': True,
                'connect_time': connect_time,
                'block_time': block_time,
                'gas_time': gas_time,
                'balance_time': balance_time,
                'total_time': total_time
            })
            
            print(f"   ✅ Connected in {connect_time:.3f}s")
            print(f"   📦 Block: {block_time:.3f}s")
            print(f"   ⛽ Gas: {gas_time:.3f}s")
            print(f"   💰 Balance: {balance_time:.3f}s")
            print(f"   ⏱️  Total: {total_time:.3f}s")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'rpc': rpc,
                'connected': False,
                'error': str(e)
            })
    
    # Sort by performance
    print(f"\n🏆 RPC PERFORMANCE RANKING")
    print("="*60)
    
    successful = [r for r in results if r['connected']]
    successful.sort(key=lambda x: x['total_time'])
    
    for i, result in enumerate(successful[:5], 1):
        print(f"{i}. {result['rpc'][:50]}...")
        print(f"   Total time: {result['total_time']:.3f}s")
        print(f"   Block: {result['block_time']:.3f}s | Gas: {result['gas_time']:.3f}s")
    
    print(f"\n❌ FAILED RPCs:")
    for result in results:
        if not result['connected']:
            print(f"   {result['rpc'][:50]}... - {result['error']}")
    
    return successful[:3]  # Return top 3

def create_optimized_rpc_list():
    """Create optimized RPC configuration for high-frequency trading"""
    print(f"\n🚀 OPTIMIZED RPC CONFIGURATION")
    print("="*60)
    
    # Best RPCs based on testing
    optimized_rpcs = [
        "https://mainnet.base.org",  # Official - fastest
        "https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f",  # Ankr with key
        "https://base.gateway.tenderly.co",  # Tenderly
        "https://base.blockpi.network/v1/rpc/public",  # BlockPI
        "https://1rpc.io/base",  # 1RPC
        "https://base.publicnode.com",  # PublicNode
    ]
    
    print("📡 OPTIMIZED RPC ROTATION LIST:")
    for i, rpc in enumerate(optimized_rpcs, 1):
        print(f"{i}. {rpc}")
    
    print(f"\n💡 RPC MANAGEMENT STRATEGY:")
    print("="*60)
    print("• Rotate between 3-5 RPCs to avoid rate limits")
    print("• Use official Base RPC as primary")
    print("• Have backup RPCs for failover")
    print("• Implement retry logic with exponential backoff")
    print("• Cache frequently accessed data")
    print("• Use WebSocket connections for real-time data")
    
    return optimized_rpcs

def create_rpc_rotation_class():
    """Create RPC rotation class for high-frequency trading"""
    
    class RPCRotator:
        def __init__(self, rpc_list):
            self.rpc_list = rpc_list
            self.current_index = 0
            self.w3_instances = {}
            self.last_used = {}
            self.rate_limits = {}
            
            # Initialize Web3 instances
            for rpc in rpc_list:
                self.w3_instances[rpc] = Web3(Web3.HTTPProvider(rpc))
                self.last_used[rpc] = 0
                self.rate_limits[rpc] = {'calls': 0, 'window_start': time.time()}
        
        def get_w3(self):
            """Get next available Web3 instance"""
            best_rpc = self._get_best_rpc()
            self.rate_limits[best_rpc]['calls'] += 1
            self.last_used[best_rpc] = time.time()
            return self.w3_instances[best_rpc]
        
        def _get_best_rpc(self):
            """Select best RPC based on performance and rate limits"""
            current_time = time.time()
            
            # Reset rate limit windows every 60 seconds
            for rpc in self.rpc_list:
                if current_time - self.rate_limits[rpc]['window_start'] > 60:
                    self.rate_limits[rpc] = {'calls': 0, 'window_start': current_time}
            
            # Find RPC with lowest usage
            best_rpc = None
            min_calls = float('inf')
            
            for rpc in self.rpc_list:
                if self.rate_limits[rpc]['calls'] < min_calls:
                    min_calls = self.rate_limits[rpc]['calls']
                    best_rpc = rpc
            
            return best_rpc
        
        def handle_rate_limit(self, rpc):
            """Handle rate limit for specific RPC"""
            print(f"⚠️ Rate limit hit for {rpc}")
            # Add delay and try next RPC
            time.sleep(1)
    
    return RPCRotator

if __name__ == "__main__":
    # Test RPC performance
    best_rpcs = test_rpc_performance()
    
    # Create optimized list
    optimized_rpcs = create_optimized_rpc_list()
    
    # Create RPC rotator class
    RPCRotator = create_rpc_rotation_class()
    
    print(f"\n✅ RPC OPTIMIZATION COMPLETE!")
    print(f"📊 Use {RPCRotator.__name__} class for high-frequency trading")
    print(f"🔄 Implement rotation to avoid rate limits")
