#!/usr/bin/env python3
import requests
import json
import re

def scrape_base_gainers():
    """Scrape Base gainers from DexScreener web page"""
    url = "https://dexscreener.com/gainers/base?rankBy=priceChangeH24&order=desc&minLiq=250000&min24HTxns=300&min24HSells=30&min24HVol=250000&profile=1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print("🔍 Analyzing DexScreener gainers page...")
        
        # Look for token data in the HTML
        content = response.text
        
        # Try to find JSON data embedded in the page
        json_pattern = r'window\.__NEXT_DATA__\s*=\s*({.+?});'
        match = re.search(json_pattern, content)
        
        if match:
            try:
                next_data = json.loads(match.group(1))
                print("✅ Found embedded data")
                return extract_token_data(next_data)
            except:
                pass
        
        # Alternative: Look for token addresses and symbols
        token_pattern = r'0x[a-fA-F0-9]{40}'
        tokens = re.findall(token_pattern, content)
        
        print(f"📊 Found {len(tokens)} token addresses in page")
        
        # Get details for unique tokens
        unique_tokens = list(set(tokens))[:20]  # Top 20 unique tokens
        
        return get_token_details(unique_tokens)
        
    except Exception as e:
        print(f"❌ Error scraping: {e}")
        return None

def extract_token_data(next_data):
    """Extract token data from Next.js page data"""
    tokens = []
    
    try:
        # Navigate through the Next.js data structure
        page_props = next_data.get('props', {}).get('pageProps', {})
        
        # Look for token data in various possible locations
        if 'pairs' in page_props:
            tokens = page_props['pairs']
        elif 'data' in page_props:
            tokens = page_props['data']
        else:
            print("❌ Could not find token data in page structure")
            return []
            
        return tokens[:20]  # Return top 20
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return []

def get_token_details(token_addresses):
    """Get details for specific tokens via API"""
    weth_address = "0x4200000000000000000000000000000000000006"
    detailed_tokens = []
    
    for addr in token_addresses[:10]:  # Limit to 10 to avoid rate limits
        try:
            # Search for this specific token
            search_url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
            response = requests.get(search_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data:
                    for pair in data['pairs']:
                        if pair.get('chainId') == 'base':
                            # Check if it's a WETH pair
                            base_addr = pair.get('baseToken', {}).get('address', '').lower()
                            quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
                            
                            if (base_addr == weth_address.lower() or quote_addr == weth_address.lower()):
                                detailed_tokens.append(pair)
                                break
                                
        except Exception as e:
            print(f"❌ Error getting details for {addr}: {e}")
            continue
    
    return detailed_tokens

def analyze_gainers(tokens):
    """Analyze gainers for arbitrage opportunities"""
    if not tokens:
        print("❌ No tokens to analyze")
        return []
    
    print("🔥 BASE TOP GAINERS ANALYSIS")
    print("="*80)
    print("Filters: Min $250K liquidity, 300+ txns, 30+ sells, $250K+ volume")
    print("="*80)
    
    # Sort by price change
    tokens.sort(key=lambda x: x.get('priceChange', {}).get('h24', 0), reverse=True)
    
    top_targets = []
    
    for i, pair in enumerate(tokens[:10]):  # Top 10
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        volume_24h = pair.get('volume', {}).get('h24', 0)
        txns_24h = pair.get('txns', {}).get('h24', {}).get('buys', 0) + pair.get('txns', {}).get('h24', {}).get('sells', 0)
        sells_24h = pair.get('txns', {}).get('h24', {}).get('sells', 0)
        price_change = pair.get('priceChange', {}).get('h24', 0)
        
        base_token = pair.get('baseToken', {})
        quote_token = pair.get('quoteToken', {})
        
        # Determine which is WETH and which is the target token
        weth_address = "0x4200000000000000000000000000000000000006"
        if base_token.get('address', '').lower() == weth_address.lower():
            target_token = quote_token
        else:
            target_token = base_token
        
        print(f"\n{i+1}. 🚀 {target_token.get('symbol', 'UNKNOWN')} (+{price_change:.2f}%)")
        print(f"    Address: {target_token.get('address', 'N/A')}")
        print(f"    DEX: {pair.get('dexId', 'N/A')}")
        print(f"    Liquidity: ${liquidity:,.0f}")
        print(f"    Volume 24h: ${volume_24h:,.0f}")
        print(f"    Txns 24h: {txns_24h} (Sells: {sells_24h})")
        
        # Check if it meets the filter criteria
        if (liquidity >= 250000 and  # Min $250K liquidity
            volume_24h >= 250000 and  # Min $250K volume
            txns_24h >= 300 and      # Min 300 txns
            sells_24h >= 30):        # Min 30 sells
            
            top_targets.append({
                'symbol': target_token.get('symbol', 'UNKNOWN'),
                'address': target_token.get('address', ''),
                'liquidity': liquidity,
                'volume': volume_24h,
                'txns': txns_24h,
                'sells': sells_24h,
                'price_change': price_change,
                'dex': pair.get('dexId', '')
            })
            print("    ✅ MEETS ALL CRITERIA - PERFECT TARGET")
        else:
            print("    ⚠️  Doesn't meet all filters")
    
    print(f"\n🎯 TOKENS MEETING ALL FILTERS ({len(top_targets)}):")
    print("="*80)
    
    for token in top_targets:
        print(f"• {token['symbol']:<8} | Change: {token['price_change']:>6.2f}% | "
              f"Liq: ${token['liquidity']:>8,.0f} | Vol: ${token['volume']:>8,.0f} | "
              f"Txns: {token['txns']:>4.0f} | Sells: {token['sells']:>3.0f}")
        print(f"  Address: {token['address']}")
    
    # Generate Rust config
    if top_targets:
        print(f"\n🦍 OPTIMIZED RUST CONFIGURATION:")
        print("="*80)
        print("// Replace your current tokens array with these:")
        print("let tokens = vec![")
        
        for token in top_targets:
            print(f'    TokenInfo {{ name: "{token["symbol"]}".to_string(), addr: "{token["address"]}".parse()?, decimals: 18 }},')
        
        print("];")
        
        print(f"\n💡 THESE ARE YOUR ARBITRAGE GEMS!")
        print("="*80)
        print("• High volatility + high liquidity = frequent arbitrage opportunities")
        print("• Strong selling pressure creates price gaps between DEXs")
        print("• These tokens are trending - perfect for MEV extraction!")
    
    return top_targets

if __name__ == "__main__":
    print("🔥 Scraping Base gainers with your specific filters...")
    tokens = scrape_base_gainers()
    
    if tokens:
        analyze_gainers(tokens)
    else:
        print("❌ Failed to get gainers data")
        print("💡 Try manually checking: https://dexscreener.com/gainers/base")
