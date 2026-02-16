
import requests

def get_base_spreads():
    search_url = 'https://api.dexscreener.com/latest/dex/search/?q=base'
    try:
        data = requests.get(search_url, timeout=10).json()
    except:
        return []
    
    opportunities = []
    seen_tokens = set()
    
    for pair in data.get('pairs', []):
        base_token = pair.get('baseToken', {})
        base_addr = base_token.get('address')
        symbol = base_token.get('symbol')
        
        if not base_addr or base_addr in seen_tokens: continue
        seen_tokens.add(base_addr)
        
        # Limit scanning to first 20 trending tokens to save time
        if len(seen_tokens) > 20: break
        
        try:
            t_url = f'https://api.dexscreener.com/latest/dex/tokens/{base_addr}'
            t_data = requests.get(t_url, timeout=5).json()
            t_pairs = [p for p in t_data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 2000]
            
            if len(t_pairs) < 2: continue
            
            prices = [float(p.get('priceUsd', 0)) for p in t_pairs]
            spread = (max(prices) - min(prices)) / min(prices) * 100
            
            if spread > 1.0:
                opportunities.append({
                    'symbol': symbol,
                    'address': base_addr,
                    'spread': spread,
                    'vol': float(pair.get('volume', {}).get('h24', 0))
                })
        except:
            continue
            
    return sorted(opportunities, key=lambda x: x['spread'], reverse=True)

if __name__ == '__main__':
    print("🔍 SCANNING TRENDING BASE TOKENS FOR SPREADS...")
    opps = get_base_spreads()
    for o in opps:
        print(f"💰 {o['symbol']} | Spread: {o['spread']:.2f}% | 24h Vol: ${o['vol']:,.0f}")
