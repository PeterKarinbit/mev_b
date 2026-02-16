
# Speed-Demon MEV Bot v6.5

Universal Flash Loan Arbitrage Bot for the Base Network.

## Features
- **Balancer Flash Loans**: Zero-fee flash loans for maximum profitability.
- **Multi-DEX Support**: 
  - Uniswap V3 (Dynamic Fees)
  - Aerodrome V2 (Stable/Volatile)
  - Aerodrome Slipstream (Concentrated Liquidity)
  - PancakeSwap V3 (Base)
- **Telegram Notifications**: Real-time alerts for attacks and successful trades.
- **Gas Optimized**: Built-in simulation and threshold checks to avoid losing gas on unprofitable trades.

## Setup
1. Clone the repo.
2. Install dependencies: `pip install web3 httpx python-dotenv`.
3. Configure `.env`:
   ```env
   BOT_ADDRESS=0xYourAddress
   BOT_PRIVATE_KEY=YourPrivateKey
   TELEGRAM_BOT_TOKEN=YourToken
   TELEGRAM_CHAT_ID=YourChatID
   ```
4. Deploy the `UniversalDemonArb` contract (or use the existing one at `0xDd5C596fB7d3E895818b7bAFfbF021058477C38A`).

## Running the Bot
```bash
python vvv_flash_orb.py
```

## Contracts
- **Universal Engine**: `0xDd5C596fB7d3E895818b7bAFfbF021058477C38A`
- **Proxy/Legacy**: See `UniversalDemonArb.sol` for source.

---
*Created by Antigravity.*
