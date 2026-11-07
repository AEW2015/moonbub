//! Bounded MSV1 receiver state. No frame allocation and no ESP-IDF dependency.
pub const HEADER: usize = 40;
pub const CHUNK: usize = 1024;
pub const MAX_FRAME: u32 = 256 * 1024;
/// Parsing recognizes both profiles; the caller must check FPGA capabilities
/// before accepting 720p and before forwarding any payload.
pub fn supported_dimensions(width: u16, height: u16) -> bool {
    (width, height) == (720, 480) || (width, height) == (1280, 720)
}
pub fn fpga_supports_dimensions(width: u16, height: u16, caps: u32) -> bool {
    caps & 1 != 0 && ((width, height) == (720, 480)
        || ((width, height) == (1280, 720) && caps & 0x10 != 0))
}

/// A replacement UDP socket from the configured host may take over only when
/// the prior sender has been silent and no frame is being assembled.
pub fn can_rebind_peer(frame_active: bool, silence_ms: u64) -> bool {
    !frame_active && silence_ms >= 500
}
pub fn generation_is_current(expected: u32, current: u32) -> bool { expected == current }

/// Frame identity advertised in heartbeat feedback. It advances only after
/// the caller has accepted the entire frame and submitted its FPGA commit.
#[derive(Default, Clone, Copy, Debug, PartialEq, Eq)]
pub struct CompletedFrame {
    pub id: u32,
    pub capture_us: u64,
    pub valid: bool,
}
impl CompletedFrame {
    pub fn commit(&mut self, header: Header) {
        self.id = header.id;
        self.capture_us = header.capture_us;
        self.valid = true;
    }
    /// The zero-valued ID and capture timestamp are legal protocol values;
    /// silence, not a success heartbeat, is required before first completion.
    pub fn success_identity(&self) -> Option<(u32, u64)> {
        self.valid.then_some((self.id, self.capture_us))
    }
}

/// Termination must never emit a success status: partial input is dropped;
/// after a completed frame, status 3 indicates session shutdown while clearing
/// held buttons, not a retroactive change to the prior completion result.
pub fn shutdown_feedback(completed: &CompletedFrame, active: Option<(u32, u64)>) -> Option<(u8, u32, u64)> {
    if let Some((id, capture)) = active { Some((1, id, capture)) }
    else { completed.success_identity().map(|(id, capture)| (3, id, capture)) }
}

/// Use a valid offending header; if none exists, only an actual in-flight
/// frame can identify the failure. Never attribute malformed input to the last
/// successfully completed frame.
pub fn failure_identity(header: Option<Header>, inflight: Option<(u32, u64)>) -> Option<(u32, u64)> {
    header.map(|h| (h.id, h.capture_us)).or(inflight)
}

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
            || !supported_dimensions(h.width, h.height)
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
const fn build_crc32_table() -> [u32; 256] {
    let mut table = [0u32; 256];
    let mut i = 0;
    while i < 256 {
        let mut value = i as u32;
        let mut bit = 0;
        while bit < 8 {
            value = (value >> 1) ^ (0xEDB88320u32 & 0u32.wrapping_sub(value & 1));
            bit += 1;
        }
        table[i] = value;
        i += 1;
    }
    table
}
const CRC32_TABLE: [u32; 256] = build_crc32_table();

/// Same reflected IEEE CRC32 state as the bitwise reference; caller owns the
/// initial/final xor so arbitrary packet splits remain equivalent.
pub fn crc_update(mut crc: u32, data: &[u8]) -> u32 {
    for byte in data {
        crc = (crc >> 8) ^ CRC32_TABLE[((crc as u8) ^ *byte) as usize];
    }
    crc
}

/// Retained for differential tests and an explicitly requested idle benchmark.
pub fn crc_update_bitwise(mut crc: u32, data: &[u8]) -> u32 {
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
    /// Read-only pre-accept assembly identity. Header is the accepted SOF;
    /// expected offset is the next byte, not the incoming datagram's offset.
    pub fn active_identity(&self) -> Option<(Header, u32)> {
        self.active.map(|header| (header, self.offset))
    }
    /// Diagnostic-only sequence comparison for an already parsed header.
    /// Mirrors check() without changing acceptance, CRC or assembly state.
    /// Bits: ID,width,height,length,CRC,capture,offset,no-active,stale-SOF.
    pub fn sequence_mismatch(&self, h: Header) -> u16 {
        if h.offset == 0 {
            return if self.last_id.is_some_and(|last|
                (h.id.wrapping_sub(last) as i32) <= 0) { 1 << 8 } else { 0 };
        }
        let Some(a) = self.active else { return 1 << 7; };
        u16::from(a.id != h.id)
            | (u16::from(a.width != h.width) << 1)
            | (u16::from(a.height != h.height) << 2)
            | (u16::from(a.length != h.length) << 3)
            | (u16::from(a.crc != h.crc) << 4)
            | (u16::from(a.capture_us != h.capture_us) << 5)
            | (u16::from(self.offset != h.offset) << 6)
    }
    pub fn expected_offset(&self) -> Option<u32> {
        self.active.map(|_| self.offset)
    }
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
            || a.width != h.width
            || a.height != h.height
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
    #[test]
    fn frame_dimensions_cannot_change_between_valid_crc_chunks() {
        let frame = vec![42; 2048];
        for (initial, changed) in [((720u16, 480u16), (1280u16, 720u16)),
                                  ((1280u16, 720u16), (720u16, 480u16))] {
            let mut first = packet(71, 0, &frame[..1024], &frame);
            first[12..14].copy_from_slice(&initial.0.to_be_bytes());
            first[14..16].copy_from_slice(&initial.1.to_be_bytes());
            let mut next = packet(71, 1024, &frame[1024..], &frame);
            next[12..14].copy_from_slice(&changed.0.to_be_bytes());
            next[14..16].copy_from_slice(&changed.1.to_be_bytes());
            // Both headers are independently supported and the payload CRC is
            // unchanged: rejection must come from frame metadata continuity.
            Header::parse(&first).unwrap();
            Header::parse(&next).unwrap();
            let mut receiver = Receiver::default();
            assert!(!receiver.accept(&first).unwrap().1);
            assert_eq!(receiver.accept(&next), Err(Error::Sequence));
            assert_eq!(receiver.expected_offset(), None);
            assert!(receiver.accept(&packet(72, 0, b"recovered", b"recovered")).unwrap().1);
        }
    }
    #[test]
    fn stable_dimensions_complete_for_both_supported_profiles() {
        let frame = vec![42; 2048];
        for dimensions in [(720u16, 480u16), (1280u16, 720u16)] {
            let mut receiver = Receiver::default();
            for offset in [0, 1024] {
                let mut p = packet(71, offset as u32, &frame[offset..offset+1024], &frame);
                p[12..14].copy_from_slice(&dimensions.0.to_be_bytes());
                p[14..16].copy_from_slice(&dimensions.1.to_be_bytes());
                let (header, done) = receiver.accept(&p).unwrap();
                assert_eq!((header.width, header.height), dimensions);
                assert_eq!(done, offset == 1024);
            }
        }
    }

    #[test]
    fn only_known_resolutions_are_recognized() {
        assert!(supported_dimensions(720, 480));
        assert!(supported_dimensions(1280, 720));
        assert!(!supported_dimensions(1920, 1080));
        assert!(!supported_dimensions(720, 720));
        assert!(fpga_supports_dimensions(720, 480, 3));
        assert!(!fpga_supports_dimensions(1280, 720, 15));
        assert!(fpga_supports_dimensions(1280, 720, 0x11));
        assert!(!fpga_supports_dimensions(1920, 1080, u32::MAX));
        let mut p = packet(1, 0, &[42], &[42]);
        p[12..14].copy_from_slice(&1280u16.to_be_bytes());
        p[14..16].copy_from_slice(&720u16.to_be_bytes());
        assert_eq!((Header::parse(&p).unwrap().width, Header::parse(&p).unwrap().height), (1280, 720));
    }
    #[test]
    fn peer_rebind_requires_idle_session() {
        assert!(!can_rebind_peer(false, 499));
        assert!(!can_rebind_peer(true, 500));
        assert!(can_rebind_peer(false, 500));
    }
    #[test]
    fn heartbeat_identity_advances_only_after_complete_frame() {
        let mut receiver = Receiver::default();
        let mut completed = CompletedFrame::default();
        let frame = vec![42; 2048];
        let (first, done) = receiver.accept(&packet(8, 0, &frame[..1024], &frame)).unwrap();
        assert!(!done);
        assert_eq!((completed.id, completed.capture_us), (0, 0));
        assert_eq!(completed.success_identity(), None);
        let (last, done) = receiver.accept(&packet(8, 1024, &frame[1024..], &frame)).unwrap();
        assert!(done);
        completed.commit(last);
        assert_eq!((completed.id, completed.capture_us), (first.id, first.capture_us));
        assert_eq!(completed.success_identity(), Some((first.id, first.capture_us)));
        receiver.accept(&packet(9, 0, &frame[..1024], &frame)).unwrap();
        assert_eq!(completed.id, 8);
        receiver.abort();
        assert_eq!(completed.id, 8);
    }
    #[test]
    fn cancellation_never_acknowledges_partial_even_with_zero_identity() {
        let mut receiver=Receiver::default(); let mut completed=CompletedFrame::default();
        let frame=vec![1;2048];
        let (first,done)=receiver.accept(&packet(0,0,&frame[..1024],&frame)).unwrap();
        assert!(!done); assert_eq!((first.id,first.capture_us),(0,0));
        assert_eq!(completed.success_identity(),None);
        assert_eq!(shutdown_feedback(&completed,Some((first.id,first.capture_us))),Some((1,0,0)));
        assert_eq!(shutdown_feedback(&completed,None),None);
        let (last,done)=receiver.accept(&packet(0,1024,&frame[1024..],&frame)).unwrap();
        assert!(done);completed.commit(last);
        assert_eq!(shutdown_feedback(&completed,None),Some((3,0,0)));
        assert_eq!(shutdown_feedback(&completed,Some((1,2))),Some((1,1,2)));
        assert!(generation_is_current(10,10));
        assert!(!generation_is_current(10,11));
    }
    #[test]
    fn failure_feedback_identifies_offending_frame_not_previous_success() {
        let bad=Header::parse(&packet(44,0,b"x",b"x")).unwrap();
        assert_eq!(failure_identity(Some(bad),Some((12,99))),Some((44,0)));
        assert_eq!(failure_identity(None,Some((12,99))),Some((12,99)));
        assert_eq!(failure_identity(None,None),None);
    }
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
    fn table_crc_matches_bitwise_across_seeds_lengths_and_chunks() {
        let mut state = 0x1234_5678u32;
        let mut bytes = vec![0u8; 262144];
        for b in &mut bytes { state = state.wrapping_mul(1664525).wrapping_add(1013904223); *b = (state >> 24) as u8; }
        for len in [0, 1, 7, 255, 256, 1024, 65536, 262144] {
            for seed in [0, 1, !0, 0x1234_5678] {
                let expected = crc_update_bitwise(seed, &bytes[..len]);
                assert_eq!(crc_update(seed, &bytes[..len]), expected);
                let mut split = seed;
                for chunk in bytes[..len].chunks(997) { split = crc_update(split, chunk); }
                assert_eq!(split, expected);
            }
        }
    }
    #[test]
    fn sequential_no_frame_allocation() {
        let mut r = Receiver::default();
        let all = vec![42; 2048];
        assert_eq!(r.expected_offset(), None);
        assert!(!r.accept(&packet(1, 0, &all[..1024], &all)).unwrap().1);
        assert_eq!(r.expected_offset(), Some(1024));
        assert!(r.accept(&packet(1, 1024, &all[1024..], &all)).unwrap().1);
        assert_eq!(r.expected_offset(), None);
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
