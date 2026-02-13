import json
import time
from web3 import Web3

# --- CONFIGURATION ---
# Alchemy Base RPC (Use the same key as Mainnet)
# Fallback to public RPC if Alchemy isn't enabled for Base yet
try:
    ALCHEMY_URL = "https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    if not w3.is_connected():
        raise Exception("Alchemy Base not connected")
except:
    PUBLIC_URL = "https://mainnet.base.org"
    w3 = Web3(Web3.HTTPProvider(PUBLIC_URL))

# Token Addresses on Base
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")

# DEX Pool Addresses
# 1. Uniswap V3 (WETH/USDC 0.05% fee)
UNI_V3_POOL = Web3.to_checksum_address("0xd0b53d9277642d899df5c87a3966a349a798f224")

# 2. Aerodrome Factory to find the Volatile Pool
AERO_FACTORY = Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da")

# ABIs
# UniV3 slot0 ABI (to get sqrtPriceX96)
V3_POOL_ABI = json.loads('[{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]')

# Aerodrome Factory ABI
AERO_FACTORY_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"bool","name":"stable","type":"bool"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')

# Aerodrome / UniV2 getReserves ABI
V2_POOL_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"}]')

def get_uni_v3_price():
    try:
        # On Base USDC/WETH pool: 
        # WETH (0x4200...) is token0 (18 decimals)
        # USDC (0x8335...) is token1 (6 decimals)
        contract = w3.eth.contract(address=UNI_V3_POOL, abi=V3_POOL_ABI)
        slot0 = contract.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        
        # P = (sqrtPriceX96 / 2**96)**2
        # Price in token1 per token0 (base units)
        # Price_base = USDC_base / WETH_base
        price_base = (sqrtPriceX96 / (2**96)) ** 2
        
        # Price_human = (USDC / 10**6) / (WETH / 10**18)
        # Price_human = (USDC/WETH) * (10**18 / 10**6)
        # Price_human = price_base * 10**12
        price_in_usd = price_base * 10**12
        return price_in_usd
    except Exception as e:
        print(f"UniV3 Error: {e}")
        return None

def get_aero_price():
    try:
        factory = w3.eth.contract(address=AERO_FACTORY, abi=AERO_FACTORY_ABI)
        # Aerodrome WETH/USDC is a Volatile (False) pool
        pool_address = factory.functions.getPool(USDC, WETH, False).call()
        
        pool = w3.eth.contract(address=pool_address, abi=V2_POOL_ABI)
        reserves = pool.functions.getReserves().call()
        
        # Aerodrome sorts tokens: WETH (0x4200) < USDC (0x8335)
        # So reserve0 = WETH, reserve1 = USDC
        resWETH, resUSDC = reserves[0], reserves[1]
            
        # Price = USDC / WETH
        price = (resUSDC / 10**6) / (resWETH / 10**18)
        return price
    except Exception as e:
        print(f"Aerodrome Error: {e}")
        return None

def sniff():
    if not w3.is_connected():
        print("Failed to connect to Base network. Check RPC URL.")
        return

    print(">>> BASE NETWORK ARBITRAGE SNIFFER <<<")
    print("Monitoring: USDC / WETH")
    print("DEXs: Aerodrome vs Uniswap V3")
    print("-" * 50)

    for i in range(5):
        aero = get_aero_price()
        uni = get_uni_v3_price()

        if aero and uni:
            diff = abs(aero - uni)
            p_diff = (diff / min(aero, uni)) * 100
            
            print(f"Time: {time.strftime('%H:%M:%S')}")
            print(f"  Aerodrome Price : ${aero:.2f}")
            print(f"  UniV3 Price     : ${uni:.2f}")
            print(f"  GAP             : {p_diff:.4f}% (${diff:.4f})")
            
            if p_diff > 0.1:
                print("  [!!!] PROFIT OPPORTUNITY DETECTED!")
            else:
                print("  [Status] Market stable on Base.")
        
        print("-" * 30)
        time.sleep(5)

if __name__ == "__main__":
    sniff()
