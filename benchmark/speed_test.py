import time
import math

class Trade:
    def __init__(self, id, price, amount):
        self.id = id
        self.price = price
        self.amount = amount

def test_parsing():
    start = time.time()
    for i in range(100000):
        s = "{\"p\": 2500.50, \"v\": 100}"
        p = float(s[6:13])
    end = time.time()
    print(f"Tests A (Parsing): {(end-start)*1000:.2f} ms")

def test_math():
    start = time.time()
    result = 0
    for i in range(1000000):
        result += math.sqrt(i * 1.05) / 3.14159
    end = time.time()
    print(f"Tests B (Math): {(end-start)*1000:.2f} ms")

def test_memory():
    start = time.time()
    for i in range(500000):
        t = Trade("tx_0x123", 100.50, 1.0)
    end = time.time()
    print(f"Tests C (Memory): {(end-start)*1000:.2f} ms")

print("🐍 PYTHON MULTI-SCENARIO BENCHMARK")
test_parsing()
test_math()
test_memory()
