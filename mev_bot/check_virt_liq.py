import json
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv('/home/peter-karingithi/Pictures/Linkivo/EPS32 configuration/mev_bot/.env')

w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/base/f7ad576d9633a69e5bd0548cc5b3ee550aa73b2cef04945136af53e95629668f'))

VIRTUAL = '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b'
WETH = '0x4200000000000000000000000000000000000006'

# PancakeSwap V3 Factory
PAN_FACTORY = '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865'

factory_abi = [{"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"pool","type":"address"}],"stateMutability":"view","type":"function"}]
pool_abi = [{"inputs":[],"name":"liquidity","outputs":[{"name":"","type":"uint128"}],"stateMutability":"view","type":"function"}]

factory = w3.eth.contract(address=PAN_FACTORY, abi=factory_abi)

def check_liquidity(fee):
    pool_addr = factory.functions.getPool(WETH, VIRTUAL, fee).call()
    if pool_addr == '0x0000000000000000000000000000000000000000':
        print(f"Fee {fee}: No pool found.")
        return
    pool = w3.eth.contract(address=pool_addr, abi=pool_abi)
    liq = pool.functions.liquidity().call()
    print(f"Fee {fee} Pool: {pool_addr} | Liquidity: {liq}")

print("Checking VIRTUAL Liquidity on PancakeSwap...")
check_liquidity(2500)
check_liquidity(100)
check_liquidity(500)
check_liquidity(10000)
