#[path = "../handheld/src/ui/overlay_epoch.rs"]
mod overlay_epoch;
use overlay_epoch::FrameFence;

#[test]
fn same_epoch_allows_all_lines_of_a_complete_frame() {
    let mut frame = FrameFence::new(12);
    let mut writes = Vec::new();
    for line in 0..240 {
        assert_eq!(frame.publish(12, || writes.push(line)), Some(()));
    }
    assert_eq!(writes.len(), 240);
    assert!(!frame.is_stale());
}
#[test]
fn program_attempt_blocks_remaining_lines_and_bounds_update() {
    let mut frame = FrameFence::new(7);
    let mut writes = 0;
    assert_eq!(frame.publish(7, || writes += 1), Some(()));
    assert_eq!(frame.publish(8, || writes += 1), None);
    for _ in 0..240 { assert_eq!(frame.publish(8, || writes += 1), None); }
    // Latch invalidation even if a later caller supplies the old value.
    assert_eq!(frame.publish(7, || writes += 1), None);
    assert_eq!(writes, 1);
    assert!(frame.is_stale());
}
#[test]
fn fresh_render_can_publish_after_reconfiguration() {
    let mut old = FrameFence::new(u32::MAX);
    assert_eq!(old.publish(0, || panic!("old render must not write")), None);
    let mut new = FrameFence::new(0);
    assert_eq!(new.publish(0, || 720), Some(720));
}
#[test]
fn write_failure_is_not_a_success_or_epoch_change() {
    let mut frame = FrameFence::new(1);
    assert_eq!(frame.publish(1, || Err::<(), _>("SPI failure")), Some(Err("SPI failure")));
    assert!(!frame.is_stale());
    assert_eq!(frame.publish(1, || Ok::<_, &str>(())), Some(Ok(())));
}
