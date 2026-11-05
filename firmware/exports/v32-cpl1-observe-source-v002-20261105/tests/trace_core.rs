#[path = "../handheld/src/streaming/diagnostic_trace.rs"]
#[allow(dead_code)]
mod diagnostic_trace;
use diagnostic_trace::*;
fn c(id: u32) -> Context {
    Context {
        incoming: Position {
            frame: id,
            offset: 5120,
            frame_valid: true,
            offset_valid: true,
        },
        active: Position {
            frame: id.wrapping_sub(1),
            offset: 4096,
            frame_valid: true,
            offset_valid: true,
        },
        queued: 31,
        queue_valid: true,
    }
}
fn auto_freeze(t: &Trace, time: u64) {
    let mut trigger = e(Kind::Failure, time, 4708);
    trigger.detail = 64;
    t.record(trigger);
    for i in 1..=POST_HISTORY {
        t.record(e(Kind::Enqueue, time + i as u64, 1));
    }
    assert!(t.summary().unwrap().frozen);
}
fn e(kind: Kind, time: u64, id: u32) -> Event {
    let mut e = Event::new(kind, time, c(id));
    e.received_us = time.saturating_sub(2);
    e
}
#[test]
fn exact_static_budget() {
    println!(
        "TRACE_STORAGE_BYTES={STORAGE_BYTES}; ring={RING_CAPACITY}; failures={FAILURE_CAPACITY}"
    );
    assert!(STORAGE_BYTES <= 9 * 1024);
    assert_eq!(RING_CAPACITY, 96);
}
#[test]
fn disarmed_then_arm_and_export_gate() {
    let t = Trace::new();
    assert!(!t.record(e(Kind::Failure, 1, 1110)));
    assert_eq!(t.summary().unwrap().len, 0);
    assert!(t.arm(2));
    assert!(t.record(e(Kind::Dequeue, 3, 1)));
    assert!(t.read(0).is_none());
    t.freeze(4);
    assert_eq!(t.read(0).unwrap().epoch, 1);
    assert!(t.read(1).is_none());
    assert!(t.arm(5));
    assert_eq!(t.summary().unwrap().epoch, 2);
    assert_eq!(t.summary().unwrap().failure_len, 0);
}
#[test]
fn real_wrap_keeps_recent_chronology_and_u64_times() {
    let t = Trace::new();
    t.arm(0);
    let base = (u32::MAX as u64) * 3;
    for i in 1..=150 {
        t.record(e(Kind::Enqueue, base + i, i as u32));
    }
    t.freeze(base + 151);
    let s = t.summary().unwrap();
    assert_eq!((s.len, s.overwritten), (96, 54));
    assert_eq!(s.first_sequence, Some(55));
    for i in 0..96 {
        let r = t.read(i).unwrap();
        assert_eq!(r.sequence, 55 + i as u64);
        assert_eq!(r.time_us, base + 55 + i as u64);
        assert_eq!(r.received_us, r.time_us - 2);
    }
}
#[test]
fn overflow_prelude_does_not_preempt_sequence_window() {
    let t = Trace::new();
    t.arm(0);
    for i in 0..140 {
        assert!(t.record(e(Kind::QueueOverflow, i, 4708)));
    }
    let s = t.summary().unwrap();
    assert!(!s.triggered && !s.frozen);
    assert_eq!(s.queue_overflows, 140);
    assert_eq!(s.first_overflow_us, Some(0));
    t.phase(Phase::ErrorAbort, 141, c(4706));
    let mut f = e(Kind::Failure, 142, 4706);
    f.detail = 64;
    assert!(t.record(f));
    let tr = t.summary().unwrap().trigger.unwrap();
    assert_eq!(tr.context.incoming.frame, 4706);
    assert_eq!(tr.phase, Phase::ErrorAbort);
    assert_eq!(t.summary().unwrap().post_remaining, 16);
    let mut done = e(Kind::Complete, 143, 4706);
    done.received_us = f.received_us;
    done.consumer_us = 80;
    assert!(t.record(done));
    for i in 0..15 {
        t.record(e(Kind::QueueOverflow, 144 + i, 4800));
    }
    let s = t.summary().unwrap();
    assert!(s.frozen);
    assert_eq!(s.len, 96);
    assert_eq!(s.first_sequence, Some(62));
    assert_eq!(t.read(79).unwrap().kind, Kind::Failure);
    assert_eq!(t.read(80).unwrap().kind, Kind::Complete);
    assert_eq!(t.read_failure(0).unwrap().consumer_us, Some(80));
}
#[test]
fn phase_max_positive_and_after_freeze() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Packet, 10, c(1));
    t.phase(Phase::Lock, 20, c(1));
    t.phase(Phase::Qspi, 45, c(1));
    assert_eq!(
        t.summary().unwrap().phase_max_us[Phase::Packet as usize],
        10
    );
    assert_eq!(t.summary().unwrap().phase_max_us[Phase::Lock as usize], 25);
    auto_freeze(&t, 50);
    t.phase(Phase::Access, 70, c(1));
    t.phase(Phase::Maintenance, 100, Context::UNKNOWN);
    assert_eq!(t.summary().unwrap().phase_max_us[Phase::Qspi as usize], 25);
    assert_eq!(
        t.summary().unwrap().phase_max_us[Phase::Access as usize],
        30
    );
}

#[test]
fn atomic_phase_bypasses_ring_lock_and_incoherent_snapshot_is_invalid() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Qspi, 10, c(1));
    t.with_test_lock(|| assert!(t.phase(Phase::Access, 20, c(1))));
    assert_eq!(t.summary().unwrap().len, 0);
    assert_eq!(t.summary().unwrap().lost_phase, 0);
    t.with_test_phase_publication(|| {
        let mut f = e(Kind::Failure, 30, 2);
        f.detail = 64;
        assert!(t.record(f));
    });
    let s = t.summary().unwrap();
    assert!(!s.trigger.unwrap().phase_valid);
    assert_eq!(s.lost_records, 0);
    t.phase(Phase::Commit, 40, c(1));
    t.phase(Phase::Yield, 70, c(1));
    assert_eq!(
        t.summary().unwrap().phase_max_us[Phase::Commit as usize],
        30
    );
}
#[test]
fn contended_overflow_keeps_clock_without_triggering() {
    let t = Trace::new();
    t.arm(0);
    let first = (u32::MAX as u64) * 3 + 5;
    t.with_test_lock(|| assert!(!t.record(e(Kind::QueueOverflow, first, 8))));
    t.freeze(first + 1);
    let s = t.summary().unwrap();
    assert!(!s.triggered && !s.trigger_lost && s.frozen);
    assert!(s.trigger.is_none());
    assert_eq!(s.first_overflow_us, Some(first));
    t.record(e(Kind::QueueOverflow, 9, 9));
    assert_eq!(t.summary().unwrap().first_overflow_us, Some(first));
    assert_eq!((s.queue_overflows, s.lost_records), (1, 1));
}
#[test]
fn completion_includes_recycle_tail_and_returns_idle() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Packet, 10, c(4));
    let mut f = e(Kind::Failure, 20, 4);
    f.received_us = 8;
    t.record(f);
    t.phase(Phase::ErrorAbort, 21, c(4));
    t.phase(Phase::Recycle, 100, c(4));
    let mut done = e(Kind::Complete, 140, 4);
    done.received_us = 8;
    done.consumer_us = 130;
    t.record(done);
    t.freeze(150);
    let f = t.read_failure(0).unwrap();
    assert_eq!(f.consumer_us, Some(130));
    assert_eq!(f.received_us, 8);
    let r = t.read(t.summary().unwrap().len - 1).unwrap();
    assert_eq!(r.phase, Phase::Recycle);
    assert_eq!(r.consumer_us, 130);
    assert_eq!(
        t.summary().unwrap().phase_max_us[Phase::Recycle as usize],
        40
    );
}
#[test]
fn failure_completion_can_arrive_after_ring_freeze() {
    let t = Trace::new();
    t.arm(0);
    let mut f = e(Kind::Failure, 10, 8);
    f.received_us = 2;
    t.record(f);
    auto_freeze(&t, 20);
    assert!(t.read_failure(0).unwrap().consumer_us.is_none());
    let mut done = e(Kind::Complete, 100, 8);
    done.received_us = 2;
    done.consumer_us = 95;
    assert!(!t.record(done));
    assert_eq!(t.read_failure(0).unwrap().consumer_us, Some(95));
    assert_eq!(t.summary().unwrap().len, 18);
}
#[test]
fn tail_requires_received_time_and_cross_frame_context() {
    let t = Trace::new();
    t.arm(0);
    let f = e(Kind::Failure, 10, 8);
    t.record(f);
    let mut done = e(Kind::Complete, 100, 9);
    done.received_us = f.received_us;
    done.consumer_us = 90;
    t.record(done);
    done.context = f.context;
    done.received_us += 1;
    t.record(done);
    auto_freeze(&t, 101);
    assert!(t.read_failure(0).unwrap().consumer_us.is_none());
    done.received_us = f.received_us;
    done.time_us = 200;
    t.record(done);
    assert_eq!(t.read_failure(0).unwrap().consumer_us, Some(90));
}
#[test]
fn ambiguous_pending_duplicates_never_get_made_up_tail() {
    let t = Trace::new();
    t.arm(0);
    let f = e(Kind::Failure, 10, 8);
    t.record(f);
    t.record(f);
    let mut done = e(Kind::Complete, 30, 8);
    done.received_us = f.received_us;
    done.consumer_us = 29;
    t.record(done);
    t.freeze(31);
    assert_eq!(t.summary().unwrap().ambiguous_tails, 2);
    for i in 0..2 {
        let f = t.read_failure(i).unwrap();
        assert!(f.tail_ambiguous && f.consumer_us.is_none());
    }
}
#[test]
fn lost_failure_invalidates_old_uncompleted_tail() {
    let t = Trace::new();
    t.arm(0);
    let f = e(Kind::Failure, 10, 8);
    t.record(f);
    t.with_test_lock(|| assert!(!t.record(f)));
    let mut done = e(Kind::Complete, 30, 8);
    done.received_us = f.received_us;
    done.consumer_us = 29;
    t.record(done);
    t.freeze(31);
    assert_eq!(t.summary().unwrap().lost_failures, 1);
    assert!(t.read_failure(0).unwrap().tail_ambiguous);
    assert!(t.read_failure(0).unwrap().consumer_us.is_none());
}
#[test]
fn failure_capacity_loss_also_invalidates_pending_tail() {
    let t = Trace::new();
    t.arm(0);
    let first = e(Kind::Failure, 10, 8);
    t.record(first);
    for i in 1..32 {
        t.record(e(Kind::Failure, 10 + i, 8 + i as u32));
    }
    t.record(first);
    let mut done = e(Kind::Complete, 100, 8);
    done.received_us = first.received_us;
    done.consumer_us = 95;
    t.record(done);
    t.freeze(101);
    assert_eq!(t.summary().unwrap().failure_overflow, 1);
    assert_eq!(t.summary().unwrap().failure_len, 32);
    assert!(t.read_failure(0).unwrap().tail_ambiguous);
    assert!(t.read_failure(0).unwrap().consumer_us.is_none());
}
#[test]
fn u32_sequence_boundary_retains_stable_full_sequence() {
    let t = Trace::new();
    t.arm(0);
    t.test_set_sequence(u32::MAX as u64 - 1);
    t.record(e(Kind::Enqueue, 1, 1));
    t.record(e(Kind::Enqueue, 2, 2));
    t.freeze(3);
    assert_eq!(t.read(0).unwrap().sequence, u32::MAX as u64);
    assert_eq!(t.read(1).unwrap().sequence, u32::MAX as u64 + 1);
}
#[test]
fn duration_clipping_is_explicit_and_positions_full_width() {
    let t = Trace::new();
    t.arm(0);
    let mut x = e(Kind::Complete, u64::MAX, u32::MAX);
    x.context.incoming.offset = u32::MAX;
    x.context.queued = u32::MAX;
    x.consumer_us = u64::MAX;
    x.lock_us = u64::MAX;
    t.record(x);
    t.freeze(u64::MAX);
    let r = t.read(0).unwrap();
    assert_eq!(r.time_us, u64::MAX);
    assert_eq!(r.context.incoming.frame, u32::MAX);
    assert_eq!(r.context.incoming.offset, u32::MAX);
    assert!(!r.context.queue_valid);
    assert!(r.duration_clipped);
    assert_eq!(r.consumer_us, u32::MAX as u64);
}

#[test]
fn manual_seal_stops_all_exported_updates_and_rearm_resets() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Lock, 1, c(1));
    auto_freeze(&t, 2);
    assert!(t.freeze(30));
    let before = format!("{:?}", t.summary().unwrap());
    for kind in [
        Kind::Phase,
        Kind::QueueOverflow,
        Kind::Failure,
        Kind::Complete,
    ] {
        let mut x = e(kind, 40, 8);
        x.phase = Phase::Qspi;
        t.record(x);
    }
    assert_eq!(before, format!("{:?}", t.summary().unwrap()));
    assert!(!t.summary().unwrap().armed);
    assert!(t.arm(50));
    assert_eq!(t.summary().unwrap().queue_overflows, 0);
}
#[test]
fn pending_writer_prevents_successful_seal_and_export() {
    let t = Trace::new();
    t.arm(0);
    t.with_test_writer(|| {
        assert!(!t.freeze(1));
        assert!(t.summary().is_none());
        assert!(!t.record(e(Kind::QueueOverflow, 2, 8)));
    });
    assert!(t.freeze(3));
    assert_eq!(t.summary().unwrap().queue_overflows, 0);
}
#[test]
fn actual_other_thread_contention_is_nonblocking_and_counted() {
    use std::sync::{Arc, Barrier};
    let t = Arc::new(Trace::new());
    t.arm(0);
    let held = Arc::new(Barrier::new(2));
    let released = Arc::new(Barrier::new(2));
    let peer = t.clone();
    let h = held.clone();
    let r = released.clone();
    let thread = std::thread::spawn(move || {
        peer.with_test_lock(|| {
            h.wait();
            r.wait();
        })
    });
    held.wait();
    assert!(!t.record(e(Kind::Enqueue, 1, 1)));
    released.wait();
    thread.join().unwrap();
    assert_eq!(t.summary().unwrap().lost_records, 1);
}

#[test]
fn first_sequence_trigger_preserves_prehistory_and_complete_without_overflow() {
    let t = Trace::new();
    t.arm(0);
    for i in 0..120 {
        t.record(e(Kind::Enqueue, i, 2007000));
    }
    t.phase(Phase::Packet, 120, c(2007061));
    let mut f = e(Kind::Failure, 130, 2007061);
    f.detail = 64;
    f.received_us = 110;
    assert!(t.record(f));
    assert!(t.summary().unwrap().triggered);
    for i in 0..500 {
        assert!(t.phase(Phase::Log, 131 + i, c(2007061)));
    }
    assert_eq!(t.summary().unwrap().post_remaining, 16);
    let mut done = e(Kind::Complete, 700, 2007061);
    done.received_us = 110;
    done.consumer_us = 580;
    done.lock_us = 31;
    done.qspi_us = 71;
    assert!(t.record(done));
    for i in 0..15 {
        t.record(e(Kind::Enqueue, 701 + i, 2007062));
    }
    let s = t.summary().unwrap();
    assert!(s.frozen);
    assert_eq!(s.len, 96);
    assert_eq!(s.queue_overflows, 0);
    assert_eq!(s.first_overflow_us, None);
    assert_eq!(s.trigger.unwrap().context.incoming.frame, 2007061);
    assert_eq!(s.trigger.unwrap().phase, Phase::Packet);
    assert_eq!(s.first_sequence, Some(42));
    assert!(t.freeze(1000));
    let records: Vec<_> = (0..96).map(|i| t.read(i).unwrap()).collect();
    assert!(records.iter().all(|r| r.kind != Kind::Phase));
    let done = records.iter().find(|r| r.kind == Kind::Complete).unwrap();
    assert_eq!(
        (done.consumer_us, done.lock_us, done.qspi_us),
        (580, 31, 71)
    );
    assert_eq!(t.read_failure(0).unwrap().consumer_us, Some(580));
}
#[test]
fn every_sequence_reason_triggers_but_other_failure_classes_do_not() {
    for bit in 0..15 {
        let t = Trace::new();
        t.arm(0);
        let mut f = e(Kind::Failure, 1, 1);
        f.detail = 1 << bit;
        t.record(f);
        let s = t.summary().unwrap();
        assert_eq!(s.triggered, bit <= 8 || bit == 12, "bit {bit}");
    }
}
#[test]
fn lost_first_sequence_is_explicit_and_overflow_clock_still_independent() {
    let t = Trace::new();
    t.arm(0);
    let mut f = e(Kind::Failure, 10, 8);
    f.detail = 128;
    t.with_test_lock(|| assert!(!t.record(f)));
    t.record(e(Kind::Dequeue, 11, 9));
    let s = t.summary().unwrap();
    assert!(s.triggered && s.trigger_lost);
    assert!(s.trigger.is_none());
    assert_eq!((s.lost_records, s.lost_failures), (1, 1));
    let when = (1u64 << 40) + 15;
    t.with_test_lock(|| assert!(!t.record(e(Kind::QueueOverflow, when, 10))));
    assert_eq!(t.summary().unwrap().first_overflow_us, Some(when));
}
#[test]
fn routine_phase_never_floods_ring_or_consumes_posthistory() {
    let t = Trace::new();
    t.arm(0);
    for i in 0..10000 {
        t.phase(Phase::Maintenance, i, Context::UNKNOWN);
    }
    let s = t.summary().unwrap();
    assert_eq!(
        (s.recorded, s.len, s.lost_records, s.lost_phase),
        (0, 0, 0, 0)
    );
    let mut f = e(Kind::Failure, 10001, 1);
    f.detail = 1 << 12;
    t.record(f);
    for i in 0..10000 {
        t.phase(Phase::Idle, 10002 + i, Context::UNKNOWN);
    }
    let s = t.summary().unwrap();
    assert_eq!((s.recorded, s.post_remaining), (1, 16));
}
#[test]
fn full_width_phase_maximum_and_concurrent_phase_writer_failure_are_explicit() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Access, 1, c(1));
    t.phase(Phase::Commit, (1u64 << 40) + 2, c(1));
    assert_eq!(
        t.summary().unwrap().phase_max_us[Phase::Access as usize],
        (1u64 << 40) + 1
    );
    t.with_test_phase_publication(|| assert!(!t.phase(Phase::Log, (1u64 << 40) + 3, c(1))));
    assert_eq!(t.summary().unwrap().lost_phase, 1);
    assert!(!t.summary().unwrap().counters_valid);
}

#[test]
fn background_transfer_is_salient_with_metrics_but_never_triggers() {
    let t = Trace::new();
    t.arm(0);
    let mut transfer = Event::new(Kind::Transfer, 10, Context::UNKNOWN);
    transfer.lock_us = 23;
    transfer.qspi_us = 67;
    transfer.detail = 64;
    assert!(t.record(transfer));
    assert!(!t.summary().unwrap().triggered);
    let mut failure = e(Kind::Failure, 20, 1);
    failure.detail = 64;
    t.record(failure);
    transfer.time_us = 21;
    assert!(t.record(transfer));
    assert_eq!(t.summary().unwrap().post_remaining, 15);
    for i in 0..15 {
        t.record(e(Kind::Enqueue, 22 + i, 2));
    }
    assert!(t.freeze(50));
    let a = t.read(0).unwrap();
    let b = t.read(2).unwrap();
    for r in [a, b] {
        assert_eq!(r.kind, Kind::Transfer);
        assert_eq!(r.context, Context::UNKNOWN);
        assert_eq!((r.lock_us, r.qspi_us), (23, 67));
    }
    assert_eq!(
        t.summary().unwrap().trigger.unwrap().context.incoming.frame,
        1
    );
}

#[test]
fn repeated_manual_freeze_is_idempotent_including_all_summary_fields() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Access, 10, c(1));
    let mut f = e(Kind::Failure, 20, 1);
    f.detail = 64;
    t.record(f);
    assert!(t.freeze(30));
    let before = format!("{:?}", t.summary().unwrap());
    assert!(t.freeze(3000000));
    assert_eq!(format!("{:?}", t.summary().unwrap()), before);
    assert!(t.freeze(u64::MAX));
    assert_eq!(format!("{:?}", t.summary().unwrap()), before);
}

#[test]
fn failed_manual_seal_after_auto_freeze_still_closes_phase_on_retry() {
    let t = Trace::new();
    t.arm(0);
    auto_freeze(&t, 1);
    t.phase(Phase::Access, 30, c(1));
    t.with_test_writer(|| assert!(!t.freeze(40)));
    assert!(t.freeze(60));
    assert_eq!(
        t.summary().unwrap().phase_max_us[Phase::Access as usize],
        30
    );
    let before = format!("{:?}", t.summary().unwrap());
    assert!(t.freeze(600));
    assert_eq!(format!("{:?}", t.summary().unwrap()), before);
}

#[test]
fn rearm_disarms_and_waits_for_already_admitted_phase_writer() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Maintenance, 10, Context::UNKNOWN);
    t.record(e(Kind::Enqueue, 11, 1));
    t.with_test_writer(|| {
        assert!(!t.arm(20));
        assert!(t.summary().is_none());
        assert!(!t.phase(Phase::Access, 21, c(1)));
    });
    assert!(!t.summary().unwrap().armed);
    assert_eq!(t.summary().unwrap().epoch, 1);
    assert_eq!(t.summary().unwrap().len, 1);
    assert!(t.arm(30));
    let s = t.summary().unwrap();
    assert_eq!((s.epoch, s.len, s.recorded), (2, 0, 0));
    assert_eq!(s.phase_max_us, [0; PHASE_COUNT]);
    assert!(t.phase(Phase::Access, 31, c(2)));
    assert!(t.freeze(40));
    assert_eq!(t.summary().unwrap().phase_max_us[Phase::Access as usize], 9);
}

#[test]
fn registered_call_before_first_armed_lookup_cannot_cross_rearm_boundary() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Maintenance, 5, Context::UNKNOWN);
    let mut phase = e(Kind::Phase, 10, 1);
    phase.phase = Phase::Access;
    assert!(!t.test_record_before_first_armed_lookup(phase, || {
        // This actual record call is paused before its first armed lookup.
        // Rearm must fail its drain check; it cannot reset/re-enable capture.
        assert!(!t.arm(20));
        assert!(t.summary().is_none());
    }));
    assert_eq!(t.summary().unwrap().epoch, 1);
    assert!(t.arm(30));
    let s = t.summary().unwrap();
    assert_eq!(s.epoch, 2);
    assert_eq!(s.phase_max_us, [0; PHASE_COUNT]);
    t.phase(Phase::Qspi, 31, c(2));
    t.freeze(35);
    assert_eq!(t.summary().unwrap().phase_max_us[Phase::Access as usize], 0);
    assert_eq!(t.summary().unwrap().phase_max_us[Phase::Qspi as usize], 4);
}

#[test]
fn salient_record_and_phase_paths_never_collect_global_maxima() {
    let t = Trace::new();
    t.arm(0);
    let before = Trace::test_maxima_snapshot_calls();
    for i in 0..200 {
        t.phase(Phase::Qspi, 10 * i, c(1));
        t.phase(Phase::Access, 10 * i + 3, c(1));
        t.record(e(Kind::Enqueue, 10 * i + 4, 1));
        t.record(e(Kind::Complete, 10 * i + 5, 1));
    }
    assert_eq!(Trace::test_maxima_snapshot_calls(), before);
    let s = t.summary().unwrap();
    assert_eq!(s.phase_max_us[Phase::Qspi as usize], 3);
    assert_eq!(Trace::test_maxima_snapshot_calls(), before + 1);
    assert!(t.freeze(3000));
    assert!(Trace::test_maxima_snapshot_calls() > before + 1);
}

#[test]
fn loss_localization_counts_each_rejected_salient_kind_and_resets() {
    let t = Trace::new();
    t.arm(0);
    let kinds = [
        Kind::Enqueue,
        Kind::Dequeue,
        Kind::QueueOverflow,
        Kind::Failure,
        Kind::Recycle,
        Kind::Complete,
        Kind::Transfer,
    ];
    t.with_test_lock(|| {
        for kind in kinds {
            assert!(!t.record(e(kind, 10, 1)));
        }
        // Phase never contends for State and must not inflate rejected counts.
        assert!(t.phase(Phase::Qspi, 11, c(1)));
        assert!(t.loss_counts().is_none());
    });
    assert!(t.freeze(20));
    let counts = t.loss_counts().unwrap();
    assert_eq!(counts.counts, [1, 1, 0, 1, 1, 1, 1, 1]);
    assert_eq!(
        counts.counts.iter().sum::<u64>(),
        t.summary().unwrap().lost_records
    );
    assert!(counts.counters_valid);
    assert!(!t.record(e(Kind::Complete, 21, 1)));
    assert_eq!(t.loss_counts().unwrap(), counts);
    assert!(t.freeze(100));
    assert_eq!(t.loss_counts().unwrap(), counts);
    assert!(t.arm(101));
    assert_eq!(t.loss_counts().unwrap().counts, [0; 8]);
    assert_eq!(t.loss_counts().unwrap().epoch, counts.epoch + 1);
}

#[test]
fn manual_seal_saves_coherent_maxima_for_unavailable_snapshot_fallback() {
    let t = Trace::new();
    t.arm(0);
    t.phase(Phase::Qspi, 10, c(1));
    t.phase(Phase::Access, 25, c(1));
    assert!(t.freeze(40));
    let before = t.summary().unwrap().phase_max_us;
    assert_eq!(before[Phase::Qspi as usize], 15);
    assert_eq!(before[Phase::Access as usize], 15);
    t.with_test_phase_publication(|| {
        // No coherent global atomic-max snapshot available: exported fallback
        // must retain exactly the maxima saved by the successful manual seal.
        assert_eq!(t.summary().unwrap().phase_max_us, before);
        assert!(t.freeze(4000));
        assert_eq!(t.summary().unwrap().phase_max_us, before);
    });
    assert_eq!(t.summary().unwrap().phase_max_us, before);
}
