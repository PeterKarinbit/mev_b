use std::time::Instant;

struct Trade {
    id: String,
    price: f64,
    amount: f64,
}

fn test_parsing() {
    let start = Instant::now();
    for _ in 0..100_000 {
        let s = "{\"p\": 2500.50, \"v\": 100}";
        let _p: f64 = s[6..13].parse().unwrap();
    }
    let duration = start.elapsed();
    println!("Tests A (Parsing): {:.2} ms", duration.as_secs_f64() * 1000.0);
}

fn test_math() {
    let start = Instant::now();
    let mut result = 0.0;
    for i in 0..1_000_000 {
        result += (i as f64 * 1.05).sqrt() / 3.14159;
    }
    let duration = start.elapsed();
    println!("Tests B (Math): {:.2} ms", duration.as_secs_f64() * 1000.0);
}

fn test_memory() {
    let start = Instant::now();
    for _ in 0..500_000 {
        let _t = Trade {
            id: String::from("tx_0x123"),
            price: 100.50,
            amount: 1.0,
        };
    }
    let duration = start.elapsed();
    println!("Tests C (Memory): {:.2} ms", duration.as_secs_f64() * 1000.0);
}

fn main() {
    println!("🦀 RUST MULTI-SCENARIO BENCHMARK");
    test_parsing();
    test_math();
    test_memory();
}
