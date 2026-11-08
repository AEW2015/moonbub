//! Joint startup admission after bounded queue/batch/optional AV allocations.
//! Samples cannot prove future allocation success or identify the prior caller.
pub const SESSION_FREE_RESERVE: usize = 32 * 1024;
pub const SESSION_LARGEST_RESERVE: usize = 16 * 1024;
// A separate conservative initial envelope for32 slots. Includes packet storage,
// queue/AV threads+buffers and renderer/runtime margin; allocator overhead and
// fragmentation remain sampled physical gates, not an exact accounting proof.
pub const QUEUE32_STARTUP_FREE: usize = 96 * 1024;
pub fn admit_queue32(depth: usize, free: usize, largest: usize) -> bool {
    depth != 32 || (free >= QUEUE32_STARTUP_FREE && largest >= SESSION_LARGEST_RESERVE)
}
pub fn admit_session(free: usize, largest: usize) -> bool {
    free >= SESSION_FREE_RESERVE && largest >= SESSION_LARGEST_RESERVE
}
#[cfg(test)] mod tests {
 use super::*;
 #[test] fn both_reserves_are_required_including_boundaries(){
  assert!(admit_session(SESSION_FREE_RESERVE,SESSION_LARGEST_RESERVE));
  assert!(!admit_session(SESSION_FREE_RESERVE-1,usize::MAX));
  assert!(!admit_session(usize::MAX,SESSION_LARGEST_RESERVE-1));
  assert!(!admit_session(0,0));
 }
 #[test] fn queue32_is_explicit_without_fallback(){
  assert!(admit_queue32(32,QUEUE32_STARTUP_FREE,SESSION_LARGEST_RESERVE));
  assert!(!admit_queue32(32,QUEUE32_STARTUP_FREE-1,usize::MAX));
  assert!(!admit_queue32(32,usize::MAX,SESSION_LARGEST_RESERVE-1));
  assert!(admit_queue32(16,0,0)); // existing smaller-queue guards still apply
 }
 #[test] fn prior_heap_snapshot_is_not_a_reproduction_or_lifetime_guarantee(){
  assert!(admit_session(50400,21504));
 }
}
