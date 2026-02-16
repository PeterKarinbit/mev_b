
import requests
import time

def scan_volatility():
    print("🔥 SCANNING BASE FOR EXTREME VOLATILITY (Volume > Liquidity) 🔥")
    # Using a broader search to get more pairs
    url = "https://api.dexscreener.com/latest/dex/search?q=base"
    
    try:
        data = requests.get(url, timeout=10).json()
        pairs = data.get('pairs', [])
        
        found = []
        for p in pairs:
            if p.get('chainId') == 'base':
                liq = float(p.get('liquidity', {}).get('usd', 0))
                # Get volume - try different keys if available
                vol_5m = float(p.get('volume', {}).get('m5', 0))
                
                if liq > 2000: # Lowered liquidity floor to catch newer degens
                    heat = vol_5m / liq
                    
                    if heat > 0.1: # Trigger at 10% of liquidity moved in 5 mins
                        found.append({
                            "symbol": p.get('baseToken', {}).get('symbol'),
                            "dex": p.get('dexId'),
                            "liq": liq,
                            "vol5m": vol_5m,
                            "heat": heat,
                            "price_change": p.get('priceChange', {}).get('m5', 0),
                            "addr": p.get('baseToken', {}).get('address')
                        })
        
        found.sort(key=lambda x: x['heat'], reverse=True)
        
        if not found:
            print("⚠️ No high-heat tokens found in this slice. Markets are calm.")
        else:
            print(f"\n{'SYMBOL':8} | {'DEX':10} | {'HEAT':6} | {'5M VOL':10} | {'LIQUIDITY':10} | {'5M CHANGE'}")
            print("-" * 75)
            for f in found[:15]:
                print(f"{f['symbol']:8} | {f['dex']:10} | {f['heat']:.2f}x | ${f['vol5m']:8,.0f} | ${f['liq']:10,.0f} | {f['price_change']}%")
                print(f"   > Address: {f['addr']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_volatility()
