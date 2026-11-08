//! Bounded, allocation-free observations of one most-recent frame.
//! Times are local monotonic microseconds, not host capture timestamps.

pub fn valid_stream_write_clock(hz: u32) -> bool { matches!(hz, 20_000_000 | 40_000_000) }
pub fn valid_queue_depth(depth: u32) -> bool { matches!(depth, 4 | 16 | 32) }
pub const QUEUE32_REQUIRED_DMA: usize = 32 * 1024 + 4096 + 33 * (40 + 1024 + 1);
pub const QUEUE32_REQUIRED_LARGEST: usize = 8192;
/// Conservative pre-allocation threshold for the optional 32-slot experiment.
pub fn queue32_dma_guard(free: usize, largest: usize) -> bool {
    free >= QUEUE32_REQUIRED_DMA && largest >= QUEUE32_REQUIRED_LARGEST
}
pub fn stream_write_change_allowed(session: bool, restoring: bool, benchmark: bool) -> bool {
    !session && !restoring && !benchmark
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct BusyDiagnostic {
    pub decision_status: Option<u32>,
    pub accepted_after: Option<u32>,
    pub decoded_after: Option<u32>,
    pub presented_after: Option<u32>,
    pub sof_dequeue_us: u64,
    pub begin_us: u64,
    pub prior_commit_confirmed_us: Option<u64>,
}
impl BusyDiagnostic {
    pub fn since_prior_commit_confirmed_us(&self) -> Option<u64> {
        self.prior_commit_confirmed_us.and_then(|previous| self.begin_us.checked_sub(previous))
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct FrameTrace {
    pub valid: bool,
    pub id: u32,
    pub started_us: u64,
    pub last_packet_us: u64,
    pub finished_us: u64,
    pub packets: u32,
    pub bytes: u32,
    pub max_interarrival_us: u64,
    pub min_interarrival_us: u64,
    pub max_queue_residence_us: u64,
    pub max_consumer_processing_us: u64,
    pub last_consumer_us: u64,
    pub max_consumer_gap_us: u64,
    pub begin_us: u64,
    pub qspi_calls: u32,
    pub qspi_total_us: u64,
    pub qspi_max_us: u64,
    pub lock_total_us: u64,
    pub lock_max_us: u64,
    // The current FPGA register is remaining frame bytes, not FIFO capacity.
    pub min_frame_remaining: u32,
    pub gap_valid: bool,
    pub expected_offset: u32,
    pub observed_offset: u32,
}

impl FrameTrace {
    pub fn start(&mut self, id: u32, now_us: u64) {
        *self = Self { valid: true, id, started_us: now_us,
            min_frame_remaining: u32::MAX, min_interarrival_us: u64::MAX, ..Self::default() };
    }
    pub fn packet(&mut self, now_us: u64) {
        if !self.valid { return; }
        if self.packets != 0 {
            let gap = now_us.saturating_sub(self.last_packet_us);
            self.max_interarrival_us = self.max_interarrival_us.max(gap);
            self.min_interarrival_us = self.min_interarrival_us.min(gap);
        }
        self.last_packet_us = now_us;
        self.packets = self.packets.saturating_add(1);
    }
    pub fn queued(&mut self, delay_us: u64) {
        if self.valid { self.max_queue_residence_us = self.max_queue_residence_us.max(delay_us); }
    }
    pub fn consumer_started(&mut self, now_us: u64) {
        if !self.valid { return; }
        if self.last_consumer_us != 0 {
            self.max_consumer_gap_us = self.max_consumer_gap_us.max(now_us.saturating_sub(self.last_consumer_us));
        }
        self.last_consumer_us = now_us;
    }
    pub fn processing(&mut self, duration_us: u64) {
        if self.valid { self.max_consumer_processing_us = self.max_consumer_processing_us.max(duration_us); }
    }
    pub fn transfer(&mut self, bytes: u32, remaining: u32, lock_us: u64, qspi_us: u64) {
        if !self.valid { return; }
        self.bytes = self.bytes.saturating_add(bytes);
        self.qspi_calls = self.qspi_calls.saturating_add(1);
        self.qspi_total_us = self.qspi_total_us.saturating_add(qspi_us);
        self.qspi_max_us = self.qspi_max_us.max(qspi_us);
        self.lock_total_us = self.lock_total_us.saturating_add(lock_us);
        self.lock_max_us = self.lock_max_us.max(lock_us);
        self.min_frame_remaining = self.min_frame_remaining.min(remaining);
    }
    pub fn gap(&mut self, expected: Option<u32>, observed: u32) {
        if self.valid && !self.gap_valid {
            if let Some(expected) = expected {
                if expected != observed {
                    self.gap_valid = true;
                    self.expected_offset = expected;
                    self.observed_offset = observed;
                }
            }
        }
    }
    pub fn finish(&mut self, now_us: u64) { self.finished_us = now_us; }
    pub fn superseded(&mut self, active: bool, now_us: u64) -> Option<Self> {
        if !active || !self.valid { return None; }
        self.finish(now_us);
        Some(*self)
    }
}

#[derive(Clone, Copy, Debug, Default)]
pub struct Snapshot { pub completed: FrameTrace, pub dropped: FrameTrace }

/// FPGA frame IDs may be reused after source rebind. Only presentations whose
/// count changed after this epoch's baseline belong to the current source.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct PresentationEpoch { pub sequence: u32, pub baseline_presented: u32, pub valid: bool }
impl PresentationEpoch {
    pub fn advance(&mut self, presented: u32) {
        self.sequence = self.sequence.wrapping_add(1);
        self.baseline_presented = presented;
        self.valid = true;
    }
    pub fn contains_new_presentation(&self, count: u32) -> bool {
        self.valid && count != self.baseline_presented
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ProducerTiming { pub datagrams: u32, pub last_us: u64, pub min_gap_us: u64, pub max_gap_us: u64, pub gaps_below_1000us: u32 }
/// Only boost the application consumer from the known default priority.
/// Never alter TCP/IP, radio, UI, or unrelated task priorities.
pub fn consumer_priority(default: u32, boost: bool) -> Option<u32> {
    if !boost { Some(default) } else if default == 5 { Some(6) } else { None }
}
/// Low 32-bit monotonic timestamps wrap about every 71 minutes; differences
/// remain valid for intervals below that duration. MAX denotes no dequeue yet.
pub fn since_last_dequeue(now_us: u64, last_us_low: u32, seen: bool) -> u32 {
    if seen { (now_us as u32).wrapping_sub(last_us_low) } else { u32::MAX }
}
impl ProducerTiming {
    pub fn observe(&mut self, now: u64) {
        if self.datagrams != 0 {
            let gap = now.saturating_sub(self.last_us);
            self.min_gap_us = self.min_gap_us.min(gap);
            self.max_gap_us = self.max_gap_us.max(gap);
            if gap < 1000 { self.gaps_below_1000us = self.gaps_below_1000us.saturating_add(1); }
        }
        self.datagrams = self.datagrams.saturating_add(1); self.last_us = now;
    }
}

#[cfg(test)]
mod tests {
    #[test] fn optional_32_queue_requires_dma_reserve_and_largest_block() {
        for depth in [4,16,32] { assert!(super::valid_queue_depth(depth)); }
        for depth in [0,8,31,33] { assert!(!super::valid_queue_depth(depth)); }
        let threshold=32*1024+4096+33*(40+1024+1);
        assert!(super::queue32_dma_guard(threshold,8192));
        assert!(!super::queue32_dma_guard(threshold-1,8192));
        assert!(!super::queue32_dma_guard(threshold,8191));
    }
    #[test] fn stream_write_clock_is_limited_to_supported_devices() {
        assert!(super::valid_stream_write_clock(20_000_000));
        assert!(super::valid_stream_write_clock(40_000_000));
        assert!(!super::valid_stream_write_clock(0));
        assert!(!super::valid_stream_write_clock(16_000_000));
        assert!(!super::valid_stream_write_clock(50_000_000));
        assert!(super::stream_write_change_allowed(false,false,false));
        assert!(!super::stream_write_change_allowed(true,false,false));
        assert!(!super::stream_write_change_allowed(false,true,false));
        assert!(!super::stream_write_change_allowed(false,false,true));
    }
    #[test] fn busy_diagnostic_uses_confirmed_local_time_and_handles_missing_or_reversed() {
        let mut d=super::BusyDiagnostic::default();
        assert_eq!(d.since_prior_commit_confirmed_us(),None);
        d.begin_us=100; d.prior_commit_confirmed_us=Some(50);
        assert_eq!(d.since_prior_commit_confirmed_us(),Some(50));
        d.prior_commit_confirmed_us=Some(101);
        assert_eq!(d.since_prior_commit_confirmed_us(),None);
    }
    use super::*;
    #[test]
    fn captures_first_gap_and_timing_without_allocations() {
        let mut t = FrameTrace::default();
        t.start(42, 100); t.packet(100); t.transfer(1024, 2048, 3, 12);
        t.packet(150); t.transfer(1024, 1024, 7, 15);
        t.gap(Some(2048), 3072); t.gap(Some(2048), 4096); t.finish(200);
        assert_eq!((t.id, t.packets, t.bytes), (42, 2, 2048));
        assert_eq!((t.qspi_total_us, t.qspi_max_us), (27, 15));
        assert_eq!((t.lock_total_us, t.lock_max_us, t.max_interarrival_us), (10, 7, 50));
        assert_eq!(t.min_interarrival_us, 50);
        assert_eq!((t.min_frame_remaining, t.expected_offset, t.observed_offset), (1024, 2048, 3072));
        assert_eq!(t.finished_us - t.started_us, 100);
    }
    #[test]
    fn start_resets_prior_gap_and_invalid_trace_is_inert() {
        let mut t = FrameTrace::default(); t.packet(1); t.transfer(8, 8, 1, 2);
        assert_eq!(t.packets, 0); t.start(1, 2); t.gap(Some(0), 1);
        t.start(2, 3); assert!(!t.gap_valid); assert_eq!(t.min_frame_remaining, u32::MAX);
    }
    #[test]
    fn new_start_preserves_superseded_incomplete_frame() {
        let mut trace = FrameTrace::default();
        trace.start(41, 10); trace.packet(11); trace.transfer(1024, 2048, 4, 20);
        let dropped = trace.superseded(true, 100).unwrap();
        trace.start(42, 100); trace.packet(101);
        assert_eq!((dropped.id, dropped.finished_us, dropped.bytes), (41, 100, 1024));
        assert_eq!((trace.id, trace.packets, trace.bytes), (42, 1, 0));
        assert!(trace.superseded(false, 110).is_none());
        assert!(FrameTrace::default().superseded(true, 1).is_none());
    }
    #[test]
    fn producer_burst_timing_and_consumer_residence_are_bounded() {
        let mut p=ProducerTiming { min_gap_us:u64::MAX, ..ProducerTiming::default() };
        p.observe(100);p.observe(500);p.observe(2500);
        assert_eq!((p.datagrams,p.min_gap_us,p.max_gap_us,p.gaps_below_1000us),(3,400,2000,1));
        let mut t=FrameTrace::default();t.start(3,10);t.queued(500);t.queued(100);t.processing(900);t.processing(40);t.consumer_started(100);t.consumer_started(600);
        assert_eq!((t.max_queue_residence_us,t.max_consumer_processing_us,t.max_consumer_gap_us),(500,900,500));
    }
    #[test]
    fn priority_experiment_only_boosts_known_consumer_default() {
        assert_eq!(consumer_priority(5,false),Some(5));
        assert_eq!(consumer_priority(5,true),Some(6));
        assert_eq!(consumer_priority(10,true),None);
        assert_eq!(consumer_priority(10,false),Some(10));
    }
    #[test]
    fn dropout_age_handles_unseen_and_timer_wrap() {
        assert_eq!(since_last_dequeue(20,10,false),u32::MAX);
        assert_eq!(since_last_dequeue(20,10,true),10);
        assert_eq!(since_last_dequeue((u32::MAX as u64)+5,u32::MAX-5,true),10);
    }
    #[test]
    fn rebind_epoch_does_not_attribute_previous_display_to_new_sender() {
        let mut e=PresentationEpoch::default();
        assert!(!e.contains_new_presentation(3));
        e.advance(3);assert!(!e.contains_new_presentation(3));
        assert!(e.contains_new_presentation(4));
        e.advance(4);assert!(!e.contains_new_presentation(4));
        e.advance(u32::MAX);assert!(e.contains_new_presentation(0));
    }
}
