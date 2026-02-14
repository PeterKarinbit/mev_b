#!/bin/bash
# 🚀 LINKIVO MEV LAUNCHER (RENDER)
# Start both bots in parallel background processes

echo "Starting Whale Radar (Liquidation Monitor)..."
python3 mev_bot/radar.py &

echo "Starting Gorilla Bot (Arbitrage + Flash Engine)..."
python3 mev_bot/gorilla_bot.py &

# Wait for both background processes to keep the container alive
wait
