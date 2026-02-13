import json
import time
from web3 import Web3

# Your Alchemy Key
RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Pair Addresses for WETH/USDC (Mainnet)
UNISWAP_V2_PAIR = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
SUSHISWAP_PAIR = "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"

def get_price(pair_address, name):
    try:
        # Standard Uniswap V2 getReserves ABI
        abi_json = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"}]')
        contract = w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=abi_json)
        reserves = contract.functions.getReserves().call()
        
        # Uniswap V2 Pair: token0 is USDC, token1 is WETH
        # USDC has 6 decimals, WETH has 18
        reserve_usdc = reserves[0]
        reserve_eth = reserves[1]
        
        if reserve_eth == 0: return None
        
        price = (reserve_usdc / 10**6) / (reserve_eth / 10**18)
        return price
    except Exception as e:
        print(f"Error fetching price from {name}: {type(e).__name__} - {e}")
        # traceback.print_exc()
        return None

def sniff():
    print(">>> STARTING LIVE MARKET SNIFFER ON ETHEREUM MAINNET <<<")
    print("Watching WETH/USDC Pair...")
    print("-" * 50)
    
    # Run for 5 iterations for this demo
    for i in range(5):
        try:
            uni_price = get_price(UNISWAP_V2_PAIR, "Uniswap")
            sushi_price = get_price(SUSHISWAP_PAIR, "SushiSwap")
            
            if uni_price and sushi_price:
                diff = abs(uni_price - sushi_price)
                percent_diff = (diff / min(uni_price, sushi_price)) * 100
                
                print(f"Snapshot {i+1}:")
                print(f"  Uniswap V2 Price : ${uni_price:.4f}")
                print(f"  SushiSwap Price   : ${sushi_price:.4f}")
                print(f"  Price Gap        : ${diff:.4f} ({percent_diff:.6f}%)")
                
                if percent_diff > 0.05:
                    print("  [!] ARBITRAGE ALERT: POTENTIAL OPPORTUNITY!")
                else:
                    print("  [Status] Market is efficient. High-frequency bots have likely closed any gaps.")
                print("-" * 30)
            
            time.sleep(2)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    sniff()
