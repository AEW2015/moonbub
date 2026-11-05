//! Allocation-free per-consumer-packet forwarding observations.
//! Lock time includes each forward acquisition wait (including Busy). QSPI time
//! includes each attempted payload write, including errors. These are subsets
//! of consumer elapsed time, not an accounting partition or all Device access.
//! u64 saturation is also >u32::MAX, so the trace core marks duration_clipped.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PacketBudget { started_us: u64, lock_us: u64, qspi_us: u64 }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Totals { pub lock_us: u64, pub qspi_us: u64, pub consumer_us: u64 }
impl PacketBudget {
    pub const fn new(started_us: u64) -> Self { Self { started_us, lock_us: 0, qspi_us: 0 } }
    pub fn add_forward(&mut self, lock_us: u64, qspi_us: u64) {
        self.lock_us = self.lock_us.saturating_add(lock_us);
        self.qspi_us = self.qspi_us.saturating_add(qspi_us);
    }
    /// Sample after cleanup and buffer recycle/drop, not after the last write.
    pub fn complete(self, now_us: u64) -> Totals {
        Totals { lock_us: self.lock_us, qspi_us: self.qspi_us,
            consumer_us: now_us.saturating_sub(self.started_us) }
    }
}
