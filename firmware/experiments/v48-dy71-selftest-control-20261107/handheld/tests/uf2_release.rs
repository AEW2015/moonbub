// Validate a packaged application with the exact UF2 block parser used by
// handheld-dfu. Run with UF2_UNDER_TEST set to the release file.
#[path = "../../handheld-dfu/src/uf2.rs"]
mod uf2;

#[repr(align(4))]
struct Aligned([u8; 512]);

#[test]
fn every_release_block_is_accepted_by_the_dfu_parser() {
    let path = std::env::var("UF2_UNDER_TEST").expect("set UF2_UNDER_TEST");
    let image = std::fs::read(path).unwrap();
    assert!(!image.is_empty());
    assert_eq!(image.len() % 512, 0);
    let count = (image.len() / 512) as u32;
    for (index, raw) in image.chunks_exact(512).enumerate() {
        let mut aligned = Aligned([0; 512]);
        aligned.0.copy_from_slice(raw);
        let block = uf2::Uf2Block::from_bytes(&aligned.0).expect("invalid UF2 block");
        assert_eq!(block.family_id(), 0xC47E_5767);
        assert_eq!(block.payload().len(), 256);
        assert_eq!(block.block_number(), index as u32);
        assert_eq!(block.total_blocks(), count);
        assert_eq!(block.address(), 0x0010_0000 + index as u32 * 256);
        assert_eq!(block.get_extension_tag(0xC8_A729), Some(&b"bub!\0\0\x04\x01"[..]));
    }
}
