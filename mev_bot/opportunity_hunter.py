
import requests

def get_base_high_potential():
    # Fetch trending/active pools on Base
    url = 'https://api.dexscreener.com/latest/dex/search/?q=base'
    try:
        data = requests.get(url, timeout=10).json()
    except:
        return []
    
    potential = []
    seen = set()
    
    # DexScreener search results are often sorted by volume/relevance
    for pair in data.get('pairs', []):
        base_token = pair.get('baseToken', {})
        addr = base_token.get('address')
        symbol = base_token.get('symbol')
        
        if not addr or addr in seen: continue
        seen.add(addr)
        
        if len(seen) > 30: break # Scan top 30
        
        try:
            t_url = f'https://api.dexscreener.com/latest/dex/tokens/{addr}'
            t_data = requests.get(t_url, timeout=5).json()
            t_pairs = [p for p in t_data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 5000]
            
            if len(t_pairs) < 2: continue
            
            # Check price spread
            prices = [float(p.get('priceUsd', 0)) for p in t_pairs]
            min_p = min(prices)
            max_p = max(prices)
            spread = (max_p - min_p) / min_p * 100
            
            # Find the DEXes
            buy_dex = [p.get('dexId') for p in t_pairs if float(p.get('priceUsd')) == min_p][0]
            sell_dex = [p.get('dexId') for p in t_pairs if float(p.get('priceUsd')) == max_p][0]
            
            if spread > 1.0: # Only care about > 1%
                potential.append({
                    'symbol': symbol,
                    'address': addr,
                    'spread': spread,
                    'buy_dex': buy_dex,
                    'sell_dex': sell_dex,
                    'vol': float(pair.get('volume', {}).get('h24', 0)),
                    'liq': float(pair.get('liquidity', {}).get('usd', 0))
                })
        except:
            continue
            
    return sorted(potential, key=lambda x: x['spread'], reverse=True)

if __name__ == '__main__':
    print("🚀 BASE ARBITRAGE SCANNER (LIQUIDITY > $5,000)")
    results = get_base_high_potential()
    if not results:
        print("No opportunities found with decent liquidity.")
    for r in results:
        print(f"\n💎 {r['symbol']} ({r['address'][:10]}...)")
        print(f"   Spread: {r['spread']:.2f}% | Liq: ${r['liq']:,.0f} | Vol: ${r['vol']:,.0f}")
        print(f"   Action: Buy on {r['buy_dex']} | Sell on {r['sell_dex']}")
