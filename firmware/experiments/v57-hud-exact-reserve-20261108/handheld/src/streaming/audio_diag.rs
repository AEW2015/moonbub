//! Bounded diagnostics owned by the AV task; USB reads small pages only.
use super::{audio_io::Phase, service_policy::{InputMetrics, ServiceMetrics}};
#[repr(usize)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reason {
    QueueFull,
    QueueAge,
    BadIma,
    NotUsable,
    FpgaFull,
    IoUnconfirmed,
    Timeout,
    Cancel,
    SessionEnd,
    SourceMismatch,
    IdleFlush,
}
pub const REASONS: usize = 11;
#[derive(Clone, Copy, Debug)]
pub struct DropRecord {
    pub sequence: u32,
    pub monotonic_us: u64,
    pub reason: Reason,
    pub phase: Phase,
    pub pending_age_us: u64,
    pub queued_count: u8,
    pub session_serial: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SnapshotFailure {
    LockMiss,
    Io(u8),
    Identity,
    Offline,
    StatusChanged,
    Range,
}
#[derive(Clone, Copy)]
pub struct Diagnostics {
    pub service: ServiceMetrics,
    pub input: InputMetrics,
    pub control_faults: u32,
    pub io_faults: u32,
    pub valid_audio: u32,
    pub enqueued: u32,
    pub dequeued: u32,
    pub busy_deferrals: u32,
    pub stale_or_foreign: u32,
    pub malformed: u32,
    pub drops: [u32; REASONS],
    pub first: Option<DropRecord>,
    pub last: Option<DropRecord>,
    pub queued: u32,
    pub queue_high: u32,
    pub max_queue_age_us: u64,
    pub lock_misses: u32,
    pub consecutive_misses: u32,
    pub max_consecutive_misses: u32,
    pub successful_steps: u32,
    pub max_step_us: u64,
    pub max_lock_hold_us: u64,
    pub max_loop_gap_us: u64,
    pub max_arrival_gap_us: u64,
    pub max_pending_us: u64,
    pub max_phase_us: u64,
    pub pending_sequence: Option<u32>,
    pub pending_since: u64,
    pub phase: Phase,
    pub phase_since: u64,
    pub session_serial: u32,
    pub snapshot_ok: u32,
    pub snapshot_lock_miss: u32,
    pub snapshot_io: [u32; 10],
    pub snapshot_identity: u32,
    pub snapshot_offline: u32,
    pub snapshot_changed: u32,
    pub snapshot_range: u32,
    pub last_snapshot_failure: Option<SnapshotFailure>,
    pub max_snapshot_us: u64,
    pub task_priority: u32,
    pub task_core: u32,
}
impl Diagnostics {
    pub const fn new() -> Self {
        Self {
            service: ServiceMetrics::new(),
            input: InputMetrics::new(),
            control_faults: 0,
            io_faults: 0,
            valid_audio: 0,
            enqueued: 0,
            dequeued: 0,
            busy_deferrals: 0,
            stale_or_foreign: 0,
            malformed: 0,
            drops: [0; REASONS],
            first: None,
            last: None,
            queued: 0,
            queue_high: 0,
            max_queue_age_us: 0,
            lock_misses: 0,
            consecutive_misses: 0,
            max_consecutive_misses: 0,
            successful_steps: 0,
            max_step_us: 0,
            max_lock_hold_us: 0,
            max_loop_gap_us: 0,
            max_arrival_gap_us: 0,
            max_pending_us: 0,
            max_phase_us: 0,
            pending_sequence: None,
            pending_since: 0,
            phase: Phase::Idle,
            phase_since: 0,
            session_serial: 0,
            snapshot_ok: 0,
            snapshot_lock_miss: 0,
            snapshot_io: [0; 10],
            snapshot_identity: 0,
            snapshot_offline: 0,
            snapshot_changed: 0,
            snapshot_range: 0,
            last_snapshot_failure: None,
            max_snapshot_us: 0,
            task_priority: 0,
            task_core: 0,
        }
    }
    pub fn pending_age(&self, now: u64) -> u64 {
        if self.pending_sequence.is_some() {
            now.saturating_sub(self.pending_since)
        } else {
            0
        }
    }
    pub fn phase(&mut self, phase: Phase, now: u64) {
        self.max_phase_us = self.max_phase_us.max(now.saturating_sub(self.phase_since));
        if phase != self.phase {
            self.phase = phase;
            self.phase_since = now;
        }
        self.max_pending_us = self.max_pending_us.max(self.pending_age(now));
    }
    pub fn start_pending(&mut self, sequence: u32, now: u64) {
        self.pending_sequence = Some(sequence);
        self.pending_since = now;
    }
    pub fn finish_pending(&mut self, now: u64) {
        self.max_pending_us = self.max_pending_us.max(self.pending_age(now));
        self.pending_sequence = None;
    }
    pub fn drop_block(
        &mut self,
        sequence: u32,
        reason: Reason,
        phase: Phase,
        now: u64,
        queued: usize,
    ) {
        self.drops[reason as usize] = self.drops[reason as usize].saturating_add(1);
        let record = DropRecord {
            sequence,
            monotonic_us: now,
            reason,
            phase,
            pending_age_us: self.pending_age(now),
            queued_count: queued as u8,
            session_serial: self.session_serial,
        };
        if self.first.is_none() {
            self.first = Some(record)
        }
        self.last = Some(record);
    }
    pub fn snapshot_failure(&mut self, f: SnapshotFailure) {
        let value = match f {
            SnapshotFailure::LockMiss => &mut self.snapshot_lock_miss,
            SnapshotFailure::Io(stage) => &mut self.snapshot_io[(stage as usize).min(9)],
            SnapshotFailure::Identity => &mut self.snapshot_identity,
            SnapshotFailure::Offline => &mut self.snapshot_offline,
            SnapshotFailure::StatusChanged => &mut self.snapshot_changed,
            SnapshotFailure::Range => &mut self.snapshot_range,
        };
        *value = value.saturating_add(1);
        self.last_snapshot_failure = Some(f);
    }
    pub fn step(&mut self, acquired: bool, duration: u64, held: u64, phase: Phase, now: u64) {
        if acquired {
            self.successful_steps = self.successful_steps.saturating_add(1);
            self.consecutive_misses = 0;
            self.max_lock_hold_us = self.max_lock_hold_us.max(held);
        } else {
            self.lock_misses = self.lock_misses.saturating_add(1);
            self.consecutive_misses = self.consecutive_misses.saturating_add(1);
            self.max_consecutive_misses = self.max_consecutive_misses.max(self.consecutive_misses);
        }
        self.max_step_us = self.max_step_us.max(duration);
        self.phase(phase, now);
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn first_last_zero_max_and_session_serial_are_exact() {
        let mut d = Diagnostics::new();
        d.session_serial = 3;
        d.start_pending(0, 10);
        d.drop_block(0, Reason::QueueAge, Phase::Pcm, 20, 4);
        d.drop_block(u32::MAX, Reason::FpgaFull, Phase::Ready, 50, 2);
        assert_eq!(d.first.unwrap().sequence, 0);
        assert_eq!(d.first.unwrap().pending_age_us, 10);
        assert_eq!(d.last.unwrap().sequence, u32::MAX);
        assert_eq!(d.last.unwrap().queued_count, 2);
        assert_eq!(d.last.unwrap().session_serial, 3);
    }
    #[test]
    fn snapshot_causes_not_merged() {
        let mut d = Diagnostics::new();
        for f in [
            SnapshotFailure::LockMiss,
            SnapshotFailure::Io(4),
            SnapshotFailure::Identity,
            SnapshotFailure::Offline,
            SnapshotFailure::StatusChanged,
            SnapshotFailure::Range,
        ] {
            d.snapshot_failure(f);
        }
        assert_eq!(d.snapshot_lock_miss, 1);
        assert_eq!(d.snapshot_io[4], 1);
        assert_eq!(d.snapshot_identity, 1);
        assert_eq!(d.snapshot_offline, 1);
        assert_eq!(d.snapshot_changed, 1);
        assert_eq!(d.snapshot_range, 1);
    }
    #[test]
    fn failed_attempts_and_successful_steps_are_separate() {
        let mut d = Diagnostics::new();
        d.start_pending(12, 0);
        for i in 0..20 {
            d.step(false, 1, 0, Phase::Frames, i);
        }
        assert_eq!(d.lock_misses, 20);
        assert_eq!(d.successful_steps, 0);
        assert_eq!(d.max_consecutive_misses, 20);
        d.step(true, 4, 3, Phase::Sequence, 100);
        assert_eq!(d.successful_steps, 1);
        assert_eq!(d.consecutive_misses, 0);
        assert_eq!(d.max_pending_us, 100);
        d.finish_pending(120);
        assert_eq!(d.max_pending_us, 120);
    }
}
