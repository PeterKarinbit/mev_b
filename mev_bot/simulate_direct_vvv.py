
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Tokens
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
VVV = Web3.to_checksum_address("0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf")

# Pools from user
POOL_A_UNI = Web3.to_checksum_address("0x01784ef301d79e4b2df3a21ad9a536d4cf09a5ce")
POOL_B_AERO = Web3.to_checksum_address("0x583fAa5E649ad044BD166745d59683E4EAe0e2eB")

ABI = [{'inputs':[],'name':'slot0','outputs':[{'name':'sqrtPriceX96','type':'uint160'},{'name':'tick','type':'int24'},{'name':'observationIndex','type':'uint16'},{'name':'observationCardinality','type':'uint16'},{'name':'observationCardinalityNext','type':'uint16'},{'name':'feeProtocol','type':'uint8'},{'name':'unlocked','type':'bool'}],'stateMutability':'view','type':'function'},{'inputs':[],'name':'token0','outputs':[{'name':'','type':'address'}],'type':'function'}]

def get_price(pool_addr):
    c = w3.eth.contract(address=pool_addr, abi=ABI)
    s0 = c.functions.slot0().call()
    t0 = c.functions.token0().call()
    sqrtPriceX96 = s0[0]
    raw_price = (sqrtPriceX96 / 2**96)**2
    
    # price = token1 / token0
    if t0.lower() == VVV.lower():
        # VVV is token0, price is token1 / token0 (WETH per VVV?)
        return raw_price
    else:
        # VVV is token1, price is token1 / token0 (VVV per token0?)
        # WETH should be token0 then
        return 1/raw_price

def simulate_direct(amount_eth):
    print(f"\n--- Simulating {amount_eth} ETH direct pool arb ---")
    try:
        p_a = get_price(POOL_A_UNI)
        p_b = get_price(POOL_B_AERO)
        
        print(f"Price Pool A (VVV/ETH): {p_a:.8f}")
        print(f"Price Pool B (VVV/ETH): {p_b:.8f}")
        
        # Buy on cheaper, sell on expensive
        if p_a < p_b:
            bought = amount_eth / p_a
            sold = bought * p_b
            profit = sold - amount_eth
            print(f"✅ BUY POOL A -> SELL POOL B")
            print(f"   Buy {bought:.2f} VVV | Sell for {sold:.6f} ETH | Profit: {profit:.6f} ETH ($ {profit*2500:.2f})")
        elif p_b < p_a:
            bought = amount_eth / p_b
            sold = bought * p_a
            profit = sold - amount_eth
            print(f"✅ BUY POOL B -> SELL POOL A")
            print(f"   Buy {bought:.2f} VVV | Sell for {sold:.6f} ETH | Profit: {profit:.6f} ETH ($ {profit*2500:.2f})")
        else:
            print("❌ No spread between these pools")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simulate_direct(0.25)
