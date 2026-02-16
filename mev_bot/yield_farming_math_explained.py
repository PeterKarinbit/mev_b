#!/usr/bin/env python3
"""
Yield Farming Math Explained
- Detailed calculation of flash loan yield farming profits
- How to verify legitimate yields vs temporary incentives
"""

def calculate_yield_farming_profit():
    """
    MATH BREAKDOWN:
    
    Profit = (Yield Earned) - (Flash Loan Fee) - (Gas Cost)
    
    Where:
    - Yield Earned = Principal × APY × (Time / 365 days)
    - Flash Loan Fee = Principal × 0.0009 (0.09%)
    - Gas Cost = Gas Price × Gas Used × ETH Price
    """
    
    print("="*80)
    print("💰 YIELD FARMING PROFIT MATH EXPLAINED")
    print("="*80)
    
    # Example: $100,000 USDC flash loan
    principal_usdc = 100000
    principal_wei = principal_usdc * 10**6  # USDC has 6 decimals
    
    # Scenario 1: Legitimate yield (5% APY difference)
    print("\n📊 SCENARIO 1: Legitimate Yield (5% APY difference)")
    print("-" * 80)
    
    apy_difference = 5.0  # 5% APY difference
    duration_days = 7     # 1 week
    
    # Step 1: Calculate yield earned
    # Formula: Principal × (APY / 100) × (Days / 365)
    annual_yield = principal_usdc * (apy_difference / 100)
    yield_earned = annual_yield * (duration_days / 365)
    
    print(f"1. Principal: ${principal_usdc:,.0f} USDC")
    print(f"2. APY Difference: {apy_difference}%")
    print(f"3. Duration: {duration_days} days")
    print(f"4. Annual Yield: ${annual_yield:,.2f}")
    print(f"5. Yield for {duration_days} days: ${yield_earned:,.2f}")
    
    # Step 2: Calculate flash loan fee
    flash_loan_fee_rate = 0.0009  # 0.09%
    flash_loan_fee = principal_usdc * flash_loan_fee_rate
    
    print(f"\n6. Flash Loan Fee ({flash_loan_fee_rate*100}%): ${flash_loan_fee:,.2f}")
    
    # Step 3: Calculate gas cost
    gas_price_gwei = 0.004  # Base network typical
    gas_price_wei = gas_price_gwei * 10**9
    gas_used = 500000  # Deposit + Withdraw + Flash loan
    gas_cost_wei = gas_price_wei * gas_used
    gas_cost_eth = gas_cost_wei / 10**18
    eth_price_usd = 2500
    gas_cost_usd = gas_cost_eth * eth_price_usd
    
    print(f"7. Gas Cost:")
    print(f"   - Gas Price: {gas_price_gwei} gwei")
    print(f"   - Gas Used: {gas_used:,} units")
    print(f"   - Cost: {gas_cost_eth:.8f} ETH = ${gas_cost_usd:,.2f}")
    
    # Step 4: Calculate net profit
    net_profit = yield_earned - flash_loan_fee - gas_cost_usd
    profit_margin = (net_profit / principal_usdc) * 100
    
    print(f"\n8. NET PROFIT CALCULATION:")
    print(f"   Yield Earned:     ${yield_earned:,.2f}")
    print(f"   Flash Loan Fee:   -${flash_loan_fee:,.2f}")
    print(f"   Gas Cost:         -${gas_cost_usd:,.2f}")
    print(f"   ─────────────────────────────")
    print(f"   NET PROFIT:       ${net_profit:,.2f}")
    print(f"   Profit Margin:    {profit_margin:.3f}%")
    
    # Scenario 2: High yield (but verify legitimacy)
    print("\n\n📊 SCENARIO 2: High Yield (50% APY difference)")
    print("-" * 80)
    
    apy_difference_high = 50.0
    annual_yield_high = principal_usdc * (apy_difference_high / 100)
    yield_earned_high = annual_yield_high * (duration_days / 365)
    net_profit_high = yield_earned_high - flash_loan_fee - gas_cost_usd
    profit_margin_high = (net_profit_high / principal_usdc) * 100
    
    print(f"1. Principal: ${principal_usdc:,.0f} USDC")
    print(f"2. APY Difference: {apy_difference_high}%")
    print(f"3. Yield for {duration_days} days: ${yield_earned_high:,.2f}")
    print(f"4. Flash Loan Fee: ${flash_loan_fee:,.2f}")
    print(f"5. Gas Cost: ${gas_cost_usd:,.2f}")
    print(f"6. NET PROFIT: ${net_profit_high:,.2f} ({profit_margin_high:.3f}%)")
    
    # Scenario 3: Minimum profitable amount
    print("\n\n📊 SCENARIO 3: Minimum Profitable Amount")
    print("-" * 80)
    
    # For a given APY difference, what's the minimum amount needed?
    apy_diff = 2.0  # 2% APY difference
    min_duration = 1  # 1 day minimum
    
    # We need: Yield > Fees + Gas
    # Principal × (APY/100) × (Days/365) > Flash Fee + Gas
    # Principal × (APY/100) × (Days/365) > Principal × 0.0009 + Gas
    # Principal × [(APY/100) × (Days/365) - 0.0009] > Gas
    # Principal > Gas / [(APY/100) × (Days/365) - 0.0009]
    
    total_fees = flash_loan_fee + gas_cost_usd
    min_principal = total_fees / ((apy_diff / 100) * (min_duration / 365) - 0.0009)
    
    print(f"For {apy_diff}% APY difference over {min_duration} day:")
    print(f"Total Fees: ${total_fees:,.2f}")
    print(f"Minimum Principal Needed: ${min_principal:,.2f} USDC")
    
    # Break-even analysis
    print("\n\n📊 BREAK-EVEN ANALYSIS")
    print("-" * 80)
    print("Break-even point: Yield Earned = Flash Loan Fee + Gas Cost")
    print("\nFor different APY differences and durations:")
    print(f"{'APY Diff':<10} {'1 Day':<15} {'7 Days':<15} {'30 Days':<15}")
    print("-" * 60)
    
    for apy in [1, 2, 5, 10, 20, 50]:
        for days in [1, 7, 30]:
            min_amt = (flash_loan_fee + gas_cost_usd) / ((apy / 100) * (days / 365) - 0.0009)
            if min_amt > 0 and min_amt < 10000000:  # Reasonable range
                print(f"{apy:>6}%    ${min_amt:>12,.0f}    ${min_amt/7:>12,.0f}    ${min_amt/30:>12,.0f}")
            else:
                print(f"{apy:>6}%    {'N/A':<15}    {'N/A':<15}    {'N/A':<15}")
    
    # How to verify legitimate yields
    print("\n\n🔍 HOW TO VERIFY LEGITIMATE YIELDS")
    print("="*80)
    print("""
    RED FLAGS (Likely NOT legitimate):
    ✓ APY > 1000% - Usually temporary incentives
    ✓ TVL < $10,000 - Too small, might be manipulation
    ✓ New protocol (< 30 days old) - High risk
    ✓ No audit or anonymous team - Scam risk
    ✓ Yields change dramatically day-to-day - Unstable
    
    GREEN FLAGS (Likely legitimate):
    ✓ APY 2-20% - Normal DeFi range
    ✓ TVL > $100,000 - Sufficient liquidity
    ✓ Established protocol (> 6 months) - Proven track record
    ✓ Audited by reputable firms - Security verified
    ✓ Stable yields over time - Sustainable model
    ✓ Clear yield source (lending, LP fees, etc.) - Transparent
    
    VERIFICATION STEPS:
    1. Check protocol documentation
    2. Verify yield source (where does the APY come from?)
    3. Check TVL and liquidity depth
    4. Review smart contract audits
    5. Monitor yield stability over time
    6. Check if rewards are temporary incentives
    """)
    
    # Real-world example calculation
    print("\n\n💡 REAL-WORLD EXAMPLE")
    print("="*80)
    print("""
    Example: Aave vs Compound
    - Aave USDC: 3% APY
    - Compound USDC: 5% APY
    - Difference: 2% APY
    
    Flash Loan: $500,000 USDC
    Duration: 30 days
    
    Calculation:
    1. Yield Earned = $500,000 × 2% × (30/365) = $821.92
    2. Flash Loan Fee = $500,000 × 0.09% = $450.00
    3. Gas Cost = ~$0.01 (Base network)
    4. Net Profit = $821.92 - $450.00 - $0.01 = $371.91
    
    Profit Margin: 0.074% (very small, but legitimate)
    
    ⚠️  NOTE: This requires $500k+ to be profitable!
    """)

if __name__ == "__main__":
    calculate_yield_farming_profit()
