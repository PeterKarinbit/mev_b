import requests

def check():
    for sym in ['BRETT', 'KEYCAT', 'VIRTUAL', 'AERO']:
        url = f'https://api.dexscreener.com/latest/dex/search?q={sym}'
        try:
            res = requests.get(url).json()
            pairs = [p for p in res.get('pairs', []) if p.get('chainId') == 'base']
            print(f'\n--- {sym} ---')
            for p in pairs:
                dex = p.get('dexId')
                price = p.get('priceUsd')
                liq = p.get('liquidity', {}).get('usd', 0)
                if liq > 10000:
                    print(f'  {dex:12} | Price: ${float(price):.8f} | Liq: ${liq:,.0f}')
        except:
            pass

if __name__ == '__main__':
    check()
