use std::time::Instant;
use std::hint::black_box; // Prevents compiler from optimizing away the loop

fn main() {
    println!("🦀 RUST OPTIMIZATION SHOWDOWN (10,000,000 OPS)");
    
    let simulated_price: f64 = black_box(2500.50);
    let mut accumulator: f64 = 0.0;
    
    let start = Instant::now();
    
    // Using iterators which Rust can vectorize (SIMD)
    for i in 0..10_000_000 {
        let val = (i as f64) * simulated_price;
        accumulator += val.sin() * val.cos();
    }
    
    // Prevent optimizing away the result
    black_box(accumulator);
    
    let duration = start.elapsed();
    let nanos = duration.as_nanos();
    let per_op = nanos as f64 / 10_000_000.0;
    
    println!("Total Time: {:.2} ms", duration.as_secs_f64() * 1000.0);
    println!("Time Per Op: {:.2} NANOSECONDS ⚡", per_op);
}
