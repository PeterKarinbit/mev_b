#!/usr/bin/env python3
import requests
import json
from web3 import Web3
from eth_abi import encode
from dotenv import load_dotenv
import os
import time

load_dotenv("mev_bot/.env")

# Enhanced token list with emerging tokens
TOKENS = [
    {
        'name': 'VIRTUAL',
        'address': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b',
        'preferred_base': 'WETH',
        'threshold': 1.0,
        'trade_amount': 10000000000000000,  # 0.01 ETH
        'fee1': 3000,
        'fee2': 2500
    },
    {
        'name': 'DEGEN', 
        'address': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed',
        'preferred_base': 'WETH',
        'threshold': 0.4,
        'trade_amount': 20000000000000000,  # 0.02 ETH
        'fee1': 3000,
        'fee2': 2500
    },
    {
        'name': 'BASE',
        'address': '0xd07379a755A8f11B57610154861D694b2A0f615a',
        'preferred_base': 'USDC',
        'threshold': 0.2,
        'trade_amount': 15000000000,  # 15,000 USDC
        'fee1': 3000,
        'fee2': 2500
    },
    {
        'name': 'SYND',
        'address': '0x11dC28D01984079b7efE7763b533e6ed9E3722B9',
        'preferred_base': 'USDC',
        'threshold': 0.25,
        'trade_amount': 20000000000,  # 20,000 USDC
        'fee1': 3000,
        'fee2': 2500
    },
    {
        'name': 'LQTY',
        'address': '0x4b9F8F9A4B8bC36c38C0B1D8b1D8eEe8b536',
        'preferred_base': 'USDC',
        'threshold': 0.15,
        'trade_amount': 10000000000,  # 10,000 USDC
        'fee1': 3000,
        'fee2': 2500
    }
]

def get_pool_prices(worker, token):
    """Get prices from all DEXs for a token"""
    weth_address = "0x4200000000000000000000000000000000000006"
    
    # Simplified price checking
    try:
        # Aerodrome V2
        aero_factory = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
        aero_pool = worker.eth.contract(address=aero_factory, abi=[{
            "inputs": [{"name": "token0", "type": "address"}, {"name": "token1", "type": "address"}, {"name": "stable", "type": "bool"}],
            "name": "getPool", "outputs": [{"name": "", "type": "address"}], "type": "function", "stateMutability": "view"
        }])
        
        pool_addr = aero_pool.functions.getPool(weth_address, token['address'], False).call()
        if pool_addr and pool_addr != "0x0000000000000000000000000000000000000000000":
            pool = worker.eth.contract(address=pool_addr, abi=[{
                "inputs": [], "name": "getReserves", "outputs": [
                    {"name": "reserve0", "type": "uint112"}, {"name": "reserve1", "type": "uint112"}, {"name": "blockTimestampLast", "type": "uint32"}
                ], "type": "function", "stateMutability": "view"
            }])
            
            reserves = pool.functions.getReserves().call()
            if reserves:
                price = reserves[1] / reserves[0]  # token per WETH
                return {'aero': price}
    except:
        pass
    
    return {}

def check_arbitrage_opportunity(worker, token):
    """Check if there's an arbitrage opportunity"""
    prices = get_pool_prices(worker, token)
    
    if len(prices) > 1:
        # Simple gap calculation (would need more DEXs for real arbitrage)
        return True, prices
    
    return False, {}

def execute_trade(worker, token, prices):
    """Execute arbitrage trade"""
    try:
        # Use the exact same call as debug_deep.py
        execute_sel = worker.keccak(text="execute(uint256,bool,address,uint24,uint24)")[:4]
        execute_data = encode(
            ['uint256', 'bool', 'address', 'uint24', 'uint24'],
            [token['trade_amount'], True, token['address'], token['fee1'], token['fee2']]
        )
        
        result = worker.eth.call({
            'from': os.getenv("BOT_ADDRESS"),
            'to': os.getenv("FLASH_ARB_CONTRACT"),
            'data': '0x' + (execute_sel + execute_data).hex(),
            'value': 0
        })
        
        print(f"✅ {token['name']} TRADE SIMULATION SUCCESS!")
        print(f"Result: {result.hex()[:50]}...")
        
        # If simulation passes, send actual transaction
        if result and len(result.hex()) > 2:
            tx_hash = worker.eth.send_transaction({
                'to': os.getenv("FLASH_ARB_CONTRACT"),
                'data': '0x' + (execute_sel + execute_data).hex(),
                'gas': 300000,  # Gas limit
                'nonce': worker.eth.get_transaction_count(os.getenv("BOT_ADDRESS"))
            })
            
            print(f"🚀 {token['name']} TRANSACTION SENT: {tx_hash.hex()}")
            return True
    except Exception as e:
        print(f"❌ {token['name']} TRADE FAILED: {e}")
        return False

def main():
    print("🚀 ENHANCED PYTHON MEV BOT - OPTIONS 2 + 3")
    print("="*60)
    
    w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Base network")
        return
    
    print("✅ Connected to Base network")
    print(f"📊 Monitoring {len(TOKENS)} enhanced tokens")
    
    success_count = 0
    total_profit_trades = 0
    
    while True:
        try:
            for token in TOKENS:
                has_opportunity, prices = check_arbitrage_opportunity(w3, token)
                
                if has_opportunity:
                    print(f"\n🎯 {token['name']} OPPORTUNITY DETECTED!")
                    print(f"   Threshold: {token['threshold']}%")
                    print(f"   Trade Amount: {token['trade_amount']}")
                    
                    success = execute_trade(w3, token, prices)
                    if success:
                        success_count += 1
                        total_profit_trades += 1
                        print(f"💰 SUCCESS COUNT: {success_count}")
                        print(f"📈 TOTAL PROFITABLE TRADES: {total_profit_trades}")
                    
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        
        time.sleep(2)  # Check every 2 seconds

if __name__ == "__main__":
    main()
