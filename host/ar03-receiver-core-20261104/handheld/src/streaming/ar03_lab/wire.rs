//! Pinned epoch-1 laboratory bytes. Parsing does not grant forwarding permission.
pub const EPOCH: u32 = 1;
pub const FRAME_CAP: u32 = 49_152;
pub const CHUNK: u32 = 1008;
pub const NO_SLOT: u16 = u16::MAX;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Length,
    Magic,
    Crc,
    Fields,
    Epoch,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Kind {
    Request = 1,
    Cancel = 2,
    Grant = 3,
    Busy = 4,
    Release = 5,
    Canceled = 6,
    Finish = 7,
    Finished = 8,
}
impl Kind {
    fn parse(v: u8) -> Result<Self, Error> {
        Ok(match v {
            1 => Self::Request,
            2 => Self::Cancel,
            3 => Self::Grant,
            4 => Self::Busy,
            5 => Self::Release,
            6 => Self::Canceled,
            7 => Self::Finish,
            8 => Self::Finished,
            _ => return Err(Error::Fields),
        })
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Frame {
    pub epoch: u32,
    pub frame: u32,
    pub total: u32,
    pub body_crc: u32,
    pub nonce: u64,
    pub slot: u16,
    pub kind: Kind,
}
impl Frame {
    pub fn same_identity(&self, other: &Self) -> bool {
        self.epoch == other.epoch
            && self.frame == other.frame
            && self.total == other.total
            && self.body_crc == other.body_crc
            && self.nonce == other.nonce
    }
    pub fn exact_owner(&self, other: &Self) -> bool {
        self.same_identity(other) && self.slot == other.slot
    }
    pub fn reply(self, kind: Kind, slot: u16) -> Self {
        Self { kind, slot, ..self }
    }
    pub fn basic_valid(&self) -> bool {
        self.epoch == EPOCH
            && self.nonce != 0
            && self.total > 0
            && self.total <= FRAME_CAP
            && matches!(self.slot, 0 | 1 | NO_SLOT)
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Data {
    pub epoch: u32,
    pub frame: u32,
    pub total: u32,
    pub complete_crc: u32,
    pub body_crc: u32,
    pub token_header_crc: u32,
    pub sequence: u64,
    pub packet_slot: u16,
    pub index: u16,
    pub count: u16,
    pub payload_bytes: u16,
}
impl Data {
    pub fn valid(&self) -> bool {
        if self.epoch != EPOCH
            || self.frame == u32::MAX
            || self.sequence == 0
            || self.packet_slot >= 6
            || self.total == 0
            || self.total > FRAME_CAP
            || self.count as u32 != (self.total + CHUNK - 1) / CHUNK
            || self.index >= self.count
        {
            return false;
        }
        self.payload_bytes as u32 == (self.total - self.index as u32 * CHUNK).min(CHUNK)
    }
    pub fn matches(&self, f: &Frame) -> bool {
        f.kind == Kind::Grant
            && f.slot < 2
            && self.epoch == f.epoch
            && self.frame == f.frame
            && self.total == f.total
            && self.body_crc == f.body_crc
    }
    pub fn query(self) -> Query {
        Query {
            epoch: self.epoch,
            slot: self.packet_slot,
            sequence: self.sequence,
            header_crc: self.token_header_crc,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Query {
    pub epoch: u32,
    pub slot: u16,
    pub sequence: u64,
    pub header_crc: u32,
}
impl Query {
    pub fn valid(&self) -> bool {
        self.epoch == EPOCH && self.slot < 6 && self.sequence != 0
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Status {
    Consumed = 0,
    Rejected = 1,
    Unknown = 2,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Receipt {
    pub key: Query,
    pub status: Status,
    pub queried: bool,
}
impl Receipt {
    pub fn returns_packet_permit(&self) -> bool {
        matches!(self.status, Status::Consumed | Status::Rejected)
    }
}
fn u16be(p: &[u8], o: usize) -> u16 {
    u16::from_be_bytes([p[o], p[o + 1]])
}
fn u32be(p: &[u8], o: usize) -> u32 {
    u32::from_be_bytes([p[o], p[o + 1], p[o + 2], p[o + 3]])
}
fn u64be(p: &[u8], o: usize) -> u64 {
    u64::from_be_bytes(p[o..o + 8].try_into().unwrap())
}
pub fn crc(p: &[u8]) -> u32 {
    let mut c = u32::MAX;
    for &v in p {
        c ^= v as u32;
        for _ in 0..8 {
            c = (c >> 1) ^ (0xedb88320u32.wrapping_mul(c & 1));
        }
    }
    !c
}
pub fn parse_frame(p: &[u8]) -> Result<Frame, Error> {
    if p.len() != 36 {
        return Err(Error::Length);
    }
    if &p[..4] != b"FG19" || p[4] != 1 {
        return Err(Error::Magic);
    }
    if crc(&p[..32]) != u32be(p, 32) {
        return Err(Error::Crc);
    }
    let f = Frame {
        kind: Kind::parse(p[5])?,
        slot: u16be(p, 6),
        epoch: u32be(p, 8),
        frame: u32be(p, 12),
        nonce: u64be(p, 16),
        total: u32be(p, 24),
        body_crc: u32be(p, 28),
    };
    if !f.basic_valid() {
        return Err(Error::Fields);
    }
    if (f.kind == Kind::Busy && f.slot != NO_SLOT)
        || (matches!(
            f.kind,
            Kind::Request | Kind::Grant | Kind::Release | Kind::Finished
        ) && f.slot == NO_SLOT)
    {
        return Err(Error::Fields);
    }
    Ok(f)
}
pub fn write_frame(f: Frame, out: &mut [u8]) -> Result<usize, Error> {
    if out.len() < 36 {
        return Err(Error::Length);
    }
    let mut p = [0u8; 36];
    p[..4].copy_from_slice(b"FG19");
    p[4] = 1;
    p[5] = f.kind as u8;
    p[6..8].copy_from_slice(&f.slot.to_be_bytes());
    p[8..12].copy_from_slice(&f.epoch.to_be_bytes());
    p[12..16].copy_from_slice(&f.frame.to_be_bytes());
    p[16..24].copy_from_slice(&f.nonce.to_be_bytes());
    p[24..28].copy_from_slice(&f.total.to_be_bytes());
    p[28..32].copy_from_slice(&f.body_crc.to_be_bytes());
    let checksum = crc(&p[..32]);
    p[32..].copy_from_slice(&checksum.to_be_bytes());
    parse_frame(&p)?;
    out[..36].copy_from_slice(&p);
    Ok(36)
}
pub fn parse_data(p: &[u8]) -> Result<Data, Error> {
    if !(47..=1055).contains(&p.len()) {
        return Err(Error::Length);
    }
    if &p[16..20] != b"GF03" || p[20] != 3 {
        return Err(Error::Magic);
    }
    let epoch = u32be(p, 0);
    if epoch != EPOCH || u32be(p, 21) != epoch || u16be(p, 6) != 0 {
        return Err(Error::Epoch);
    }
    let d = Data {
        epoch,
        packet_slot: u16be(p, 4),
        sequence: u64be(p, 8),
        frame: u32be(p, 25),
        total: u32be(p, 29),
        index: u16be(p, 33),
        count: u16be(p, 35),
        payload_bytes: u16be(p, 37),
        complete_crc: u32be(p, 39),
        body_crc: u32be(p, 43),
        token_header_crc: crc(&p[..47]),
    };
    if !d.valid() || p.len() != 47 + d.payload_bytes as usize {
        return Err(Error::Fields);
    }
    Ok(d)
}
pub fn parse_query(p: &[u8]) -> Result<Query, Error> {
    if p.len() != 28 {
        return Err(Error::Length);
    }
    if &p[..4] != b"QC18" {
        return Err(Error::Magic);
    }
    if crc(&p[..24]) != u32be(p, 24) {
        return Err(Error::Crc);
    }
    let q = Query {
        epoch: u32be(p, 4),
        slot: u16be(p, 8),
        sequence: u64be(p, 12),
        header_crc: u32be(p, 20),
    };
    if !q.valid() || u16be(p, 10) != 0 {
        return Err(Error::Fields);
    }
    Ok(q)
}
pub fn write_receipt(r: Receipt, out: &mut [u8]) -> Result<usize, Error> {
    if out.len() < 29 || !r.key.valid() {
        return Err(Error::Fields);
    }
    let mut p = [0u8; 29];
    p[..4].copy_from_slice(b"PC18");
    p[4..8].copy_from_slice(&r.key.epoch.to_be_bytes());
    p[8..10].copy_from_slice(&r.key.slot.to_be_bytes());
    p[10..12].copy_from_slice(&(r.queried as u16).to_be_bytes());
    p[12..20].copy_from_slice(&r.key.sequence.to_be_bytes());
    p[20] = r.status as u8;
    p[21..25].copy_from_slice(&r.key.header_crc.to_be_bytes());
    let checksum = crc(&p[..25]);
    p[25..].copy_from_slice(&checksum.to_be_bytes());
    out[..29].copy_from_slice(&p);
    Ok(29)
}
