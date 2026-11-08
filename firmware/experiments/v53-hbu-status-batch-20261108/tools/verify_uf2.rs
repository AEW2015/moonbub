#[path = "../handheld-dfu/src/uf2.rs"]
mod uf2;

#[repr(align(4))]
struct Aligned([u8; 512]);

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let image = std::fs::read(&args[1]).unwrap();
    let binary = std::fs::read(&args[2]).unwrap();
    assert_eq!(image.len() % 512, 0);
    let count = image.len() / 512;
    assert!(count > 0);
    let mut payload = Vec::new();
    for (i, bytes) in image.chunks_exact(512).enumerate() {
        let block_bytes = Aligned(bytes.try_into().unwrap());
        let block = uf2::Uf2Block::from_bytes(&block_bytes.0).unwrap();
        assert_eq!(block.flags(), 0xA000);
        assert_eq!(block.family_id(), 0xC47E5767);
        assert_eq!(block.payload().len(), 256);
        assert_eq!(block.block_number(), i as u32);
        assert_eq!(block.total_blocks(), count as u32);
        assert_eq!(block.address(), 0x100000 + i as u32 * 256);
        assert!(block.address() + 256 <= 0x600000);
        assert_eq!(block.get_extension_tag(0xC8A729), Some(b"bub!\0\0\x04\x01".as_slice()));
        payload.extend_from_slice(block.payload());
    }
    assert_eq!(&payload[..binary.len()], binary.as_slice());
    assert!(payload[binary.len()..].iter().all(|&b| b == 0xff));
    assert!(payload.len() - binary.len() < 256);
    println!("PASS: {count} blocks parsed by production DFU parser; Rev4 identity, application addresses, and binary round trip verified.");
}
