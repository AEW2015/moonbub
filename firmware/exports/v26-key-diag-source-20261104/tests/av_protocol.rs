#[path = "../handheld/src/streaming/adpcm.rs"]
mod adpcm;
#[path = "../handheld/src/streaming/audio_io.rs"]
mod audio_io;
#[path = "../handheld/src/streaming/av_session.rs"]
mod av_session;
#[path = "../handheld/src/streaming/av_wire.rs"]
mod av_wire;
#[path = "../handheld/src/streaming/protocol.rs"]
mod protocol;

#[test]
fn independent_ffmpeg_pcm_golden() {
    let block = include_bytes!("fixtures/av-v1/stereo-505.ima");
    let expected = include_bytes!("fixtures/av-v1/stereo-505-decoded.s16le");
    let mut actual = [0u8; 2020];
    adpcm::decode(block, &mut actual).unwrap();
    assert_eq!(
        actual.iter().zip(expected.iter()).position(|(a, b)| a != b),
        None,
        "first PCM byte mismatch"
    );
}
#[test]
fn all_host_wire_vectors_roundtrip_exact() {
    for vector in [
        include_bytes!("fixtures/av-v1/hello.bin").as_slice(),
        include_bytes!("fixtures/av-v1/offer.bin").as_slice(),
        include_bytes!("fixtures/av-v1/start.bin").as_slice(),
        include_bytes!("fixtures/av-v1/keep.bin").as_slice(),
        include_bytes!("fixtures/av-v1/audio.bin").as_slice(),
        include_bytes!("fixtures/av-v1/input.bin").as_slice(),
        include_bytes!("fixtures/av-v1/stop.bin").as_slice(),
    ] {
        let p = av_wire::parse(vector).unwrap();
        let mut out = [0; 560];
        let encoded = av_wire::encode(
            p.kind,
            p.cookie,
            p.sequence,
            p.flags,
            p.timestamp,
            p.payload,
            &mut out,
        )
        .unwrap();
        assert_eq!(encoded, vector);
    }
}

#[test]fn correct_crc_does_not_bypass_profile_checks(){let base=include_bytes!("fixtures/av-v1/audio.bin");for at in[0,4,5,6,7,20,21,22,23,24,25,26,27,28,29,30,31,44,45,46,47]{let mut data=*base;data[at]^=0x40;let c=av_wire::packet_crc(&data);data[40..44].copy_from_slice(&c.to_be_bytes());assert!(av_wire::parse(&data).is_err(),"field{at}");}let mut data=*base;data[8..16].fill(0);let c=av_wire::packet_crc(&data);data[40..44].copy_from_slice(&c.to_be_bytes());assert!(av_wire::parse(&data).is_err());}
#[test]fn ima_every_index_and_reserved_byte_boundary(){for index in 0..=255u8{for at in[2,6]{let mut b=[0;512];b[at]=index;assert_eq!(adpcm::validate(&b).is_ok(),index<=88);}}for value in 1..=255u8{for at in[3,7]{let mut b=[0;512];b[at]=value;assert!(adpcm::validate(&b).is_err());}}}
