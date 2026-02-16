import requests
from collections import defaultdict

def scan():
    url = 'https://api.dexscreener.com/latest/dex/search?q=WETH%20base'
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        data = response.json()
        pairs = data.get('pairs', [])
        
        tokens = defaultdict(list)
        for p in pairs:
            if p.get('chainId') != 'base': continue
            # Look for WETH or USDC pairs
            quote = p.get('quoteToken', {}).get('symbol')
            if quote not in ['WETH', 'USDC']: continue
            
            addr = p.get('baseToken', {}).get('address')
            tokens[addr].append(p)
            
        print('--- REAL-TIME MULTI-DEX TARGETS (BASE) ---')
        found = 0
        for addr, p_list in tokens.items():
            dexes = {p.get('dexId') for p in p_list}
            # We need at least two different DEXs for arbitrage
            if len(dexes) > 1:
                name = p_list[0].get('baseToken', {}).get('name')
                symbol = p_list[0].get('baseToken', {}).get('symbol')
                
                # Check liquidity
                max_liq = max(p.get('liquidity', {}).get('usd', 0) for p in p_list)
                if max_liq > 100000:
                    found += 1
                    print(f'\n{symbol} ({name})')
                    print(f'  Address: {addr}')
                    print(f'  Exchanges: {", ".join(dexes)}')
                    
                    # Prices
                    prices = {}
                    for p in p_list:
                        prices[p.get('dexId')] = float(p.get('priceUsd', 0))
                    
                    # Calculate gaps
                    d_list = list(prices.keys())
                    for i in range(len(d_list)):
                        for j in range(i+1, len(d_list)):
                            d1, d2 = d_list[i], d_list[j]
                            p1, p2 = prices[d1], prices[d2]
                            if p1 > 0 and p2 > 0:
                                gap = abs(p1 - p2) / min(p1, p2) * 100
                                print(f'  GAP [{d1} vs {d2}]: {gap:.2f}%')
        
        if found == 0:
            print("No high-liquidity multi-DEX targets found in this search.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    scan()
