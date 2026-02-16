import requests
from collections import defaultdict

def scan():
    # Looking for top volume tokens on Base
    url = 'https://api.dexscreener.com/latest/dex/search?q=base'
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        data = response.json()
        pairs = data.get('pairs', [])
        
        # Sort pairs by 24h volume
        pairs.sort(key=lambda x: x.get('volume', {}).get('h24', 0), reverse=True)
        
        tokens = defaultdict(list)
        for p in pairs:
            if p.get('chainId') != 'base': continue
            addr = p.get('baseToken', {}).get('address')
            tokens[addr].append(p)
            
        print('--- HIGH-VOLUME MULTI-DEX TARGETS (BASE) ---')
        targets = []
        for addr, p_list in tokens.items():
            dexes = {p.get('dexId') for p in p_list}
            if len(dexes) > 1:
                name = p_list[0].get('baseToken', {}).get('name')
                symbol = p_list[0].get('baseToken', {}).get('symbol')
                max_liq = max(p.get('liquidity', {}).get('usd', 0) for p in p_list)
                
                if max_liq > 20000:
                    prices = {}
                    for p in p_list:
                        prices[p.get('dexId')] = float(p.get('priceUsd', 0))
                    
                    d_list = list(prices.keys())
                    max_gap = 0
                    best_pair = ""
                    for i in range(len(d_list)):
                        for j in range(i+1, len(d_list)):
                            p1, p2 = prices[d_list[i]], prices[d_list[j]]
                            if p1 > 0 and p2 > 0:
                                gap = abs(p1 - p2) / min(p1, p2) * 100
                                if gap > max_gap:
                                    max_gap = gap
                                    best_pair = f"{d_list[i]} vs {d_list[j]}"

                    targets.append({
                        'symbol': symbol,
                        'gap': max_gap,
                        'pair': best_pair,
                        'liq': max_liq,
                        'addr': addr
                    })

        targets.sort(key=lambda x: x['gap'], reverse=True)
        for t in targets[:15]:
            print(f"{t['symbol']} | Gap: {t['gap']:.2f}% | {t['pair']} | Liq: ${t['liq']:,.0f} | {t['addr']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    scan()
