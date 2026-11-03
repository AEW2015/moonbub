#![no_std]
//! Allocation-free snapshots of ESP-IDF capability heaps for lab profiling.
//! The caller supplies a monotonic clock, a phase and the exact capability mask.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase { BeforeWifi, WifiReady, SocketReady, Streaming, AfterStop }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Snapshot {
    pub phase: Phase,
    pub monotonic_us: u64,
    pub caps: u32,
    pub free_bytes: usize,
    pub largest_free_block: usize,
    pub minimum_free_bytes: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RecordError { Capacity, ClockWentBackwards }

/// Fixed-size history; no heap allocation and no credential or payload storage.
pub struct History<const N: usize> {
    entries: [Option<Snapshot>; N],
    len: usize,
}
impl<const N: usize> History<N> {
    pub const fn new() -> Self { Self { entries: [None; N], len: 0 } }
    pub fn push(&mut self, s: Snapshot) -> Result<(), RecordError> {
        if let Some(last) = self.entries.get(self.len.wrapping_sub(1)).and_then(|v| *v) {
            if s.monotonic_us < last.monotonic_us { return Err(RecordError::ClockWentBackwards); }
        }
        if self.len == N { return Err(RecordError::Capacity); }
        self.entries[self.len] = Some(s);
        self.len += 1;
        Ok(())
    }
    pub fn as_slice(&self) -> &[Option<Snapshot>] { &self.entries[..self.len] }
}
impl<const N: usize> Default for History<N> { fn default() -> Self { Self::new() } }

/// The three ESP-IDF queries are consecutive, not an atomic heap snapshot.
/// The mask must be the ESP-IDF MALLOC_CAP_* combination being investigated.
#[cfg(feature = "esp_idf")]
pub fn capture(phase: Phase, monotonic_us: u64, caps: u32) -> Snapshot {
    extern "C" {
        fn heap_caps_get_free_size(caps: u32) -> usize;
        fn heap_caps_get_largest_free_block(caps: u32) -> usize;
        fn heap_caps_get_minimum_free_size(caps: u32) -> usize;
    }
    // ESP-IDF implements these read-only heap queries. Actual availability and
    // behavior must be checked against the target's IDF version at integration.
    unsafe { Snapshot { phase, monotonic_us, caps,
        free_bytes: heap_caps_get_free_size(caps),
        largest_free_block: heap_caps_get_largest_free_block(caps),
        minimum_free_bytes: heap_caps_get_minimum_free_size(caps),
    } }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn item(time: u64) -> Snapshot { Snapshot { phase: Phase::Streaming, monotonic_us: time, caps: 3, free_bytes: 5000, largest_free_block: 4000, minimum_free_bytes: 3000 } }
    #[test] fn rejects_backwards_clock_without_mutating_history() {
        let mut h=History::<2>::new(); assert_eq!(h.push(item(10)), Ok(()));
        assert_eq!(h.push(item(9)),Err(RecordError::ClockWentBackwards));
        assert_eq!(h.as_slice(), &[Some(item(10))]);
        assert_eq!(h.push(item(10)),Ok(()));
    }
    #[test] fn rejects_full_and_zero_capacity() {
        let mut h=History::<1>::new(); assert_eq!(h.push(item(0)),Ok(()));
        assert_eq!(h.push(item(1)),Err(RecordError::Capacity));
        let mut empty=History::<0>::new(); assert_eq!(empty.push(item(0)),Err(RecordError::Capacity));
    }
    #[cfg(feature = "esp_idf")]
    #[no_mangle] extern "C" fn heap_caps_get_free_size(caps: u32) -> usize { caps as usize + 100 }
    #[cfg(feature = "esp_idf")]
    #[no_mangle] extern "C" fn heap_caps_get_largest_free_block(caps: u32) -> usize { caps as usize + 50 }
    #[cfg(feature = "esp_idf")]
    #[no_mangle] extern "C" fn heap_caps_get_minimum_free_size(caps: u32) -> usize { caps as usize + 25 }
    #[cfg(feature = "esp_idf")]
    #[test] fn esp_adapter_passes_caps_to_all_three_queries() {
        let s=capture(Phase::WifiReady,42,7);
        assert_eq!(s,Snapshot { phase: Phase::WifiReady, monotonic_us:42, caps:7,
            free_bytes:107, largest_free_block:57, minimum_free_bytes:32 });
    }
    #[test] fn records_caps_and_independent_values_without_guessing_coherence() {
        let mut h=History::<1>::new(); let s=Snapshot { largest_free_block: 6000, ..item(1) };
        assert_eq!(h.push(s),Ok(())); assert_eq!(h.as_slice(),&[Some(s)]);
    }
}
