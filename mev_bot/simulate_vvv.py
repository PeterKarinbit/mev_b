
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Tokens
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
VVV = Web3.to_checksum_address("0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf")
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

# Protocols
UNI_QUOTER = Web3.to_checksum_address("0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a")
AERO_ROUTER = Web3.to_checksum_address("0xcF77a3Ba9A5CA399B7C97c7a1C7f6F1a4f79D2f8")
AERO_FACTORY = Web3.to_checksum_address("0x420DD381b31aEf6683db6B902084cB0FFECe40Da")

# ABIs
QUOTER_ABI = [{"inputs": [{"components": [{"name": "tokenIn", "type": "address"}, {"name": "tokenOut", "type": "address"}, {"name": "amountIn", "type": "uint256"}, {"name": "fee", "type": "uint24"}, {"name": "sqrtPriceLimitX96", "type": "uint160"}], "name": "params", "type": "tuple"}], "name": "quoteExactInputSingle", "outputs": [{"name": "amountOut", "type": "uint256"}, {"name": "sqrtPriceX96After", "type": "uint160"}, {"name": "initializedTicksCrossed", "type": "uint32"}, {"name": "gasEstimate", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}]
AERO_ROUTER_ABI = [{"inputs": [{"name": "amountIn", "type": "uint256"}, {"components": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "stable", "type": "bool"}, {"name": "factory", "type": "address"}], "name": "routes", "type": "tuple[]"}], "name": "getAmountsOut", "outputs": [{"name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}]

quoter = w3.eth.contract(address=UNI_QUOTER, abi=QUOTER_ABI)
aero_router = w3.eth.contract(address=AERO_ROUTER, abi=AERO_ROUTER_ABI)

def simulate(amount_eth):
    amount_in = int(amount_eth * 10**18)
    print(f"\n--- Simulating {amount_eth} ETH ---")
    
    # Uni V3 Buy (Check 0.3% and 1% fees)
    for fee in [3000, 10000]:
        try:
            res = quoter.functions.quoteExactInputSingle({
                'tokenIn': WETH,
                'tokenOut': VVV,
                'amountIn': amount_in,
                'fee': fee,
                'sqrtPriceLimitX96': 0
            }).call()
            uni_out = res[0]
            print(f"Uni V3 Buy ({fee/10000}%):   {uni_out/1e18:,.2f} VVV")
            
            # Check Sell on Aero
            try:
                # WETH -> FELIX/VVV might be multi-hop?
                # Let's try WETH -> USDC -> VVV since you found a USDC pool
                route = [
                    {'from': VVV, 'to': USDC, 'stable': False, 'factory': AERO_FACTORY},
                    {'from': USDC, 'to': WETH, 'stable': False, 'factory': AERO_FACTORY}
                ]
                res_weth = aero_router.functions.getAmountsOut(uni_out, route).call()
                final_weth = res_weth[-1]
                profit = (final_weth - amount_in) / 1e18
                print(f"   -> Aero Sell (2-hop): {final_weth/1e18:.6f} WETH | Profit: {profit:.6f} ETH ($ {profit*2500:.2f})")
            except: pass
        except Exception as e:
            pass

    # Aerodrome Buy
    try:
        # Try 1-hop first
        route = [{'from': WETH, 'to': VVV, 'stable': False, 'factory': AERO_FACTORY}]
        aero_out = aero_router.functions.getAmountsOut(amount_in, route).call()[-1]
        print(f"Aero Buy (1-hop):   {aero_out/1e18:,.2f} VVV")
    except: 
        try:
            # Try 2-hop WETH -> USDC -> VVV
            route = [
                {'from': WETH, 'to': USDC, 'stable': False, 'factory': AERO_FACTORY},
                {'from': USDC, 'to': VVV, 'stable': False, 'factory': AERO_FACTORY}
            ]
            aero_out = aero_router.functions.getAmountsOut(amount_in, route).call()[-1]
            print(f"Aero Buy (2-hop):   {aero_out/1e18:,.2f} VVV")
        except:
            print("Aero Buy: No path found")

if __name__ == "__main__":
    print("🚀 VVV ARBITRAGE SIMULATION")
    for a in [0.25]:
        simulate(a)
