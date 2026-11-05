#[path = "../handheld/src/streaming/diagnostic_budget.rs"]
mod diagnostic_budget;
use diagnostic_budget::{PacketBudget, Totals};

#[test]
fn all_forward_calls_and_error_waits_contribute_to_one_completion() {
    let mut packet = PacketBudget::new(100);
    packet.add_forward(5, 0); // lock acquired, then credit/register error
    packet.add_forward(7, 0); packet.add_forward(0, 31); // successful write
    packet.add_forward(11, 0); packet.add_forward(0, 17); // failed write
    packet.add_forward(8_001, 0); // Busy without a write
    assert_eq!(packet.complete(9_000), Totals { lock_us: 8_024,
        qspi_us: 48, consumer_us: 8_900 });
}
#[test]
fn cleanup_tail_changes_elapsed_without_inventing_transfer_time() {
    let mut packet = PacketBudget::new(1000);
    packet.add_forward(3, 20);
    assert_eq!(packet.complete(1023).consumer_us, 23);
    let after_cleanup = packet.complete(1700);
    assert_eq!(after_cleanup, Totals { lock_us: 3, qspi_us: 20, consumer_us: 700 });
}
#[test]
fn next_packet_and_background_have_fresh_zero_budgets() {
    let mut old = PacketBudget::new(1); old.add_forward(33, 77);
    let fresh = PacketBudget::new(900);
    assert_eq!(fresh.complete(903), Totals { lock_us: 0, qspi_us: 0, consumer_us: 3 });
    assert_eq!(old.complete(904).qspi_us, 77);
}
#[test]
fn overflow_saturates_without_wrapping_into_unclipped_range() {
    let mut packet = PacketBudget::new(0);
    packet.add_forward(u64::MAX - 1, u64::MAX - 4);
    packet.add_forward(9, 10);
    let totals = packet.complete(u64::MAX);
    assert_eq!(totals.lock_us, u64::MAX); assert_eq!(totals.qspi_us, u64::MAX);
    assert!(totals.lock_us > u32::MAX as u64 && totals.qspi_us > u32::MAX as u64);
}
#[test]
fn anomalous_clock_sample_fails_to_zero_elapsed_not_wraparound() {
    assert_eq!(PacketBudget::new(100).complete(99).consumer_us, 0);
    assert_eq!(std::mem::size_of::<PacketBudget>(), 24);
}
