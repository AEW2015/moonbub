//! Fixed metadata leases. A backend must own bounded copied/pinned bytes, not RX borrows.
use super::{
    frame::{Control, Frames},
    wire::{self, Data, Frame, Kind, Query, Receipt, Status},
};
pub const DATA_POSITIONS: usize = 5;
pub const MAILBOX_POSITIONS: usize = 6;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Identity {
    pub owner: Frame,
    pub route: Data,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BufferLease {
    pub id: u64,
    pub datagram_bytes: u16,
    pub fifo_bytes: u16,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reservation {
    Owned(BufferLease),
    Unavailable,
    Unknown,
}
/// No firmware implementation exists. Owned may be returned only after copying
/// or pinning the entire ephemeral datagram into backend-owned bounded storage
/// and reserving real FIFO space for its GF03 header+payload. A borrow/raw pointer
/// into the caller's reusable RX array is not an owned asynchronous DMA lease.
pub trait Backend {
    // Unavailable guarantees no ownership was acquired. The caller must retain
    // its RX bytes for a bounded retry or stop; it must not claim acceptance and
    // recycle the borrowed buffer. Unknown means possible ownership and pins it.
    fn reserve(&mut self, identity: Identity, datagram: &[u8], fifo_bytes: u16) -> Reservation;
    /// Called only for a fully identity-matched completion. true means the exact
    /// buffer lease is released; false is ambiguous and forces retained safe stop.
    fn release(&mut self, identity: Identity, lease: BufferLease) -> bool;
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AdmissionError {
    Wire(wire::Error),
    Stopped,
    NoOwner,
    ReservedControlPosition,
    Busy,
    Stale,
    Duplicate,
    RouteConflict,
    NoCapacity,
    Ambiguous,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Completion {
    Consumed,
    Rejected,
    Unknown,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Completed {
    Receipt(Receipt),
    Duplicate,
    Stale,
    SafeStop,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Pending {
    identity: Identity,
    buffer: Option<BufferLease>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Cached {
    identity: Identity,
    receipt: Receipt,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QueryResult {
    Receipt(Receipt),
    Pending,
    Unknown,
}
impl QueryResult {
    /// Frozen QC18 always receives a queried PC18. Pending/unknown uses status2,
    /// which does not return a DATA permit or release the still-owned buffer.
    pub fn wire_reply(self, query: Query) -> Receipt {
        match self {
            Self::Receipt(receipt) => receipt,
            Self::Pending | Self::Unknown => Receipt {
                key: query,
                status: Status::Unknown,
                queried: true,
            },
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ControlIdentity {
    Frame(Frame),
    Query(Query),
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ControlDone {
    ReplyEnqueued,
    NoReplyConsumed,
    Unknown,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct ControlLease {
    identity: ControlIdentity,
    reply_required: bool,
}
#[derive(Debug, PartialEq, Eq)]
pub struct Gateway {
    frames: Frames,
    pending: [Option<Pending>; DATA_POSITIONS],
    cached: [Option<Cached>; DATA_POSITIONS],
    last_sequence: [u64; DATA_POSITIONS],
    complete_crc: [Option<u32>; 2],
    control: Option<ControlLease>,
}
impl Gateway {
    /// Fresh offline epoch1 laboratory construction only. This is not reset/rekey,
    /// reconnect or permission to expose a live endpoint. No production enable exists.
    pub const fn cold_epoch1(finish_ack: bool) -> Self {
        Self {
            frames: Frames::cold_epoch1(finish_ack),
            pending: [None; DATA_POSITIONS],
            cached: [None; DATA_POSITIONS],
            last_sequence: [0; DATA_POSITIONS],
            complete_crc: [None; 2],
            control: None,
        }
    }
    pub fn stopped(&self) -> bool {
        self.frames.stopped()
    }
    pub fn safe_stop(&mut self) {
        self.frames.safe_stop()
    }
    pub fn frame_count(&self) -> usize {
        self.frames.count()
    }
    pub fn packet_count(&self) -> usize {
        self.pending.iter().filter(|p| p.is_some()).count()
    }
    pub fn mailbox_count(&self) -> usize {
        self.packet_count() + usize::from(self.control.is_some())
    }
    pub fn owner(&self, slot: u16) -> Option<super::frame::Owner> {
        self.frames.owner(slot)
    }
    pub fn frame_control(&mut self, f: Frame) -> Result<Control, AdmissionError> {
        if self.stopped() {
            return Err(AdmissionError::Stopped);
        }
        if !f.basic_valid() || !matches!(f.kind, Kind::Request | Kind::Cancel | Kind::Finish) {
            return Err(AdmissionError::Wire(wire::Error::Fields));
        }
        if self.control.is_some() {
            return Err(AdmissionError::Busy);
        }
        let old = self.frames.owner(f.slot);
        let reply = self.frames.control(f);
        // Reuse may clear a previous frame's gateway-only complete-CRC anchor.
        if let Control::Reply(r) = reply {
            if r.kind == Kind::Grant && r.slot == f.slot && old.is_none() {
                self.complete_crc[r.slot as usize] = None;
            }
            if r.kind == Kind::Canceled {
                self.complete_crc[r.slot as usize] = None;
            }
        }
        self.control = Some(ControlLease {
            identity: ControlIdentity::Frame(f),
            reply_required: matches!(reply, Control::Reply(_)),
        });
        Ok(reply)
    }
    pub fn complete_control(&mut self, identity: ControlIdentity, done: ControlDone) -> bool {
        if self.stopped() {
            return false;
        }
        let Some(lease) = self.control else {
            return false;
        };
        if lease.identity != identity {
            return false;
        }
        if done == ControlDone::Unknown {
            self.safe_stop();
            return false;
        }
        if lease.reply_required && done != ControlDone::ReplyEnqueued {
            return false;
        }
        self.control = None;
        true
    }
    pub fn admit(
        &mut self,
        datagram: &[u8],
        backend: &mut impl Backend,
    ) -> Result<Identity, AdmissionError> {
        if self.stopped() {
            return Err(AdmissionError::Stopped);
        }
        let route = wire::parse_data(datagram).map_err(AdmissionError::Wire)?;
        // Frozen five-token profile uses data slots0..4; position5 is reserved control.
        if route.packet_slot as usize >= DATA_POSITIONS {
            return Err(AdmissionError::ReservedControlPosition);
        }
        let owner = self.frames.lookup(&route).ok_or(AdmissionError::NoOwner)?;
        let slot = route.packet_slot as usize;
        let identity = Identity {
            owner: owner.grant,
            route,
        };
        if let Some(p) = self.pending[slot] {
            return Err(if p.identity == identity {
                AdmissionError::Duplicate
            } else {
                AdmissionError::Busy
            });
        }
        if let Some(c) = self.cached[slot] {
            if c.identity == identity {
                return Err(AdmissionError::Duplicate);
            }
        }
        if route.sequence <= self.last_sequence[slot] {
            return Err(AdmissionError::Stale);
        }
        if owner.observed & (1u64 << route.index) != 0 {
            return Err(AdmissionError::Duplicate);
        }
        if self.complete_crc[owner.grant.slot as usize].is_some_and(|crc| crc != route.complete_crc)
        {
            return Err(AdmissionError::RouteConflict);
        }
        let fifo = 31 + route.payload_bytes;
        let reservation = backend.reserve(identity, datagram, fifo);
        let buffer = match reservation {
            Reservation::Unavailable => return Err(AdmissionError::NoCapacity),
            Reservation::Unknown => None,
            Reservation::Owned(b) => Some(b),
        };
        self.pending[slot] = Some(Pending { identity, buffer });
        self.last_sequence[slot] = route.sequence;
        self.complete_crc[owner.grant.slot as usize] = Some(route.complete_crc);
        // Observation pins frame cancellation before any asynchronous transfer ends.
        let observed = self.frames.observe(route);
        let valid = buffer.is_some_and(|b| {
            b.datagram_bytes as usize >= datagram.len()
                && b.fifo_bytes >= fifo
                && self.pending.iter().enumerate().all(|(i, p)| {
                    i == slot || !p.is_some_and(|p| p.buffer.is_some_and(|old| old.id == b.id))
                })
        });
        if !observed || !valid {
            self.safe_stop();
            return Err(AdmissionError::Ambiguous);
        }
        Ok(identity)
    }
    pub fn complete(
        &mut self,
        identity: Identity,
        buffer_id: u64,
        result: Completion,
        backend: &mut impl Backend,
    ) -> Completed {
        if self.stopped() {
            return Completed::SafeStop;
        }
        let slot = identity.route.packet_slot as usize;
        if slot >= DATA_POSITIONS {
            return Completed::Stale;
        }
        let Some(p) = self.pending[slot] else {
            return if self.cached[slot].is_some_and(|c| c.identity == identity) {
                Completed::Duplicate
            } else {
                Completed::Stale
            };
        };
        if p.identity != identity || !p.buffer.is_some_and(|b| b.id == buffer_id) {
            return Completed::Stale;
        }
        if result == Completion::Unknown {
            self.safe_stop();
            return Completed::SafeStop;
        }
        let lease = p.buffer.unwrap();
        if !backend.release(identity, lease) {
            self.safe_stop();
            return Completed::SafeStop;
        }
        let receipt = Receipt {
            key: identity.route.query(),
            status: if result == Completion::Consumed {
                Status::Consumed
            } else {
                Status::Rejected
            },
            queried: false,
        };
        self.pending[slot] = None;
        self.cached[slot] = Some(Cached { identity, receipt });
        Completed::Receipt(receipt)
    }
    pub fn query(&self, q: Query) -> QueryResult {
        if self.stopped() || !q.valid() {
            return QueryResult::Unknown;
        }
        let slot = q.slot as usize;
        if slot >= DATA_POSITIONS {
            return QueryResult::Unknown;
        }
        if self.pending[slot].is_some_and(|p| p.identity.route.query() == q) {
            return QueryResult::Pending;
        }
        if let Some(c) = self.cached[slot] {
            if c.receipt.key == q {
                return QueryResult::Receipt(Receipt {
                    queried: true,
                    ..c.receipt
                });
            }
        }
        QueryResult::Unknown
    }
    pub fn query_control(&mut self, q: Query) -> Result<QueryResult, AdmissionError> {
        if self.stopped() {
            return Err(AdmissionError::Stopped);
        }
        if !q.valid() {
            return Err(AdmissionError::Wire(wire::Error::Fields));
        }
        if self.control.is_some() {
            return Err(AdmissionError::Busy);
        }
        let reply = self.query(q);
        self.control = Some(ControlLease {
            identity: ControlIdentity::Query(q),
            reply_required: true,
        });
        Ok(reply)
    }
    pub fn physical_drain(&mut self, f: Frame) -> bool {
        if self
            .pending
            .iter()
            .flatten()
            .any(|p| p.identity.owner.exact_owner(&f))
        {
            return false;
        }
        self.frames.physical_drain(f)
    }
    pub fn take_release(&mut self, f: Frame) -> Option<Frame> {
        if self.control.is_some()
            || self
                .pending
                .iter()
                .flatten()
                .any(|p| p.identity.owner.exact_owner(&f))
        {
            return None;
        }
        let reply = self.frames.take_release(f)?;
        self.complete_crc[f.slot as usize] = None;
        Some(reply)
    }
}
