from web3 import Web3
import time

# I noticed the full URL in the UI often has some extra bits or the key ID.
# Let's try the direct public-redirect style URL.
DRPC_URL = "https://lb.drpc.live/base/Ai4fl3BpEEt0rz-y6c7Opkdml53OCP4R8bEUcs5opQTS"

def test_rpc():
    print(f"Testing dRPC Speed for Base...")
    try:
        # Use headers if needed, but 403 usually means the key isn't active on that specific path.
        w3 = Web3(Web3.HTTPProvider(DRPC_URL))
        
        start = time.time()
        # Try a simpler call first
        connected = w3.is_connected()
        end = time.time()
        
        if connected:
            print(f"✅ Success!")
            print(f"Latency: {(end - start) * 1000:.2f}ms")
        else:
            print(f"❌ Failed to connect to {DRPC_URL}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_rpc()
