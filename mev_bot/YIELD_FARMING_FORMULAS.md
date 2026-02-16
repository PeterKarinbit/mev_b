# Yield Farming Profit Formulas

## 📐 Core Formula

```
NET PROFIT = Yield Earned - Flash Loan Fee - Gas Cost
```

## 🔢 Detailed Breakdown

### 1. Yield Earned
```
Yield Earned = Principal × (APY Difference / 100) × (Duration in Days / 365)
```

**Example:**
- Principal: $100,000 USDC
- APY Difference: 5%
- Duration: 7 days
- Yield = $100,000 × 0.05 × (7/365) = **$95.89**

### 2. Flash Loan Fee
```
Flash Loan Fee = Principal × 0.0009
```
(0.09% fee on most flash loan providers)

**Example:**
- Principal: $100,000 USDC
- Fee = $100,000 × 0.0009 = **$90.00**

### 3. Gas Cost
```
Gas Cost (USD) = (Gas Price × Gas Used) / 10^18 × ETH Price
```

**Example (Base network):**
- Gas Price: 0.004 gwei = 0.004 × 10^9 wei
- Gas Used: 500,000 units
- ETH Price: $2,500
- Gas Cost = (0.004 × 10^9 × 500,000) / 10^18 × $2,500 = **$0.01**

### 4. Net Profit
```
Net Profit = Yield Earned - Flash Loan Fee - Gas Cost
```

**Example:**
- Yield Earned: $95.89
- Flash Loan Fee: -$90.00
- Gas Cost: -$0.01
- **Net Profit = $5.89**

## 📊 Minimum Profitable Amount

To find the minimum amount needed to be profitable:

```
Minimum Principal = (Flash Loan Fee + Gas Cost) / [(APY Difference / 100) × (Days / 365) - 0.0009]
```

**Example:**
- APY Difference: 2%
- Duration: 7 days
- Flash Loan Fee: $90
- Gas Cost: $0.01
- Min Principal = ($90 + $0.01) / [(0.02 × 7/365) - 0.0009]
- Min Principal = $90.01 / 0.000483 = **$186,355 USDC**

## ⚠️ Key Insights

### 1. Flash Loan Fee is Fixed Percentage
- **Always 0.09%** regardless of amount
- This means larger amounts = better profit margins
- $100k: Fee = $90
- $1M: Fee = $900 (same percentage!)

### 2. Gas Cost is Fixed
- **~$0.01 per transaction** on Base
- Doesn't scale with amount
- Becomes negligible for large amounts

### 3. Yield Scales with Amount AND Time
- More principal = more yield
- Longer duration = more yield
- But flash loans must be repaid in same transaction!

## 🎯 Profitability Thresholds

| APY Diff | Min Amount (1 day) | Min Amount (7 days) | Min Amount (30 days) |
|----------|-------------------|-------------------|---------------------|
| 1%       | Not profitable    | Not profitable    | Not profitable      |
| 2%       | Not profitable    | $186,355          | $43,456             |
| 5%       | $1,527,992        | $28,043           | $6,535              |
| 10%      | $88,430           | $12,297           | $2,870               |
| 20%      | $30,660           | $5,792            | $1,352               |
| 50%      | $10,358           | $2,239            | $523                 |

## ✅ Legitimate Yield Checklist

**RED FLAGS (Avoid):**
- ❌ APY > 1000% (usually temporary/scam)
- ❌ TVL < $10,000 (too risky)
- ❌ Protocol < 30 days old
- ❌ No audits
- ❌ Anonymous team

**GREEN FLAGS (Safe):**
- ✅ APY 2-20% (normal range)
- ✅ TVL > $100,000
- ✅ Protocol > 6 months old
- ✅ Audited by reputable firms
- ✅ Stable yields over time
- ✅ Clear yield source

## 💡 Real Example

**Aave vs Compound:**
- Aave USDC: 3% APY
- Compound USDC: 5% APY
- **Difference: 2% APY**

**With $500,000 USDC for 30 days:**
1. Yield = $500,000 × 0.02 × (30/365) = **$821.92**
2. Flash Loan Fee = $500,000 × 0.0009 = **$450.00**
3. Gas Cost = **$0.01**
4. **Net Profit = $371.91** ✅

**Profit Margin: 0.074%** (small but legitimate!)

## 🚨 Important Notes

1. **Flash loans must be repaid in same transaction** - you can't hold for days!
2. **Yield farming with flash loans is only profitable for:**
   - Large amounts ($100k+)
   - Significant APY differences (2%+)
   - Established, legitimate protocols

3. **The high APY numbers you saw (5000%+) are likely:**
   - Temporary incentives
   - Reward tokens (not stable)
   - Low TVL pools (risky)
   - **Verify before executing!**
