//! Native subprocess bridge to the unmodified portable firmware receiver.
#[allow(dead_code)]
#[path = "../../../firmware/handheld/src/streaming/protocol97.rs"]
mod protocol97;
use std::io::{self, BufRead, Write};

fn decode(s: &str) -> Vec<u8> {
    assert_eq!(s.len() % 2, 0);
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i+2], 16).unwrap()).collect()
}
fn encode(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }
fn main() {
    let mut receiver = protocol97::Receiver::default();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let mut words = line.split_whitespace();
        let response = match words.next().unwrap() {
            "NEW" => {
                let profile: u32 = words.next().unwrap().parse().unwrap();
                let generation: u32 = words.next().unwrap().parse().unwrap();
                receiver = protocol97::Receiver::new(protocol97::SinkConfig {
                    opaque_profile: if profile == 0 { None } else { Some(profile) },
                }, generation);
                "OK".to_owned()
            },
            "SETUP" => match receiver.setup(&decode(words.next().unwrap())) {
                Ok(ack) => format!("ACK {}", encode(&ack)), Err(e) => format!("ERR {e:?}"),
            },
            "DATA" => match receiver.accept(&decode(words.next().unwrap())) {
                Ok(c) => format!("CHUNK {} {} {} {}", c.index, c.offset, c.count, c.crc_complete),
                Err(e) => format!("ERR {e:?}"),
            },
            _ => panic!("unexpected command"),
        };
        println!("{response}");
        io::stdout().flush().unwrap();
    }
}
