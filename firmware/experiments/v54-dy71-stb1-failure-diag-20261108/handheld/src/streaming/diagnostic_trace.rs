//! Opt-in bounded diagnostics. Hot paths use try_lock; no I/O/formatting/heap.
//! Call arm only while producer/consumer/AV are quiescent. Successful arm primes
//! the std Mutex before any armed hot-path call (the target runtime may allocate
//! its mutex backing during initialization, outside the hot path).
//! Accepted-call sequences are monotonic u64, not socket/channel ordering.
//! Contended calls have explicit loss counts, not fabricated records/sequences.
//! First Sequence Failure (detail lower9 bits or bit12) triggers
//! auto-freeze of 96 salient records (normally79pre+trigger+16post); phase maxima
//! and first32 failure identities/tails continue until caller STOP/drain then
//! manual freeze seals all updates. A false seal result requires retry; exports
//! return None while a preseal writer remains in flight. No whole-ring copying.
//! Summary maxima cover coherent completed phase intervals, not scheduler CPU
//! attribution; missing phases invalidate the intervening duration. Export clocks
//! are full u64; stored durations saturate u32 with duration_clipped. Complete's
//! consumer_us includes the caller's entire dequeue-through-recycle/drop interval;
//! zero is valid for Complete; other record kinds use zero/unavailable.
//! Failure tails require matching preaccept incoming+active context and receive
//! timestamp. Collisions/capture losses conservatively mark pending tails
//! ambiguous. Those observations are not a formal unique packet identifier.
//! Queue occupancy is diagnostic (real capacity32): out-of-storage-range values
//! clear queue_valid. No frame/offset ID bits or protocol bounds are reduced.
//! Loss counters use bounded u32 atomics; wrap clears counters_valid. The first
//! overflow clock is independently latched hi/lo+ready by the single producer.
//! Routine phase transitions are single-consumer atomic-only, not ring events.
//! Ring: Enqueue/Dequeue/Failure/QueueOverflow/Recycle/Complete/Transfer.
//! Transfer is one actual background forward result, never an idle heartbeat. Phase maxima
//! are wall-clock observations, not CPU attribution. Snapshot coherence is
//! version checked once; a concurrent writer yields phase_valid=false.
//! Poisoned/contended mutexes fail open for the application and lose diagnostics.
//! Per-Kind rejected-call counters distinguish salient event losses without
//! retaining packet identities or claiming a particular missing completion.
//! SeqCst writer admission/disarm fences exclude late bookkeeping after a
//! successful manual seal; external quiescence remains mandatory for rearm.
use std::sync::{
    atomic::{AtomicBool, AtomicU32, Ordering},
    Mutex,
};
#[cfg(test)]
thread_local! {static MAXIMA_SNAPSHOTS: std::cell::Cell<usize> = const { std::cell::Cell::new(0) };}
pub const RING_CAPACITY: usize = 96;
pub const FAILURE_CAPACITY: usize = 32;
pub const POST_HISTORY: usize = 16;
pub const PHASE_COUNT: usize = 16;
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Enqueue = 0,
    Dequeue = 1,
    Phase = 2,
    QueueOverflow = 3,
    Failure = 4,
    Recycle = 5,
    Complete = 6,
    Transfer = 7,
}
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Idle = 0,
    Packet = 1,
    Begin = 2,
    Admission = 3,
    Flush = 4,
    Lock = 5,
    Access = 6,
    Qspi = 7,
    Commit = 8,
    ErrorAbort = 9,
    Log = 10,
    Feedback = 11,
    Yield = 12,
    Recycle = 13,
    BufferDrop = 14,
    Maintenance = 15,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Position {
    pub frame: u32,
    pub offset: u32,
    pub frame_valid: bool,
    pub offset_valid: bool,
}
impl Position {
    pub const UNKNOWN: Self = Self {
        frame: 0,
        offset: 0,
        frame_valid: false,
        offset_valid: false,
    };
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Context {
    pub incoming: Position,
    pub active: Position,
    pub queued: u32,
    pub queue_valid: bool,
}
impl Context {
    pub const UNKNOWN: Self = Self {
        incoming: Position::UNKNOWN,
        active: Position::UNKNOWN,
        queued: 0,
        queue_valid: false,
    };
}
#[derive(Clone, Copy, Debug)]
pub struct Event {
    pub time_us: u64,
    pub received_us: u64,
    pub kind: Kind,
    pub phase: Phase,
    pub context: Context,
    pub detail: u16,
    pub lock_us: u64,
    pub qspi_us: u64,
    pub consumer_us: u64,
}
impl Event {
    pub const fn new(kind: Kind, time_us: u64, context: Context) -> Self {
        Self {
            time_us,
            received_us: 0,
            kind,
            phase: Phase::Idle,
            context,
            detail: 0,
            lock_us: 0,
            qspi_us: 0,
            consumer_us: 0,
        }
    }
}
#[derive(Clone, Copy, Debug)]
pub struct Record {
    pub epoch: u32,
    pub sequence: u64,
    pub time_us: u64,
    pub received_us: u64,
    pub kind: Kind,
    pub context: Context,
    pub phase: Phase,
    pub phase_since_us: u64,
    pub phase_valid: bool,
    pub detail: u16,
    pub lock_us: u64,
    pub qspi_us: u64,
    pub duration_clipped: bool,
    pub consumer_us: u64,
}
#[derive(Clone, Copy, Debug)]
pub struct Failure {
    pub epoch: u32,
    pub sequence: u64,
    pub time_us: u64,
    pub context: Context,
    pub detail: u16,
    pub received_us: u64,
    pub consumer_us: Option<u64>,
    pub duration_clipped: bool,
    pub tail_ambiguous: bool,
}
#[derive(Clone, Copy, Debug)]
pub struct Trigger {
    pub time_us: u64,
    pub sequence: u64,
    pub received_us: u64,
    pub context: Context,
    pub consumer_context: Context,
    pub phase: Phase,
    pub phase_since_us: u64,
    pub phase_valid: bool,
}
#[derive(Clone, Copy, Debug)]
pub struct Summary {
    pub epoch: u32,
    pub armed: bool,
    pub frozen: bool,
    pub triggered: bool,
    pub trigger_lost: bool,
    pub first_overflow_us: Option<u64>,
    pub len: usize,
    pub failure_len: usize,
    pub post_remaining: usize,
    pub first_sequence: Option<u64>,
    pub last_sequence: Option<u64>,
    pub recorded: u64,
    pub overwritten: u64,
    pub lost_records: u64,
    pub lost_phase: u64,
    pub lost_failures: u64,
    pub queue_overflows: u64,
    pub failure_overflow: u64,
    pub ambiguous_tails: u64,
    pub counters_valid: bool,
    pub phase_max_us: [u64; PHASE_COUNT],
    pub trigger: Option<Trigger>,
}
/// Separate additive diagnostics; existing Summary/USB page schema is unchanged.
/// Counts identify rejected salient call kinds, not specific lost packets.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct LossCounts {
    pub epoch: u32,
    pub counts: [u64; 8], // Kind repr index; Phase is atomic-only and remains0
    pub counters_valid: bool,
}
// Private packed storage; public exports widen durations and never truncate IDs.
#[derive(Clone, Copy)]
struct PackedContext {
    incoming_frame: u32,
    incoming_offset: u32,
    active_frame: u32,
    active_offset: u32,
    queued: u16,
    flags: u16,
}
impl PackedContext {
    const EMPTY: Self = Self {
        incoming_frame: 0,
        incoming_offset: 0,
        active_frame: 0,
        active_offset: 0,
        queued: 0,
        flags: 0,
    };
    fn pack(c: Context) -> Self {
        Self {
            incoming_frame: c.incoming.frame,
            incoming_offset: c.incoming.offset,
            active_frame: c.active.frame,
            active_offset: c.active.offset,
            queued: c.queued.min(u16::MAX as u32) as u16,
            flags: (c.incoming.frame_valid as u16)
                | ((c.incoming.offset_valid as u16) << 1)
                | ((c.active.frame_valid as u16) << 2)
                | ((c.active.offset_valid as u16) << 3)
                | (((c.queue_valid && c.queued <= u16::MAX as u32) as u16) << 4),
        }
    }
    fn unpack(self) -> Context {
        Context {
            incoming: Position {
                frame: self.incoming_frame,
                offset: self.incoming_offset,
                frame_valid: self.flags & 1 != 0,
                offset_valid: self.flags & 2 != 0,
            },
            active: Position {
                frame: self.active_frame,
                offset: self.active_offset,
                frame_valid: self.flags & 4 != 0,
                offset_valid: self.flags & 8 != 0,
            },
            queued: self.queued as u32,
            queue_valid: self.flags & 16 != 0,
        }
    }
}
#[derive(Clone, Copy)]
struct Raw {
    time_us: u64,
    received_us: u64,
    phase_since_us: u64,
    context: PackedContext,
    sequence: u32,
    lock_us: u32,
    qspi_us: u32,
    consumer_us: u32,
    detail: u16,
    kind: Kind,
    phase: Phase,
}
impl Raw {
    const EMPTY: Self = Self {
        time_us: 0,
        received_us: 0,
        phase_since_us: 0,
        context: PackedContext::EMPTY,
        sequence: 0,
        lock_us: 0,
        qspi_us: 0,
        consumer_us: 0,
        detail: 0,
        kind: Kind::Enqueue,
        phase: Phase::Idle,
    };
}
#[derive(Clone, Copy)]
struct RawFailure {
    time_us: u64,
    received_us: u64,
    sequence: u64,
    incoming_frame: u32,
    incoming_offset: u32,
    active_frame: u32,
    active_offset: u32,
    meta: u64,
}
impl RawFailure {
    const EMPTY: Self = Self {
        time_us: 0,
        received_us: 0,
        sequence: 0,
        incoming_frame: 0,
        incoming_offset: 0,
        active_frame: 0,
        active_offset: 0,
        meta: 0,
    };
    fn new(e: Event, sequence: u64) -> Self {
        let c = PackedContext::pack(e.context);
        let flags = if e.context.queued > 63 {
            c.flags & !16
        } else {
            c.flags
        };
        Self {
            time_us: e.time_us,
            received_us: e.received_us,
            sequence,
            incoming_frame: c.incoming_frame,
            incoming_offset: c.incoming_offset,
            active_frame: c.active_frame,
            active_offset: c.active_offset,
            meta: (flags as u64 & 31)
                | ((e.context.queued.min(63) as u64) << 7)
                | ((e.detail as u64) << 13),
        }
    }
    fn context(self) -> Context {
        PackedContext {
            incoming_frame: self.incoming_frame,
            incoming_offset: self.incoming_offset,
            active_frame: self.active_frame,
            active_offset: self.active_offset,
            queued: ((self.meta >> 7) & 63) as u16,
            flags: (self.meta & 31) as u16,
        }
        .unpack()
    }
    fn pending(self) -> bool {
        self.meta & ((1 << 5) | (1 << 61)) == 0
    }
    fn ambiguous(&mut self) {
        self.meta |= 1 << 61
    }
    fn complete(&mut self, elapsed: u64) {
        self.meta |= 1 << 5;
        self.meta |= elapsed.min(u32::MAX as u64) << 29;
        if elapsed > u32::MAX as u64 {
            self.meta |= 1 << 6
        }
    }
}
struct State {
    ring: [Raw; RING_CAPACITY],
    failures: [RawFailure; FAILURE_CAPACITY],
    head: usize,
    len: usize,
    failure_len: usize,
    post: usize,
    epoch: u32,
    sequence: u64,
    ring_last: u64,
    overwritten: u64,
    failure_overflow: u64,
    ambiguous_tails: u64,
    failure_loss_seen: u32,
    phase: Phase,
    phase_since: u64,
    phase_context: Context,
    phase_max: [u64; PHASE_COUNT],
    triggered: bool,
    frozen: bool,
    sealed: bool,
    trigger: Option<Trigger>,
}
impl State {
    const fn new() -> Self {
        Self {
            ring: [Raw::EMPTY; RING_CAPACITY],
            failures: [RawFailure::EMPTY; FAILURE_CAPACITY],
            head: 0,
            len: 0,
            failure_len: 0,
            post: 0,
            epoch: 0,
            sequence: 0,
            ring_last: 0,
            overwritten: 0,
            failure_overflow: 0,
            ambiguous_tails: 0,
            failure_loss_seen: 0,
            phase: Phase::Idle,
            phase_since: 0,
            phase_context: Context::UNKNOWN,
            phase_max: [0; PHASE_COUNT],
            triggered: false,
            frozen: false,
            sealed: false,
            trigger: None,
        }
    }
}
// Single consumer publishes phases. Readers take one versioned snapshot, never
// spin or take the ring mutex. Every payload word is atomic (no Rust data race).
struct AtomicPhase {
    version: AtomicU32,
    words: [AtomicU32; 10], // phase, time lo/hi, packed context's six words, known
    maxima: [AtomicU32; PHASE_COUNT * 2], // full u64 lo/hi under version
}
impl AtomicPhase {
    const fn new() -> Self {
        Self {
            version: AtomicU32::new(0),
            words: [const { AtomicU32::new(0) }; 10],
            maxima: [const { AtomicU32::new(0) }; PHASE_COUNT * 2],
        }
    }
    fn context_snapshot(&self) -> Option<(Phase, u64, Context)> {
        let before = self.version.load(Ordering::SeqCst);
        if before & 1 != 0 {
            return None;
        }
        let w: [u32; 10] = std::array::from_fn(|i| self.words[i].load(Ordering::SeqCst));
        if self.version.load(Ordering::SeqCst) != before || w[9] == 0 {
            return None;
        }
        let phase = match w[0] {
            0 => Phase::Idle,
            1 => Phase::Packet,
            2 => Phase::Begin,
            3 => Phase::Admission,
            4 => Phase::Flush,
            5 => Phase::Lock,
            6 => Phase::Access,
            7 => Phase::Qspi,
            8 => Phase::Commit,
            9 => Phase::ErrorAbort,
            10 => Phase::Log,
            11 => Phase::Feedback,
            12 => Phase::Yield,
            13 => Phase::Recycle,
            14 => Phase::BufferDrop,
            15 => Phase::Maintenance,
            _ => return None,
        };
        let c = PackedContext {
            incoming_frame: w[3],
            incoming_offset: w[4],
            active_frame: w[5],
            active_offset: w[6],
            queued: w[7] as u16,
            flags: w[8] as u16,
        }
        .unpack();
        Some((phase, w[1] as u64 | ((w[2] as u64) << 32), c))
    }
    // Summary/seal only: never collect all16 maxima on the packet record path.
    // Separate version fence covers these full64 atomic pairs independently.
    fn maxima_snapshot(&self) -> Option<[u64; PHASE_COUNT]> {
        #[cfg(test)]
        MAXIMA_SNAPSHOTS.with(|n| n.set(n.get() + 1));
        let before = self.version.load(Ordering::SeqCst);
        if before & 1 != 0 {
            return None;
        }
        let maxima = std::array::from_fn(|i| {
            self.maxima[2 * i].load(Ordering::SeqCst) as u64
                | ((self.maxima[2 * i + 1].load(Ordering::SeqCst) as u64) << 32)
        });
        if self.version.load(Ordering::SeqCst) != before {
            return None;
        }
        Some(maxima)
    }
    // Caller holds writer admission. CAS is one attempt, never a wait loop.
    fn update(&self, phase: Phase, now: u64, context: Context, owner: &Trace) -> bool {
        let version = self.version.load(Ordering::SeqCst);
        if version & 1 != 0
            || self
                .version
                .compare_exchange(
                    version,
                    version.wrapping_add(1),
                    Ordering::SeqCst,
                    Ordering::SeqCst,
                )
                .is_err()
        {
            owner.count(&owner.lost_phase);
            // Multiple phase writers violate the single-consumer contract;
            // do not claim coherent aggregate coverage after such a collision.
            owner.counter_wrapped.store(true, Ordering::SeqCst);
            return false;
        }
        if version >= u32::MAX - 1 {
            owner.counter_wrapped.store(true, Ordering::SeqCst);
        }
        if self.words[9].load(Ordering::SeqCst) != 0 {
            let old = self.words[0].load(Ordering::SeqCst) as usize;
            let since = self.words[1].load(Ordering::SeqCst) as u64
                | ((self.words[2].load(Ordering::SeqCst) as u64) << 32);
            if now >= since && old < PHASE_COUNT {
                let prior = self.maxima[old * 2].load(Ordering::SeqCst) as u64
                    | ((self.maxima[old * 2 + 1].load(Ordering::SeqCst) as u64) << 32);
                let max = prior.max(now - since);
                self.maxima[old * 2].store(max as u32, Ordering::SeqCst);
                self.maxima[old * 2 + 1].store((max >> 32) as u32, Ordering::SeqCst);
            } else {
                owner.count(&owner.lost_phase);
            }
        }
        let c = PackedContext::pack(context);
        let w = [
            phase as u32,
            now as u32,
            (now >> 32) as u32,
            c.incoming_frame,
            c.incoming_offset,
            c.active_frame,
            c.active_offset,
            c.queued as u32,
            c.flags as u32,
            1,
        ];
        for (i, value) in w.iter().enumerate() {
            self.words[i].store(*value, Ordering::SeqCst);
        }
        self.version
            .store(version.wrapping_add(2), Ordering::SeqCst);
        true
    }
    fn reset(&self) {
        self.version.store(0, Ordering::SeqCst);
        for w in &self.words {
            w.store(0, Ordering::SeqCst);
        }
        for w in &self.maxima {
            w.store(0, Ordering::SeqCst);
        }
    }
}
struct Writer<'a>(&'a AtomicU32);
impl Drop for Writer<'_> {
    fn drop(&mut self) {
        self.0.fetch_sub(1, Ordering::SeqCst);
    }
}
pub struct Trace {
    writers: AtomicU32,
    state: Mutex<State>,
    armed: AtomicBool,
    trigger_requested: AtomicBool,
    trigger_lost: AtomicBool,
    atomic_phase: AtomicPhase,
    lost: AtomicU32,
    lost_by_kind: [AtomicU32; 8],
    lost_phase: AtomicU32,
    lost_failure: AtomicU32,
    overflows: AtomicU32,
    counter_wrapped: AtomicBool,
    first_overflow_hi: AtomicU32,
    first_overflow_lo: AtomicU32,
    first_overflow_ready: AtomicBool,
}
pub const STORAGE_BYTES: usize = std::mem::size_of::<Trace>();
pub static TRACE: Trace = Trace::new();
impl Trace {
    pub const fn new() -> Self {
        Self {
            writers: AtomicU32::new(0),
            state: Mutex::new(State::new()),
            armed: AtomicBool::new(false),
            trigger_requested: AtomicBool::new(false),
            trigger_lost: AtomicBool::new(false),
            atomic_phase: AtomicPhase::new(),
            lost: AtomicU32::new(0),
            lost_by_kind: [const { AtomicU32::new(0) }; 8],
            lost_phase: AtomicU32::new(0),
            lost_failure: AtomicU32::new(0),
            overflows: AtomicU32::new(0),
            counter_wrapped: AtomicBool::new(false),
            first_overflow_hi: AtomicU32::new(0),
            first_overflow_lo: AtomicU32::new(0),
            first_overflow_ready: AtomicBool::new(false),
        }
    }
    fn count(&self, c: &AtomicU32) {
        if c.fetch_add(1, Ordering::Relaxed) == u32::MAX {
            self.counter_wrapped.store(true, Ordering::SeqCst)
        }
    }
    /// Caller must prove producer, consumer and AV are quiescent before arm.
    pub fn arm(&self, now: u64) -> bool {
        let Ok(mut s) = self.state.try_lock() else {
            return false;
        };
        // Atomic-only phase writers do not take State: close admission before
        // checking drain, exactly as manual seal. A failed arm requires retry.
        self.armed.store(false, Ordering::SeqCst);
        if self.writers.load(Ordering::SeqCst) != 0 {
            return false;
        }
        let epoch = s.epoch.wrapping_add(1);
        s.head = 0;
        s.len = 0;
        s.failure_len = 0;
        s.post = 0;
        s.epoch = epoch;
        s.sequence = 0;
        s.ring_last = 0;
        s.overwritten = 0;
        s.failure_overflow = 0;
        s.ambiguous_tails = 0;
        s.failure_loss_seen = 0;
        s.phase = Phase::Idle;
        s.phase_since = now;
        s.phase_context = Context::UNKNOWN;
        s.phase_max = [0; PHASE_COUNT];
        s.triggered = false;
        s.frozen = false;
        s.sealed = false;
        s.trigger = None;
        self.atomic_phase.reset();
        self.lost.store(0, Ordering::Relaxed);
        for count in &self.lost_by_kind {
            count.store(0, Ordering::Relaxed);
        }
        self.lost_phase.store(0, Ordering::Relaxed);
        self.lost_failure.store(0, Ordering::Relaxed);
        self.overflows.store(0, Ordering::Relaxed);
        self.first_overflow_hi.store(0, Ordering::Relaxed);
        self.first_overflow_lo.store(0, Ordering::Relaxed);
        self.first_overflow_ready.store(false, Ordering::SeqCst);
        self.counter_wrapped.store(false, Ordering::SeqCst);
        self.trigger_requested.store(false, Ordering::SeqCst);
        self.trigger_lost.store(false, Ordering::SeqCst);
        self.armed.store(true, Ordering::SeqCst);
        true
    }
    pub fn record(&self, e: Event) -> bool {
        // Register BEFORE any armed lookup. Rearm cannot pass its drain check
        // while a call that observed the old capture is paused before entry.
        self.writers.fetch_add(1, Ordering::SeqCst);
        let _writer = Writer(&self.writers);
        self.record_admitted(e)
    }
    fn record_admitted(&self, e: Event) -> bool {
        if !self.armed.load(Ordering::SeqCst) {
            return false;
        }
        if e.kind == Kind::Phase {
            return self
                .atomic_phase
                .update(e.phase, e.time_us, e.context, self);
        }
        if e.kind == Kind::QueueOverflow {
            let old = self.overflows.fetch_add(1, Ordering::Relaxed);
            if old == u32::MAX {
                self.counter_wrapped.store(true, Ordering::SeqCst)
            }
            if old == 0 && !self.first_overflow_ready.load(Ordering::SeqCst) {
                self.first_overflow_hi
                    .store((e.time_us >> 32) as u32, Ordering::Relaxed);
                self.first_overflow_lo
                    .store(e.time_us as u32, Ordering::Relaxed);
                self.first_overflow_ready.store(true, Ordering::SeqCst)
            }
        }
        let trigger_candidate = e.kind == Kind::Failure && e.detail & 0x11ff != 0;
        let first_trigger =
            trigger_candidate && !self.trigger_requested.swap(true, Ordering::SeqCst);
        let Ok(mut s) = self.state.try_lock() else {
            if !self.armed.load(Ordering::SeqCst) {
                return false;
            }
            self.count(&self.lost);
            self.count(&self.lost_by_kind[e.kind as usize]);
            if e.kind == Kind::Failure {
                self.count(&self.lost_failure)
            }
            if first_trigger {
                self.trigger_lost.store(true, Ordering::SeqCst)
            }
            return false;
        };
        if !self.armed.load(Ordering::SeqCst) {
            return false;
        }
        if s.sequence == u64::MAX {
            self.counter_wrapped.store(true, Ordering::SeqCst)
        }
        s.sequence = s.sequence.saturating_add(1);
        let seq = s.sequence;
        let phase_valid =
            if let Some((phase, since, context)) = self.atomic_phase.context_snapshot() {
                s.phase = phase;
                s.phase_since = since;
                s.phase_context = context;
                since <= e.time_us
            } else {
                false
            };
        let newly_triggered = !s.triggered && self.trigger_requested.load(Ordering::SeqCst);
        if newly_triggered {
            s.triggered = true;
            s.post = POST_HISTORY;
            if !self.trigger_lost.load(Ordering::SeqCst) && first_trigger {
                s.trigger = Some(Trigger {
                    time_us: e.time_us,
                    sequence: seq,
                    received_us: e.received_us,
                    context: e.context,
                    consumer_context: s.phase_context,
                    phase: s.phase,
                    phase_since_us: s.phase_since,
                    phase_valid,
                })
            } else {
                self.trigger_lost.store(true, Ordering::SeqCst)
            }
        }
        if e.kind == Kind::Failure {
            if s.failure_len < FAILURE_CAPACITY {
                let i = s.failure_len;
                s.failures[i] = RawFailure::new(e, seq);
                s.failure_len += 1
            } else {
                s.failure_overflow = s.failure_overflow.saturating_add(1);
                for j in 0..s.failure_len {
                    if s.failures[j].pending() {
                        s.failures[j].ambiguous();
                        s.ambiguous_tails = s.ambiguous_tails.saturating_add(1)
                    }
                }
            }
        }
        let lost_failure = self.lost_failure.load(Ordering::SeqCst);
        if lost_failure != s.failure_loss_seen {
            for i in 0..s.failure_len {
                if s.failures[i].pending() {
                    s.failures[i].ambiguous();
                    s.ambiguous_tails = s.ambiguous_tails.saturating_add(1)
                }
            }
            s.failure_loss_seen = lost_failure;
        }
        if e.kind == Kind::Complete {
            let mut matched = None;
            let mut count = 0;
            for i in 0..s.failure_len {
                let f = s.failures[i];
                let c = f.context();
                if f.pending()
                    && f.received_us == e.received_us
                    && c.incoming == e.context.incoming
                    && c.active == e.context.active
                {
                    matched = Some(i);
                    count += 1
                }
            }
            if count == 1 {
                s.failures[matched.unwrap()].complete(e.consumer_us)
            } else if count > 1 {
                for i in 0..s.failure_len {
                    let f = s.failures[i];
                    let c = f.context();
                    if f.pending()
                        && f.received_us == e.received_us
                        && c.incoming == e.context.incoming
                        && c.active == e.context.active
                    {
                        s.failures[i].ambiguous();
                        s.ambiguous_tails = s.ambiguous_tails.saturating_add(1)
                    }
                }
            }
        }
        if s.frozen {
            if e.kind == Kind::Complete {
                self.atomic_phase
                    .update(Phase::Idle, e.time_us, e.context, self);
            }
            return false;
        }
        let mut context = PackedContext::pack(e.context);
        let valid = phase_valid;
        if valid {
            context.flags |= 32
        }
        if e.lock_us > u32::MAX as u64
            || e.qspi_us > u32::MAX as u64
            || e.consumer_us > u32::MAX as u64
        {
            context.flags |= 64
        }
        let raw = Raw {
            time_us: e.time_us,
            received_us: e.received_us,
            phase_since_us: s.phase_since,
            context,
            sequence: seq as u32,
            lock_us: e.lock_us.min(u32::MAX as u64) as u32,
            qspi_us: e.qspi_us.min(u32::MAX as u64) as u32,
            consumer_us: e.consumer_us.min(u32::MAX as u64) as u32,
            detail: e.detail,
            kind: e.kind,
            phase: s.phase,
        };
        let i = s.head;
        s.ring[i] = raw;
        s.head = (i + 1) % RING_CAPACITY;
        s.ring_last = seq;
        if s.len < RING_CAPACITY {
            s.len += 1
        } else {
            s.overwritten = s.overwritten.saturating_add(1)
        }
        if e.kind == Kind::Complete {
            self.atomic_phase
                .update(Phase::Idle, e.time_us, e.context, self);
        }
        if s.triggered && !newly_triggered && s.post > 0 {
            s.post -= 1;
            if s.post == 0 {
                s.frozen = true
            }
        }
        true
    }
    pub fn phase(&self, phase: Phase, time_us: u64, context: Context) -> bool {
        let mut e = Event::new(Kind::Phase, time_us, context);
        e.phase = phase;
        self.record(e)
    }
    /// Caller must STOP/drain before export. Manual freeze does not invent trigger.
    pub fn freeze(&self, now: u64) -> bool {
        let Ok(mut s) = self.state.try_lock() else {
            return false;
        };
        self.armed.store(false, Ordering::SeqCst);
        if self.writers.load(Ordering::SeqCst) != 0 {
            return false;
        }
        // Only successful manual seal sets this; a failed in-flight-writer
        // attempt can disarm an auto-frozen trace without finishing the seal.
        if s.sealed {
            return true;
        }
        if let Some((phase, since, context)) = self.atomic_phase.context_snapshot() {
            // Close final phase with no new interval start after successful seal.
            self.atomic_phase.update(phase, now, context, self);
            if let Some(maxima) = self.atomic_phase.maxima_snapshot() {
                s.phase_max = maxima;
            }
            let _ = since;
        }
        if self.trigger_requested.load(Ordering::SeqCst) && !s.triggered {
            s.triggered = true;
            s.post = POST_HISTORY;
            self.trigger_lost.store(true, Ordering::SeqCst)
        }
        s.frozen = true;
        s.sealed = true;
        true
    }
    pub fn summary(&self) -> Option<Summary> {
        let s = self.state.try_lock().ok()?;
        if !self.armed.load(Ordering::SeqCst) && self.writers.load(Ordering::SeqCst) != 0 {
            return None;
        }
        Some(Summary {
            epoch: s.epoch,
            armed: self.armed.load(Ordering::SeqCst),
            frozen: s.frozen,
            triggered: s.triggered || self.trigger_requested.load(Ordering::SeqCst),
            trigger_lost: self.trigger_lost.load(Ordering::SeqCst),
            first_overflow_us: if self.first_overflow_ready.load(Ordering::SeqCst) {
                Some(
                    ((self.first_overflow_hi.load(Ordering::Relaxed) as u64) << 32)
                        | self.first_overflow_lo.load(Ordering::Relaxed) as u64,
                )
            } else {
                None
            },
            len: s.len,
            failure_len: s.failure_len,
            post_remaining: s.post,
            first_sequence: if s.len == 0 {
                None
            } else {
                let r = s.ring[(s.head + RING_CAPACITY - s.len) % RING_CAPACITY];
                Some(s.ring_last - (s.ring_last as u32).wrapping_sub(r.sequence) as u64)
            },
            last_sequence: if s.len == 0 { None } else { Some(s.ring_last) },
            recorded: s.sequence,
            overwritten: s.overwritten,
            lost_records: self.lost.load(Ordering::Relaxed) as u64,
            lost_phase: self.lost_phase.load(Ordering::Relaxed) as u64,
            lost_failures: self.lost_failure.load(Ordering::Relaxed) as u64,
            queue_overflows: self.overflows.load(Ordering::Relaxed) as u64,
            failure_overflow: s.failure_overflow,
            ambiguous_tails: s.ambiguous_tails,
            counters_valid: !self.counter_wrapped.load(Ordering::SeqCst),
            phase_max_us: self.atomic_phase.maxima_snapshot().unwrap_or(s.phase_max),
            trigger: s.trigger,
        })
    }
    /// STOP and successful manual freeze give stable totals. While armed,
    /// this is a bounded observation and the independent counters can advance.
    pub fn loss_counts(&self) -> Option<LossCounts> {
        let s = self.state.try_lock().ok()?;
        if !self.armed.load(Ordering::SeqCst) && self.writers.load(Ordering::SeqCst) != 0 {
            return None;
        }
        Some(LossCounts {
            epoch: s.epoch,
            counts: std::array::from_fn(|i| self.lost_by_kind[i].load(Ordering::SeqCst) as u64),
            counters_valid: !self.counter_wrapped.load(Ordering::SeqCst),
        })
    }
    pub fn read(&self, index: usize) -> Option<Record> {
        let s = self.state.try_lock().ok()?;
        if !s.frozen
            || index >= s.len
            || (!self.armed.load(Ordering::SeqCst) && self.writers.load(Ordering::SeqCst) != 0)
        {
            return None;
        }
        let r = s.ring[(s.head + RING_CAPACITY - s.len + index) % RING_CAPACITY];
        Some(Record {
            epoch: s.epoch,
            sequence: s.ring_last - (s.ring_last as u32).wrapping_sub(r.sequence) as u64,
            time_us: r.time_us,
            received_us: r.received_us,
            kind: r.kind,
            context: r.context.unpack(),
            phase: r.phase,
            phase_since_us: r.phase_since_us,
            phase_valid: r.context.flags & 32 != 0,
            detail: r.detail,
            lock_us: r.lock_us as u64,
            qspi_us: r.qspi_us as u64,
            duration_clipped: r.context.flags & 64 != 0,
            consumer_us: r.consumer_us as u64,
        })
    }
    pub fn read_failure(&self, index: usize) -> Option<Failure> {
        let s = self.state.try_lock().ok()?;
        if !s.frozen
            || index >= s.failure_len
            || (!self.armed.load(Ordering::SeqCst) && self.writers.load(Ordering::SeqCst) != 0)
        {
            return None;
        }
        let f = s.failures[index];
        Some(Failure {
            epoch: s.epoch,
            sequence: f.sequence,
            time_us: f.time_us,
            context: f.context(),
            detail: ((f.meta >> 13) & 65535) as u16,
            received_us: f.received_us,
            consumer_us: if f.meta & (1 << 5) != 0 {
                Some((f.meta >> 29) & 0xFFFF_FFFF)
            } else {
                None
            },
            duration_clipped: f.meta & (1 << 6) != 0,
            tail_ambiguous: f.meta & (1 << 61) != 0,
        })
    }
    #[cfg(test)]
    pub fn test_maxima_snapshot_calls() -> usize {
        MAXIMA_SNAPSHOTS.with(|n| n.get())
    }
    #[cfg(test)]
    pub fn test_record_before_first_armed_lookup(&self, e: Event, boundary: impl FnOnce()) -> bool {
        self.writers.fetch_add(1, Ordering::SeqCst);
        let _writer = Writer(&self.writers);
        boundary();
        self.record_admitted(e)
    }
    #[cfg(test)]
    pub fn with_test_phase_publication(&self, f: impl FnOnce()) {
        self.atomic_phase.version.fetch_add(1, Ordering::SeqCst);
        f();
        self.atomic_phase.version.fetch_add(1, Ordering::SeqCst);
    }
    #[cfg(test)]
    pub fn with_test_writer(&self, f: impl FnOnce()) {
        self.writers.fetch_add(1, Ordering::SeqCst);
        let _w = Writer(&self.writers);
        f()
    }
    #[cfg(test)]
    pub fn test_set_sequence(&self, v: u64) {
        self.state.lock().unwrap().sequence = v;
    }
    #[cfg(test)]
    pub fn with_test_lock(&self, f: impl FnOnce()) {
        let _g = self.state.lock().unwrap();
        f()
    }
}
pub fn arm(now: u64) -> bool {
    TRACE.arm(now)
}
pub fn freeze(now: u64) -> bool {
    TRACE.freeze(now)
}
pub fn record(event: Event) -> bool {
    TRACE.record(event)
}
pub fn phase(phase: Phase, now: u64, context: Context) -> bool {
    TRACE.phase(phase, now, context)
}
pub fn summary() -> Option<Summary> {
    TRACE.summary()
}
pub fn read(index: usize) -> Option<Record> {
    TRACE.read(index)
}
pub fn read_failure(index: usize) -> Option<Failure> {
    TRACE.read_failure(index)
}

pub fn loss_counts() -> Option<LossCounts> {
    TRACE.loss_counts()
}
