//! Host-only comparison; this is not an ESP32 throughput measurement.
#[allow(dead_code)]
#[path = "../handheld/src/streaming/protocol.rs"]
mod protocol;
use std::{hint::black_box, time::Instant};
fn main() {
    let data: Vec<u8> = (0..4096).map(|i| i as u8).collect();
    const REPEATS: usize = 8192;
    let start = Instant::now();
    let mut slow = !0u32;
    for _ in 0..REPEATS { slow = protocol::crc_update_bitwise(slow, black_box(&data)); }
    let slow_us = start.elapsed().as_micros();
    let start = Instant::now();
    let mut fast = !0u32;
    for _ in 0..REPEATS { fast = protocol::crc_update(fast, black_box(&data)); }
    let fast_us = start.elapsed().as_micros();
    assert_eq!(slow, fast);
    println!("HOST_ONLY bytes={} bitwise_us={} table_us={} crc={:08x}", REPEATS * data.len(), slow_us, fast_us, !fast);
}
