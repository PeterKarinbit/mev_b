import asyncio
import websockets
import json
import time

async def handler(websocket):
    print("🔥 Client Connected. Unloading 100,000 Messages...")
    # Pre-generate JSON for speed (server is just sender)
    payload = json.dumps({"p": 1234.56, "liquidity": 500000, "pair": "0xABCDEF"})
    
    start = time.time()
    for _ in range(100000):
        await websocket.send(payload)
    end = time.time()
    
    print(f"🔥 Blast finished in {end - start:.2f}s")
    await websocket.close()

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("🔥 FIREHOSE SERVER LISTENING on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
