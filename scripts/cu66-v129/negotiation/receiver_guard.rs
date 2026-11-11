//! Host-only test of the unchanged production MSV1 receiver's codec boundary.
#[allow(dead_code)]
#[path = "../../../firmware/handheld/src/streaming/protocol.rs"]
mod protocol;

use std::{env, fs};

fn framed_packets(input: &[u8]) -> Vec<Vec<u8>> {
    let mut packets = Vec::new();
    let mut offset = 0;
    while offset < input.len() {
        assert!(offset + 2 <= input.len(), "truncated framing prefix");
        let length = u16::from_be_bytes([input[offset], input[offset + 1]]) as usize;
        offset += 2;
        assert!(offset + length <= input.len(), "truncated framed packet");
        packets.push(input[offset..offset + length].to_vec());
        offset += length;
    }
    packets
}

fn main() {
    let path = env::args().nth(1).expect("usage: receiver_guard FIXTURE");
    let packets = framed_packets(&fs::read(path).expect("read fixture"));
    assert_eq!(packets.len(), 26);
    assert!(packets.iter().all(|p| p[5] == 1));
    let original_id = u32::from_be_bytes(packets[0][8..12].try_into().unwrap());
    let next_id = original_id.checked_add(1).unwrap();
    let expected_len = protocol::Header::parse(&packets[0]).unwrap().length as usize;
    let mut recovered_count = 0;
    for codec in 0u8..=255 {
        if codec == 1 { continue; }
        let mut first_unknown = packets[0].clone();
        first_unknown[5] = codec;
        assert_eq!(protocol::Header::parse(&first_unknown), Err(protocol::Error::Format));
        let mut receiver = protocol::Receiver::default();
        assert_eq!(receiver.accept(&first_unknown), Err(protocol::Error::Format));

        // A bad codec in the middle aborts the active frame; trailing packets
        // cannot complete it. The next frame ID must still recover correctly.
        let mut receiver = protocol::Receiver::default();
        assert!(!receiver.accept(&packets[0]).unwrap().1);
        let mut middle_unknown = packets[1].clone();
        middle_unknown[5] = codec;
        assert_eq!(receiver.accept(&middle_unknown), Err(protocol::Error::Format));
        assert_eq!(receiver.accept(&packets[2]), Err(protocol::Error::Sequence));
        let mut bytes = 0usize;
        for (index, packet) in packets.iter().enumerate() {
            let mut retry = packet.clone();
            retry[8..12].copy_from_slice(&next_id.to_be_bytes());
            let (header, done) = receiver.accept(&retry).expect("JPEG retry rejected");
            bytes += header.count as usize;
            assert_eq!(done, index + 1 == packets.len());
        }
        assert_eq!(bytes, expected_len);
        recovered_count += 1;
    }
    assert_eq!(recovered_count, 255);

    // A JPEG-labelled non-JPEG payload with a valid CRC crosses this parser:
    // format negotiation/content validation must happen at another boundary.
    let payload = b"CS88";
    let mut forged = packets[0][..protocol::HEADER].to_vec();
    forged[6..8].copy_from_slice(&3u16.to_be_bytes());
    forged[16..20].copy_from_slice(&(payload.len() as u32).to_be_bytes());
    forged[20..24].copy_from_slice(&0u32.to_be_bytes());
    forged[24..26].copy_from_slice(&(payload.len() as u16).to_be_bytes());
    let crc = !protocol::crc_update(!0, payload);
    forged[28..32].copy_from_slice(&crc.to_be_bytes());
    forged.extend_from_slice(payload);
    let mut receiver = protocol::Receiver::default();
    let (header, done) = receiver.accept(&forged).expect("label/CRC control");
    assert!(done && header.length == payload.len() as u32);

    println!("{{\"status\":\"TEST_PASS\",\"unknown_codec_ids_rejected\":255,\"aborted_frame_recoveries\":{},\"fixture_datagrams\":{},\"jpeg_frame_bytes\":{},\"mislabeled_cs88_accepted_by_protocol\":true,\"actual_rust_receiver\":true,\"actual_session_or_fpga_executed\":false}}", recovered_count, packets.len(), expected_len);
}
