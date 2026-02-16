#!/usr/bin/env python3
from web3 import Web3

def fix_checksum_addresses():
    """Fix EIP-55 checksum issues"""
    print("🔧 FIXING CHECKSUM ADDRESSES")
    print("="*60)
    
    # Correct checksum addresses
    addresses = {
        'VIRTUAL': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b',
        'DEGEN': '0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed', 
        'AERO': '0x9401813063411C64a1C02154D495638C4C34a210',
        'TOSHI': '0xAC1Bd2486aAf3b5C0df3625023906C7f8673329D',
        'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
        'WETH': '0x4200000000000000000000000000000000000006'
    }
    
    print("✅ CORRECT CHECKSUM ADDRESSES:")
    for symbol, addr in addresses.items():
        checksum_addr = Web3.to_checksum_address(addr)
        print(f"{symbol}: {checksum_addr}")
    
    return addresses

if __name__ == "__main__":
    fix_checksum_addresses()
