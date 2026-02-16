#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <chrono>

using namespace std;
using namespace std::chrono;

struct Trade {
    string id;
    double price;
    double amount;
};

void test_parsing() {
    auto start = high_resolution_clock::now();
    for(int i=0; i<100000; i++) {
        string s = "{\"p\": 2500.50, \"v\": 100}";
        double p = stod(s.substr(6, 7));
    }
    auto end = high_resolution_clock::now();
    cout << "Tests A (Parsing): " << duration_cast<milliseconds>(end-start).count() << " ms" << endl;
}

void test_math() {
    auto start = high_resolution_clock::now();
    double result = 0;
    for(int i=0; i<1000000; i++) {
        result += sqrt(i * 1.05) / 3.14159;
    }
    auto end = high_resolution_clock::now();
    cout << "Tests B (Math): " << duration_cast<milliseconds>(end-start).count() << " ms" << endl;
}

void test_memory() {
    auto start = high_resolution_clock::now();
    for(int i=0; i<500000; i++) {
        Trade* t = new Trade();
        t->id = "tx_0x123";
        t->price = 100.50;
        delete t;
    }
    auto end = high_resolution_clock::now();
    cout << "Tests C (Memory): " << duration_cast<milliseconds>(end-start).count() << " ms" << endl;
}

int main() {
    cout << "🔥 C++ MULTI-SCENARIO BENCHMARK" << endl;
    test_parsing();
    test_math();
    test_memory();
    return 0;
}
