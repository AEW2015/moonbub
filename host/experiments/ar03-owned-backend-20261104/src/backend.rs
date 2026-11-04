//! Dormant software storage prerequisite, not an implemented FPGA/ESP-IDF driver.
//! Capacity and completion must come from real hardware in a future adapter.
use crate::ar03_lab::{packet::*, wire};

pub const MAX_DATAGRAM: usize = 1055;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Capacity {
    Granted(u64),
    Unavailable,
    Unknown,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Proof {
    pub identity: Identity,
    pub lease: BufferLease,
    pub ticket: u64,
    pub result: Completion,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Poll {
    Pending,
    Done(Proof),
    Unknown,
}

/// Private adapter contract only. No CSR, QSPI command or wire packet is assigned.
pub trait Fifo {
    /// Granted means actual FIFO capacity is reserved for this exact transaction.
    /// This method receives NO pointer to pool memory. It must not invent credit
    /// from free software slots. Unavailable guarantees no acquired ownership.
    fn reserve_capacity(&mut self, identity: Identity, lease: BufferLease) -> Capacity;
    /// Done must prove the real consumer has stopped reading the packet. An SPI
    /// submit return, JPEG credit count or diagnostic snapshot is not this proof.
    fn poll(&mut self, identity: Identity, lease: BufferLease, ticket: u64) -> Poll;
    /// true proves the exact completed reservation has been retired. Unknown
    /// retirement must return false; the caller then retains its bytes and stops.
    fn retire(&mut self, proof: Proof) -> bool;
}

struct Record {
    identity: Identity,
    lease: BufferLease,
    ticket: Option<u64>,
    completed: Option<Proof>,
    polls: u32,
}
struct Slot {
    record: Option<Record>,
    bytes: [u8; MAX_DATAGRAM],
}
impl Slot {
    const fn empty() -> Self {
        Self { record: None, bytes: [0; MAX_DATAGRAM] }
    }
}

/// Neither Copy nor Clone. No reset/rekey/force-free API exists.
pub struct OwnedBackend<T: Fifo> {
    slots: [Slot; DATA_POSITIONS],
    next_id: u64,
    stopped: bool,
    poll_budget: u32,
    transport: T,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Progress {
    Pending,
    Stale,
    Completed(Completed),
    SafeStop,
}
impl<T: Fifo> OwnedBackend<T> {
    /// Offline cold construction only; not a production reconnect/reset recipe.
    pub const fn cold(transport: T) -> Self {
        Self { slots: [const { Slot::empty() }; DATA_POSITIONS], next_id: 1,
            stopped: false, poll_budget: 64, transport }
    }
    /// A private call-count bound, not a negotiated timeout or wall-clock proof.
    /// A future worker also needs a real bounded scheduling/deadline policy.
    pub fn cold_bounded(transport: T, poll_budget: u32) -> Option<Self> {
        if poll_budget == 0 { return None; }
        let mut result = Self::cold(transport);
        result.poll_budget = poll_budget;
        Some(result)
    }
    pub fn stopped(&self) -> bool { self.stopped }
    pub fn retained(&self) -> usize {
        self.slots.iter().filter(|s| s.record.is_some()).count()
    }
    pub fn transport(&self) -> &T { &self.transport }
    pub fn lease(&self, identity: Identity) -> Option<BufferLease> {
        self.slots.get(identity.route.packet_slot as usize)?.record.as_ref()
            .filter(|r| r.identity == identity).map(|r| r.lease)
    }
    /// An ordinary Rust borrow; no asynchronous DMA pointer is exposed. A future
    /// blocking SPI driver must finish reading before this borrow ends, or use
    /// a separately reviewed pinned-buffer lifetime implementation.
    pub fn bytes(&self, identity: Identity, lease: BufferLease) -> Option<&[u8]> {
        let slot = self.slots.get(identity.route.packet_slot as usize)?;
        let r = slot.record.as_ref()?;
        if r.identity != identity || r.lease != lease { return None; }
        Some(&slot.bytes[..lease.datagram_bytes as usize])
    }
    pub fn fifo_payload(&self, identity: Identity, lease: BufferLease) -> Option<&[u8]> {
        self.bytes(identity, lease).map(|b| &b[16..])
    }
    /// The completion status passed into Gateway is derived from the matched
    /// transport proof, not a caller-selected Consumed/Rejected status.
    pub fn poll_one(&mut self, gateway: &mut Gateway, identity: Identity,
                    lease: BufferLease) -> Progress {
        if self.stopped || gateway.stopped() { return Progress::SafeStop; }
        let Some(r) = self.slots.get(identity.route.packet_slot as usize)
            .and_then(|s| s.record.as_ref()) else { return Progress::Stale; };
        if r.identity != identity || r.lease != lease { return Progress::Stale; }
        if r.polls >= self.poll_budget {
            self.stopped = true; gateway.safe_stop(); return Progress::SafeStop;
        }
        let Some(ticket) = r.ticket else { self.stopped = true; gateway.safe_stop(); return Progress::SafeStop; };
        self.slots[identity.route.packet_slot as usize].record.as_mut().unwrap().polls += 1;
        let proof = match self.transport.poll(identity, lease, ticket) {
            Poll::Pending => return Progress::Pending,
            Poll::Unknown => { self.stopped = true; gateway.safe_stop(); return Progress::SafeStop; }
            Poll::Done(p) => p,
        };
        if proof.identity != identity || proof.lease != lease || proof.ticket != ticket {
            // A late/foreign completion does not free any current owner.
            return Progress::Stale;
        }
        if proof.result == Completion::Unknown {
            self.stopped = true; gateway.safe_stop(); return Progress::SafeStop;
        }
        self.slots[identity.route.packet_slot as usize].record.as_mut().unwrap()
            .completed = Some(proof);
        Progress::Completed(gateway.complete(identity, lease.id, proof.result, self))
    }
}
impl<T: Fifo> Backend for OwnedBackend<T> {
    fn reserve(&mut self, identity: Identity, datagram: &[u8], fifo_bytes: u16) -> Reservation {
        if self.stopped { return Reservation::Unknown; }
        let index = identity.route.packet_slot as usize;
        if index >= DATA_POSITIONS || datagram.len() > MAX_DATAGRAM
            || wire::parse_data(datagram) != Ok(identity.route)
            || !identity.owner.basic_valid() || !identity.route.matches(&identity.owner)
            || datagram.len() != usize::from(fifo_bytes) + 16 {
            return Reservation::Unavailable;
        }
        if self.slots[index].record.is_some() { return Reservation::Unavailable; }
        let Some(next) = self.next_id.checked_add(1) else {
            self.stopped = true; return Reservation::Unknown;
        };
        let lease = BufferLease { id: self.next_id, datagram_bytes: datagram.len() as u16, fifo_bytes };
        self.next_id = next;
        self.slots[index].bytes[..datagram.len()].copy_from_slice(datagram);
        self.slots[index].record = Some(Record { identity, lease, ticket: None, completed: None, polls: 0 });
        match self.transport.reserve_capacity(identity, lease) {
            Capacity::Unavailable => { self.slots[index].record = None; Reservation::Unavailable }
            Capacity::Unknown => { self.stopped = true; Reservation::Unknown }
            Capacity::Granted(ticket) => {
                let collision = ticket == 0 || self.slots.iter().enumerate()
                    .any(|(i, s)| i != index && s.record.as_ref().is_some_and(|r| r.ticket == Some(ticket)));
                self.slots[index].record.as_mut().unwrap().ticket = Some(ticket);
                if collision { self.stopped = true; Reservation::Unknown }
                else { Reservation::Owned(lease) }
            }
        }
    }
    fn release(&mut self, identity: Identity, lease: BufferLease) -> bool {
        if self.stopped { return false; }
        let Some(r) = self.slots.get(identity.route.packet_slot as usize)
            .and_then(|s| s.record.as_ref()) else { return false; };
        if r.identity != identity || r.lease != lease { return false; }
        let Some(proof) = r.completed else { self.stopped = true; return false; };
        if !self.transport.retire(proof) { self.stopped = true; return false; }
        self.slots[identity.route.packet_slot as usize].record = None;
        true
    }
}

// Metadata + five full owned datagrams; excludes the adapter and target runtime.
struct NoFifo;
impl Fifo for NoFifo {
    fn reserve_capacity(&mut self, _: Identity, _: BufferLease) -> Capacity { Capacity::Unknown }
    fn poll(&mut self, _: Identity, _: BufferLease, _: u64) -> Poll { Poll::Unknown }
    fn retire(&mut self, _: Proof) -> bool { false }
}
const _: () = assert!(core::mem::size_of::<OwnedBackend<NoFifo>>() <= 8192);
