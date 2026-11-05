//! Frozen docs/av-wire-v1.md framing; opaque payload, no allocation.
use super::protocol;
pub const HEADER: usize = 48;
pub const MAX: usize = 560;
pub const RATE: u32 = 48293;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Hello,
    Start,
    Keep,
    Stop,
    Audio,
    Offer,
    Input,
}
#[derive(Clone, Copy, Debug)]
pub struct Packet<'a> {
    pub kind: Kind,
    pub cookie: u64,
    pub sequence: u32,
    pub flags: u32,
    pub timestamp: u64,
    pub payload: &'a [u8],
}
pub fn newer(candidate: u32, previous: u32) -> bool {
    let delta = candidate.wrapping_sub(previous);
    delta != 0 && delta < 0x8000_0000
}
pub fn crc(bytes: &[u8]) -> u32 {
    !protocol::crc_update(!0, bytes)
}
pub fn packet_crc(bytes: &[u8]) -> u32 {
    let mut c = protocol::crc_update(!0, &bytes[..40]);
    c = protocol::crc_update(c, &[0; 4]);
    !protocol::crc_update(c, &bytes[44..])
}
pub fn parse(bytes: &[u8]) -> Result<Packet<'_>, ()> {
    if bytes.len() < HEADER
        || bytes.len() > MAX
        || bytes[4] != 1
        || u16::from_be_bytes([bytes[6], bytes[7]]) != 48
    {
        return Err(());
    }
    let u32at = |i| u32::from_be_bytes(bytes[i..i + 4].try_into().unwrap());
    let cookie = u64::from_be_bytes(bytes[8..16].try_into().unwrap());
    let sequence = u32at(16);
    let frames = u16::from_be_bytes([bytes[24], bytes[25]]);
    let length = u16::from_be_bytes([bytes[26], bytes[27]]) as usize;
    let flags = u32at(28);
    if cookie == 0
        || u32at(20) != RATE
        || u32at(44) != 0
        || length + HEADER != bytes.len()
        || packet_crc(bytes) != u32at(40)
    {
        return Err(());
    }
    let kind = match (&bytes[..4], bytes[5]) {
        (b"MSC1", 1) if sequence == 0 && frames == 0 && length == 0 && flags <= 1 => Kind::Hello,
        (b"MSC1", 2) if sequence == 1 && frames == 0 && length == 8 && flags <= 1 => Kind::Start,
        (b"MSC1", 3) if frames == 0 && length == 0 && flags == 0 => Kind::Keep,
        (b"MSC1", 4) if frames == 0 && length == 0 && flags == 0 => Kind::Stop,
        (b"MSA1", 1) if frames == 505 && length == 512 && flags == 0 => Kind::Audio,
        (b"MSR1", 1) if sequence == 0 && frames == 0 && length == 8 && flags <= 1 => Kind::Offer,
        (b"MSI1", 1) if frames == 0 && length == 32 && flags == 0 => Kind::Input,
        _ => return Err(()),
    };
    Ok(Packet {
        kind,
        cookie,
        sequence,
        flags,
        timestamp: u64::from_be_bytes(bytes[32..40].try_into().unwrap()),
        payload: &bytes[48..],
    })
}
pub fn encode<'a>(
    kind: Kind,
    cookie: u64,
    sequence: u32,
    flags: u32,
    timestamp: u64,
    payload: &[u8],
    out: &'a mut [u8],
) -> Result<&'a [u8], ()> {
    if out.len() < 48 + payload.len() || payload.len() > 512 {
        return Err(());
    }
    let n = 48 + payload.len();
    out[..n].fill(0);
    let (magic, ty) = match kind {
        Kind::Hello => (b"MSC1", 1),
        Kind::Start => (b"MSC1", 2),
        Kind::Keep => (b"MSC1", 3),
        Kind::Stop => (b"MSC1", 4),
        Kind::Audio => (b"MSA1", 1),
        Kind::Offer => (b"MSR1", 1),
        Kind::Input => (b"MSI1", 1),
    };
    out[..4].copy_from_slice(magic);
    out[4] = 1;
    out[5] = ty;
    out[6..8].copy_from_slice(&48u16.to_be_bytes());
    out[8..16].copy_from_slice(&cookie.to_be_bytes());
    out[16..20].copy_from_slice(&sequence.to_be_bytes());
    out[20..24].copy_from_slice(&RATE.to_be_bytes());
    out[24..26].copy_from_slice(&(if kind == Kind::Audio { 505u16 } else { 0 }).to_be_bytes());
    out[26..28].copy_from_slice(&(payload.len() as u16).to_be_bytes());
    out[28..32].copy_from_slice(&flags.to_be_bytes());
    out[32..40].copy_from_slice(&timestamp.to_be_bytes());
    out[48..n].copy_from_slice(payload);
    let c = packet_crc(&out[..n]);
    out[40..44].copy_from_slice(&c.to_be_bytes());
    parse(&out[..n])?;
    Ok(&out[..n])
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn all_classes_roundtrip() {
        for (k, seq, flags, p) in [
            (Kind::Hello, 0, 1, vec![]),
            (Kind::Start, 1, 1, vec![0; 8]),
            (Kind::Keep, 2, 0, vec![]),
            (Kind::Stop, 3, 0, vec![]),
            (Kind::Audio, 0, 0, vec![0; 512]),
            (Kind::Offer, 0, 1, vec![0; 8]),
            (Kind::Input, 0, 0, vec![0; 32]),
        ] {
            let mut out = [0; 560];
            let b = encode(k, 9, seq, flags, 100, &p, &mut out).unwrap();
            let parsed = parse(b).unwrap();
            assert_eq!(parsed.kind, k);
            assert_eq!(parsed.sequence, seq);
            assert_eq!(parsed.payload, p)
        }
    }
    #[test]
    fn every_header_byte_corruption_rejected() {
        let mut b = [0; 560];
        let n = encode(Kind::Audio, 1, 0, 0, 0, &[0; 512], &mut b)
            .unwrap()
            .len();
        for i in 0..n {
            let mut c = b;
            c[i] ^= 1;
            assert!(parse(&c[..n]).is_err(), "byte{i}");
        }
        assert!(parse(&b[..n - 1]).is_err());
    }
    #[test]
    fn sequence_wrap() {
        assert!(newer(0, u32::MAX));
        assert!(!newer(1, 1));
        assert!(!newer(0x80000001, 1));
        assert!(!newer(u32::MAX, 0));
    }
}
