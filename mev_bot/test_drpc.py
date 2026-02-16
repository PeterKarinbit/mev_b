from web3 import Web3
import time

DRPC_URL = "https://lb.drpc.live/base/Ai4fl3BpEEt0rz-y6c7Opkdml53OCP4R8bEUcs5opQTS"

def test_rpc():
    print(f"Testing dRPC Speed for Base...")
    try:
        w3 = Web3(Web3.HTTPProvider(DRPC_URL))
        
        start = time.time()
        block = w3.eth.block_number
        end = time.time()
        
        print(f"✅ Success!")
        print(f"Latest Block: {block}")
        print(f"Latency: {(end - start) * 1000:.2f}ms")
        
        if w3.is_connected():
            print("Status: Connected and Ready for MEV.")
        else:
            print("Status: Failed to verify connection.")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_rpc()
