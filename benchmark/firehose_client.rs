use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use futures_util::StreamExt;
use std::time::Instant;
use serde_json::Value;

#[tokio::main]
async fn main() {
    let url = "ws://localhost:8765";
    let (ws_stream, _) = connect_async(url).await.expect("Failed to connect");
    let (_, mut read) = ws_stream.split();
    
    println!("🦀 RUST CLIENT: Connected");
    let mut count = 0;
    
    // First message starts timer
    if let Some(msg) = read.next().await {
        let _data: Value = serde_json::from_str(msg.unwrap().to_text().unwrap()).unwrap();
        count += 1;
    }
    
    let start = Instant::now();
    
    while let Some(msg) = read.next().await {
        let msg = msg.unwrap();
        if msg.is_text() || msg.is_binary() {
            let _data: Value = serde_json::from_str(msg.to_text().unwrap()).unwrap();
            count += 1;
        }
        if count >= 100000 { break; }
    }
    
    let elapsed = start.elapsed();
    let seconds = elapsed.as_secs_f64();
    
    println!("🦀 RUST: {} messages in {:.4}s", count, seconds);
    println!("RATE: {:.2} MSG/SEC", count as f64 / seconds);
}
