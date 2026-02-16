# Maximum Flash Loan Limits

## 📊 Current Balancer Vault Liquidity (Base Network)

**As of latest check:**

### WETH (Ethereum)
- **Total Available:** 53.89 ETH
- **Value:** ~$188,609 (at $3,500/ETH)

### USDC (Stablecoin)
- **Total Available:** 122,659 USDC
- **Value:** $122,659

---

## 💰 Maximum Flash Loan Amounts

### WETH Flash Loans

| Risk Level | Amount | Value (USD) | Recommendation |
|------------|--------|-------------|----------------|
| **Conservative** | 5.39 ETH | ~$18,861 | ✅ **RECOMMENDED** |
| **Aggressive** | 10.78 ETH | ~$37,722 | ⚠️ Higher risk |
| **Maximum** | 26.94 ETH | ~$94,304 | ❌ **NOT RECOMMENDED** |

### USDC Flash Loans

| Risk Level | Amount | Value (USD) | Recommendation |
|------------|--------|-------------|----------------|
| **Conservative** | 12,266 USDC | $12,266 | ✅ **RECOMMENDED** |
| **Aggressive** | 24,532 USDC | $24,532 | ⚠️ Higher risk |
| **Maximum** | 61,329 USDC | $61,329 | ❌ **NOT RECOMMENDED** |

---

## 🧮 How Limits Are Calculated

### Formula:
```
Maximum Flash Loan = Vault Balance × Percentage
```

### Why There Are Limits:

1. **Liquidity Impact**
   - Borrowing too much can move prices
   - Causes slippage in your trades
   - Makes arbitrage unprofitable

2. **Market Manipulation**
   - Large loans can be seen as manipulation
   - May trigger protocol safeguards

3. **Practical Limits**
   - Balancer allows up to vault balance
   - But you should use much less for safety

---

## ⚠️ Risk Considerations

### Why NOT Borrow Maximum:

1. **Slippage**
   - Large trades move prices
   - You buy high, sell low (opposite of arbitrage!)
   - Can turn profit into loss

2. **Gas Costs**
   - Larger transactions = more gas
   - Can exceed profit margins

3. **Competition**
   - Other bots compete for same opportunities
   - Larger trades = more visible = more competition

4. **Flash Loan Fee**
   - 0.09% fee applies to entire amount
   - $100k loan = $90 fee
   - $1M loan = $900 fee (same percentage, but larger absolute)

---

## 💡 Recommended Strategy

### For Arbitrage:
- **Start Small:** 0.01-0.05 ETH or 5,000-25,000 USDC
- **Scale Up:** Gradually increase as you find opportunities
- **Stay Under 5%:** Keep loans under 5% of vault liquidity
- **Monitor:** Watch gas costs vs profits

### For Yield Farming:
- **Need Large Amounts:** $100k+ to be profitable
- **But Vault Limit:** Only 122k USDC available
- **Solution:** Use maximum available (but verify yields first!)

### Current Bot Configuration:
- ✅ VIRTUAL: 0.01 ETH (safe)
- ✅ DEGEN: 0.02 ETH (safe)
- ✅ AERO: 0.025 ETH (safe)
- ✅ BASE: 15,000 USDC (safe - within limits)
- ✅ SYND: 20,000 USDC (safe - within limits)
- ✅ LQTY: 10,000 USDC (safe)

---

## 📈 Profitability by Loan Size

### Example: 2% APY difference, 7 days

| Loan Amount | Yield Earned | Flash Fee | Gas | Net Profit |
|-------------|--------------|-----------|-----|------------|
| $10,000 | $3.84 | $9.00 | $0.01 | **-$5.17** ❌ |
| $50,000 | $19.18 | $45.00 | $0.01 | **-$25.83** ❌ |
| $100,000 | $38.36 | $90.00 | $0.01 | **-$51.65** ❌ |
| $500,000 | $191.78 | $450.00 | $0.01 | **-$258.23** ❌ |

**⚠️ Not profitable with 2% APY difference!**

### Example: 10% APY difference, 7 days

| Loan Amount | Yield Earned | Flash Fee | Gas | Net Profit |
|-------------|--------------|-----------|-----|------------|
| $10,000 | $19.18 | $9.00 | $0.01 | **$10.17** ✅ |
| $50,000 | $95.89 | $45.00 | $0.01 | **$50.88** ✅ |
| $100,000 | $191.78 | $90.00 | $0.01 | **$101.77** ✅ |
| $122,659 (MAX) | $235.07 | $110.39 | $0.01 | **$124.67** ✅ |

**✅ Profitable with 10% APY difference!**

---

## 🎯 Key Takeaways

1. **Maximum Available:**
   - WETH: ~27 ETH (but use 5-10 ETH max)
   - USDC: ~61k USDC (but use 12-24k max)

2. **For Yield Farming:**
   - Need $100k+ for profitability
   - But vault only has $122k USDC
   - **You can use most of it** (but verify yields first!)

3. **For Arbitrage:**
   - Smaller amounts work better
   - Less slippage = more profit
   - Current bot uses $500 USDC (very safe)

4. **Flash Loan Fee:**
   - Always 0.09% regardless of amount
   - $100k = $90 fee
   - $1M = $900 fee (if vault had that much)

---

## ✅ Summary

**Maximum Flash Loan You Can Borrow:**
- **WETH:** Up to 26.94 ETH (~$94k) - but use 5-10 ETH max
- **USDC:** Up to 61,329 USDC (~$61k) - but use 12-24k max

**Recommended:**
- **Conservative:** 5.39 ETH or 12,266 USDC
- **Aggressive:** 10.78 ETH or 24,532 USDC
- **Maximum (risky):** 26.94 ETH or 61,329 USDC

**Your current bot uses $500 USDC - very safe!** ✅
