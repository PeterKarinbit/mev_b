import requests

def triangle_scan():
    # Primary Bridge: WETH / USDC
    # Token 1: USDC
    # Token 2: VIRTUAL, BRETT, or AERO
    tokens = [
        {'name': 'VIRTUAL', 'addr': '0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b'},
        {'name': 'BRETT', 'addr': '0x532f27101965dd1a3c95fef19C0693A8B59E5046'},
        {'name': 'AERO', 'addr': '0x9401813063411C64a1C02154D495638C4C34a210'}
    ]
    USDC = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
    WETH = '0x4200000000000000000000000000000000000006'

    print("--- POTENTIAL TRIANGLES (WETH -> USDC -> Token -> WETH) ---")
    
    # Get Prices
    # 1. WETH -> USDC (Fixed at ~2600 currently)
    # 2. USDC -> Token
    # 3. Token -> WETH
    
    for t in tokens:
        try:
            # USDC -> Token
            res1 = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{t["addr"]}').json()
            pairs = res1.get('pairs', [])
            
            p_usdc = next((p for p in pairs if p.get('quoteToken', {}).get('symbol') == 'USDC' and p.get('chainId') == 'base'), None)
            p_weth = next((p for p in pairs if p.get('quoteToken', {}).get('symbol') == 'WETH' and p.get('chainId') == 'base'), None)
            
            if p_usdc and p_weth:
                # WETH price in USDC
                weth_price = float(p_weth.get('priceUsd')) / float(p_weth.get('priceNative'))
                
                # Loop: 
                # 1 ETH -> USDC (weth_price)
                # USDC -> Token (weth_price / p_usdc_price)
                # Token -> ETH ( (weth_price/p_usdc_price) * p_weth_native_price )
                
                usdc_amount = weth_price
                token_amount = usdc_amount / float(p_usdc.get('priceUsd'))
                final_eth = token_amount * float(p_weth.get('priceNative'))
                
                profit = (final_eth - 1.0) * 100
                print(f"{t['name']} Triangle: {profit:+.4f}%")
                if profit > 0.1:
                    print(f"  🚀 OPPORTUNITY: {t['name']} loop is profitable!")
        except Exception as e:
            # print(f"Error checking {t['name']}: {e}")
            pass

if __name__ == '__main__':
    triangle_scan()
