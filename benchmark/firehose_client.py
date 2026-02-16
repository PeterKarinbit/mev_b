import asyncio
import websockets
import json
import time

async def client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("🐍 CLIENT: Connected")
        count = 0
        start = time.time()
        
        async for message in websocket:
            data = json.loads(message) # Parse it
            if count == 0: start = time.time() # Accurate start
            count += 1
            if count >= 100000: break
            
        end = time.time()
        duration = end - start
        
        print(f"🐍 PYTHON: {count} messages in {duration:.4f}s")
        print(f"RATE: {count/duration:.2f} MSG/SEC")

if __name__ == "__main__":
    asyncio.run(client())
