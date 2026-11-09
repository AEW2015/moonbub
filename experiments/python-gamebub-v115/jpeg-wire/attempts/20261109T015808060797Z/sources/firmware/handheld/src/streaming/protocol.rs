//! Bounded MSV1 receiver state. No frame allocation and no ESP-IDF dependency.
pub const HEADER: usize = 40;
pub const CHUNK: usize = 1024;
pub const MAX_FRAME: u32 = 256 * 1024;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Header,
    Format,
    Bounds,
    Sequence,
    Integrity,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Header {
    pub flags: u16,
    pub id: u32,
    pub width: u16,
    pub height: u16,
    pub length: u32,
    pub offset: u32,
    pub count: u16,
    pub crc: u32,
    pub capture_us: u64,
}
impl Header {
    pub fn parse(packet: &[u8]) -> Result<Self, Error> {
        if packet.len() < HEADER || &packet[..4] != b"MSV1" || packet[4] != 1 {
            return Err(Error::Header);
        }
        let u16at = |n| u16::from_be_bytes([packet[n], packet[n + 1]]);
        let u32at = |n| u32::from_be_bytes(packet[n..n + 4].try_into().unwrap());
        let h = Self {
            flags: u16at(6),
            id: u32at(8),
            width: u16at(12),
            height: u16at(14),
            length: u32at(16),
            offset: u32at(20),
            count: u16at(24),
            crc: u32at(28),
            capture_us: u64::from_be_bytes(packet[32..40].try_into().unwrap()),
        };
        if packet[5] != 1
            || u16at(26) != 0
            || h.flags & !3 != 0
            || h.width != 720
            || h.height != 480
        {
            return Err(Error::Format);
        }
        if h.length == 0
            || h.length > MAX_FRAME
            || h.count == 0
            || h.count as usize > CHUNK
            || packet.len() != HEADER + h.count as usize
            || h.offset
                .checked_add(h.count as u32)
                .filter(|end| *end <= h.length)
                .is_none()
        {
            return Err(Error::Bounds);
        }
        if (h.offset == 0) != (h.flags & 1 != 0)
            || (h.offset + h.count as u32 == h.length) != (h.flags & 2 != 0)
        {
            return Err(Error::Sequence);
        }
        Ok(h)
    }
}
pub fn crc_update(mut crc: u32, data: &[u8]) -> u32 {
    for byte in data {
        crc ^= *byte as u32;
        for _ in 0..8 {
            crc = (crc >> 1) ^ (0xEDB88320u32 & 0u32.wrapping_sub(crc & 1));
        }
    }
    crc
}
#[derive(Default)]
pub struct Receiver {
    active: Option<Header>,
    offset: u32,
    crc: u32,
    last_id: Option<u32>,
}
impl Receiver {
    pub fn abort(&mut self) {
        self.active = None;
        self.offset = 0;
        self.crc = !0;
    }
    /// Call before forwarding. A bad packet invalidates the incomplete frame.
    pub fn accept(&mut self, packet: &[u8]) -> Result<(Header, bool), Error> {
        let result = self.check(packet);
        if result.is_err() {
            self.abort();
        }
        result
    }
    fn check(&mut self, packet: &[u8]) -> Result<(Header, bool), Error> {
        let h = Header::parse(packet)?;
        if h.offset == 0 {
            if self
                .last_id
                .is_some_and(|last| (h.id.wrapping_sub(last) as i32) <= 0)
            {
                return Err(Error::Sequence);
            }
            self.active = Some(h);
            self.offset = 0;
            self.crc = !0;
            self.last_id = Some(h.id);
        }
        let a = self.active.ok_or(Error::Sequence)?;
        if a.id != h.id
            || a.length != h.length
            || a.crc != h.crc
            || a.capture_us != h.capture_us
            || self.offset != h.offset
        {
            return Err(Error::Sequence);
        }
        self.crc = crc_update(self.crc, &packet[HEADER..]);
        self.offset += h.count as u32;
        let done = h.flags & 2 != 0;
        if done {
            if !self.crc != h.crc {
                return Err(Error::Integrity);
            }
            self.active = None;
        }
        Ok((h, done))
    }
}
pub fn feedback(
    status: u8,
    buttons: u16,
    id: u32,
    credits: u32,
    received: u32,
    dropped: u32,
    capture: u64,
) -> [u8; 32] {
    let mut b = [0u8; 32];
    b[..4].copy_from_slice(b"MSF1");
    b[4] = 1;
    b[5] = status;
    b[6..8].copy_from_slice(&buttons.to_be_bytes());
    b[8..12].copy_from_slice(&id.to_be_bytes());
    b[12..16].copy_from_slice(&credits.to_be_bytes());
    b[16..20].copy_from_slice(&received.to_be_bytes());
    b[20..24].copy_from_slice(&dropped.to_be_bytes());
    b[24..32].copy_from_slice(&capture.to_be_bytes());
    b
}

#[cfg(test)]
mod tests {
    use super::*;
    fn packet(id: u32, offset: u32, data: &[u8], all: &[u8]) -> Vec<u8> {
        let mut p = vec![0; 40];
        p[..4].copy_from_slice(b"MSV1");
        p[4] = 1;
        p[5] = 1;
        let flags = (if offset == 0 { 1u16 } else { 0 })
            | (if offset as usize + data.len() == all.len() {
                2
            } else {
                0
            });
        p[6..8].copy_from_slice(&flags.to_be_bytes());
        p[8..12].copy_from_slice(&id.to_be_bytes());
        p[12..14].copy_from_slice(&720u16.to_be_bytes());
        p[14..16].copy_from_slice(&480u16.to_be_bytes());
        p[16..20].copy_from_slice(&(all.len() as u32).to_be_bytes());
        p[20..24].copy_from_slice(&offset.to_be_bytes());
        p[24..26].copy_from_slice(&(data.len() as u16).to_be_bytes());
        p[28..32].copy_from_slice(&(!crc_update(!0, all)).to_be_bytes());
        p.extend(data);
        p
    }
    #[test]
    fn ieee_crc_vector() {
        assert_eq!(!crc_update(!0, b"123456789"), 0xcbf43926);
    }
    #[test]
    fn sequential_no_frame_allocation() {
        let mut r = Receiver::default();
        let all = vec![42; 2048];
        assert!(!r.accept(&packet(1, 0, &all[..1024], &all)).unwrap().1);
        assert!(r.accept(&packet(1, 1024, &all[1024..], &all)).unwrap().1);
        assert!(std::mem::size_of::<Receiver>() < 128);
    }
    #[test]
    fn loss_aborts_and_next_frame_recovers() {
        let mut r = Receiver::default();
        let a = vec![1; 2050];
        r.accept(&packet(1, 0, &a[..1024], &a)).unwrap();
        assert_eq!(
            r.accept(&packet(1, 2048, &a[2048..], &a)),
            Err(Error::Sequence)
        );
        assert!(r.accept(&packet(2, 0, b"ok", b"ok")).unwrap().1);
    }
    #[test]
    fn corrupt_final_never_commits() {
        let mut r = Receiver::default();
        let mut p = packet(1, 0, b"ok", b"ok");
        p[40] ^= 1;
        assert_eq!(r.accept(&p), Err(Error::Integrity));
        assert!(r.accept(&packet(2, 0, b"ok", b"ok")).unwrap().1);
    }
    #[test]
    fn duplicate_and_reorder_rejected() {
        let mut r = Receiver::default();
        let a = vec![1; 2048];
        let p = packet(1, 0, &a[..1024], &a);
        r.accept(&p).unwrap();
        assert_eq!(r.accept(&p), Err(Error::Sequence));
        assert_eq!(
            r.accept(&packet(1, 1024, &a[1024..], &a)),
            Err(Error::Sequence)
        );
    }
    #[test]
    fn truncated_unknown_and_oversize_rejected() {
        for n in 0..40 {
            assert_eq!(Header::parse(&vec![0; n]), Err(Error::Header));
        }
        let mut p = packet(1, 0, b"ok", b"ok");
        p[5] = 2;
        assert_eq!(Header::parse(&p), Err(Error::Format));
        p[5] = 1;
        p[16..20].copy_from_slice(&(MAX_FRAME + 1).to_be_bytes());
        assert_eq!(Header::parse(&p), Err(Error::Bounds));
    }
    #[test]
    fn conflicting_metadata_rejected() {
        let mut r = Receiver::default();
        let a = vec![1; 2048];
        r.accept(&packet(1, 0, &a[..1024], &a)).unwrap();
        let mut p = packet(1, 1024, &a[1024..], &a);
        p[32] = 1;
        assert_eq!(r.accept(&p), Err(Error::Sequence));
    }
    #[test]
    fn stale_frame_and_wrap() {
        let mut r = Receiver::default();
        r.accept(&packet(u32::MAX, 0, b"ok", b"ok")).unwrap();
        assert!(r.accept(&packet(0, 0, b"ok", b"ok")).unwrap().1);
        assert_eq!(
            r.accept(&packet(u32::MAX, 0, b"ok", b"ok")),
            Err(Error::Sequence)
        );
    }
    #[test]
    fn feedback_layout() {
        let b = feedback(1, 0x800, 2, 3, 4, 5, 6);
        assert_eq!(&b[..8], b"MSF1\x01\x01\x08\x00");
        assert_eq!(u64::from_be_bytes(b[24..32].try_into().unwrap()), 6);
    }
}
