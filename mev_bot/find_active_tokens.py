
import requests

def scan_top_tokens():
    # Searching for high liquidity tokens on Base
    tokens = [
        "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4", # TOSHI
        "0x532f27101965dd163c93259842f1cf57a0701886", # DEGEN (newer?) 0x4ed4e86158bb3020350c1203a943fe2de2456f5c is the real one
        "0x532f27101965dd163c93259842f1cf57a0701886", # HIGHER
        "0x532f27101965dd163c93259842f1cf57a0701886",
        "0x4ed4e86158bb3020350c1203a943fe2de2456f5c", # DEGEN
        "0x532f27101965dd163c93259842f1cf57aa0a20"  # MOCO (partial)
    ]
    # Actually let's use the trending tokens if possible or just more common ones
    common = ["TOSHI", "DEGEN", "BRETT", "VIRTUAL", "MORPHO", "BNKR", "VVV", "AERO"]
    
    print(f"{'SYM':10} | {'MAX SPREAD':10} | {'LIQ':12}")
    print('-' * 40)
    
    for sym in common:
        url = f"https://api.dexscreener.com/latest/dex/search/?q={sym}"
        try:
            data = requests.get(url).json()
            pairs = [p for p in data.get('pairs', []) if p.get('chainId') == 'base' and float(p.get('liquidity', {}).get('usd', 0)) > 20000]
            if len(pairs) < 2: continue
            
            # Check WETH spreads
            weth_pools = [p for p in pairs if p.get('quoteToken', {}).get('symbol') == 'WETH']
            if len(weth_pools) >= 2:
                prices = [float(p.get('priceNative', 0)) for p in weth_pools]
                spread = (max(prices) - min(prices)) / min(prices) * 100
                liq = sum(float(p.get('liquidity', {}).get('usd', 0)) for p in weth_pools)
                print(f"{sym:10} | {spread:9.2f}% | ${int(liq):,d}")
        except:
            pass

if __name__ == "__main__":
    scan_top_tokens()
