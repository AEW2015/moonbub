#![allow(dead_code)]
#[path = "../source/moonbub/protocol.rs"]
mod protocol;
use std::env;
use std::fs;

fn write_json_string(out: &mut String, value: &str) {
    out.push('"');
    for ch in value.chars() {
        match ch { '"' => out.push_str("\\\""), '\\' => out.push_str("\\\\"), '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"), '\t' => out.push_str("\\t"), c if c < ' ' => out.push('?'), c => out.push(c) }
    }
    out.push('"');
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 4 { return Err("usage: receiver_probe INPUT_FRAMED RECOVERED_JPEG EVENTS_JSON".into()); }
    let input = fs::read(&args[1])?;
    let mut recovered = Vec::<u8>::new();
    let mut pending = Vec::<u8>::new();
    let mut events = Vec::<String>::new();
    let mut feedback_bytes = Vec::<u8>::new();
    let mut receiver = protocol::Receiver::default();
    let mut offset = 0usize;
    let mut accepted_datagrams = 0u64;
    let mut accepted_payload_bytes = 0u64;
    let mut dropped = 0u32;
    let mut event_count = 0usize;
    while offset < input.len() {
        let index = event_count;
        if input.len() - offset < 2 {
            events.push(format!("{{\"type\":\"framing_error\",\"index\":{index},\"error\":\"truncated_u16_prefix\"}}"));
            dropped = dropped.saturating_add(1);
            break;
        }
        let length = u16::from_be_bytes([input[offset], input[offset + 1]]) as usize;
        offset += 2;
        if input.len() - offset < length {
            events.push(format!("{{\"type\":\"framing_error\",\"index\":{index},\"error\":\"truncated_datagram\"}}"));
            dropped = dropped.saturating_add(1);
            break;
        }
        let packet = &input[offset..offset + length];
        offset += length;
        match receiver.accept(packet) {
            Ok((header, done)) => {
                if header.offset == 0 { pending.clear(); }
                pending.extend_from_slice(&packet[protocol::HEADER..]);
                accepted_datagrams += 1;
                accepted_payload_bytes += header.count as u64;
                events.push(format!("{{\"type\":\"accepted\",\"index\":{index},\"id\":{},\"offset\":{},\"count\":{},\"done\":{}}}",
                    header.id, header.offset, header.count, done));
                if done {
                    if pending.len() != header.length as usize {
                        events.push(format!("{{\"type\":\"wrapper_error\",\"index\":{index},\"error\":\"recovered_length_mismatch\"}}"));
                        pending.clear(); dropped = dropped.saturating_add(1);
                    } else {
                        recovered.extend_from_slice(&pending);
                        pending.clear();
                        let feedback = protocol::feedback(1, 0, header.id, 0, accepted_payload_bytes as u32,
                                                          dropped, header.capture_us);
                        feedback_bytes.extend_from_slice(&feedback);
                        events.push(format!("{{\"type\":\"done\",\"index\":{index},\"id\":{},\"recovered_bytes\":{},\"feedback\":\"MSF1\"}}",
                            header.id, header.length));
                    }
                }
            }
            Err(error) => {
                pending.clear(); dropped = dropped.saturating_add(1);
                events.push(format!("{{\"type\":\"error\",\"index\":{index},\"error\":\"{:?}\"}}", error));
            }
        }
        event_count += 1;
    }
    let events_json = format!("[\n{}\n]\n", events.join(",\n"));
    fs::write(&args[2], &recovered)?;
    fs::write(&args[3], events_json)?;
    let mut feedback_path = args[3].clone(); feedback_path.push_str(".msf1");
    fs::write(feedback_path, feedback_bytes)?;
    eprintln!("receiver_probe accepted_datagrams={accepted_datagrams} accepted_payload_bytes={accepted_payload_bytes} recovered_bytes={} dropped={dropped} events={event_count}", recovered.len());
    Ok(())
}
