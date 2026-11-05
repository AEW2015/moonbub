#[path = "../handheld/src/streaming/audio_io.rs"]
mod io;
use io::{Bus, Feeder, Phase, ResultEvent as E};
#[derive(Default)]
struct Fake {
    session: u32,
    seq: u32,
    crc: u32,
    count: u32,
    staging: bool,
    queued: u32,
    armed: bool,
    calls: usize,
    fail: Option<usize>,
    ambiguous: bool,
    writes: Vec<(u32, u32)>,
    data: usize,
    receipt_bad: u8,
    last_result: u32,
}
impl Fake {
    fn action(&mut self) -> Result<(), ()> {
        self.calls += 1;
        if self.fail == Some(self.calls) {
            Err(())
        } else {
            Ok(())
        }
    }
}
impl Bus for Fake {
    fn read(&mut self, o: u32) -> Result<u32, ()> {
        self.action()?;
        Ok(match o {
            0 => 0x4d425631,
            4 => 0x00010000,
            0x184 => io::BUILD,
            0x300 => io::MAGIC,
            0x304 => io::SCHEMA,
            0x30c => {
                1 | if self.staging { 2 } else { 0 }
                    | (self.last_result << 8)
                    | if self.last_result == 3 { 64 } else { 0 }
            }
            0x320 => 8 - self.queued,
            0x324 => {
                self.count
                    + if self.receipt_bad == 3 && self.calls > 12 {
                        1
                    } else {
                        0
                    }
            }
            0x328 => self.seq + if self.receipt_bad == 1 { 1 } else { 0 },
            0x32c => self.session + if self.receipt_bad == 2 { 1 } else { 0 },
            _ => panic!("read{o:x}"),
        })
    }
    fn write(&mut self, o: u32, v: u32) -> Result<(), ()> {
        let result = self.action();
        if result.is_err() && !(self.ambiguous && o == 0x308 && v == 3) {
            return result;
        }
        self.writes.push((o, v));
        match o {
            0x31c => self.session = v,
            0x310 => assert_eq!(v, 505),
            0x314 => self.seq = v,
            0x318 => self.crc = v,
            0x308 => match v {
                0 => {
                    self.queued = 0;
                    self.staging = false;
                    self.armed = false;
                    self.last_result = 5;
                }
                1 => {
                    self.armed = true;
                    self.last_result = 1;
                }
                2 => {
                    assert!(!self.staging);
                    self.staging = true;
                    self.data = 0;
                    self.last_result = 2;
                }
                3 => {
                    assert!(self.staging);
                    assert_eq!(self.data, 2020);
                    self.staging = false;
                    self.count = self.count.wrapping_add(1);
                    self.queued += 1;
                    self.last_result = 3;
                }
                _ => panic!(),
            },
            _ => panic!("write{o:x}"),
        }
        result
    }
    fn pcm(&mut self, p: &[u8]) -> Result<(), ()> {
        self.action()?;
        assert!(self.staging);
        self.data = p.len();
        Ok(())
    }
}
fn drain(f: &mut Feeder, b: &mut Fake) -> E {
    for _ in 0..40 {
        let e = f.step(b, &[0; 2020]);
        if e != E::None {
            return e;
        }
    }
    panic!("unbounded");
}
fn ready() -> (Feeder, Fake) {
    let mut f = Feeder::new();
    let mut b = Fake::default();
    f.start(123);
    assert_eq!(drain(&mut f, &mut b), E::Online);
    (f, b)
}
#[test]
fn whole_block_receipt_and_two_block_arm() {
    let (mut f, mut b) = ready();
    assert!(f.submit(0, 45));
    assert_eq!(drain(&mut f, &mut b), E::Committed);
    assert!(!b.armed);
    assert!(f.submit(1, 46));
    assert_eq!(drain(&mut f, &mut b), E::Committed);
    assert_eq!(f.phase, Phase::Arm);
    assert_eq!(f.step(&mut b, &[0; 2020]), E::Armed);
    assert!(b.armed);
    assert_eq!(b.queued, 2);
    assert_eq!(f.blocks, 2);
}
#[test]
fn full_rejects_before_begin_without_flushing() {
    let (mut f, mut b) = ready();
    b.queued = 8;
    let writes = b.writes.len();
    assert!(f.submit(0, 0));
    assert_eq!(drain(&mut f, &mut b), E::Rejected);
    assert_eq!(b.queued, 8);
    assert_eq!(writes, b.writes.len());
    assert_eq!(f.phase, Phase::Idle);
}
#[test]
fn every_packet_io_fault_cannot_publish_unconfirmed() {
    let (mut reference, mut good) = ready();
    reference.submit(0, 1);
    let start = good.calls;
    assert_eq!(drain(&mut reference, &mut good), E::Committed);
    let count = good.calls - start;
    for action in 1..=count {
        let (mut f, mut b) = ready();
        b.fail = Some(b.calls + action);
        f.submit(0, 1);
        let event = drain(&mut f, &mut b);
        assert_eq!(event, E::Fault, "fault{action}");
        assert_ne!(f.phase, Phase::Idle);
    }
}
#[test]
fn ambiguous_commit_resolves_exact_receipt_without_replay() {
    let (mut f, mut b) = ready();
    f.submit(3, 0);
    while f.phase != Phase::Commit {
        assert_eq!(f.step(&mut b, &[0; 2020]), E::None)
    }
    b.fail = Some(b.calls + 1);
    b.ambiguous = true;
    assert_eq!(drain(&mut f, &mut b), E::Committed);
    assert_eq!(b.writes.iter().filter(|x| **x == (0x308, 3)).count(), 1);
    assert_eq!(b.count, 1);
}
#[test]
fn wrong_receipts_fail() {
    for kind in 1..=3 {
        let (mut f, mut b) = ready();
        b.receipt_bad = kind;
        f.submit(3, 0);
        assert_eq!(drain(&mut f, &mut b), E::Fault, "receipt{kind}");
    }
}
#[test]
fn cancellation_every_phase_stops_before_any_further_commit() {
    for cancel_at in 0..16 {
        let (mut f, mut b) = ready();
        f.submit(0, 0);
        for _ in 0..cancel_at {
            let _ = f.step(&mut b, &[0; 2020]);
        }
        let prior = b.writes.iter().filter(|x| **x == (0x308, 3)).count();
        f.stop();
        assert_eq!(drain(&mut f, &mut b), E::Stopped);
        assert_eq!(b.queued, 0);
        assert!(!b.staging);
        assert!(!b.armed);
        assert_eq!(b.writes.iter().filter(|x| **x == (0x308, 3)).count(), prior);
    }
}
#[test]
fn count_wrap_is_exact_not_stale() {
    let (mut f, mut b) = ready();
    b.count = u32::MAX;
    f.submit(0, 0);
    assert_eq!(drain(&mut f, &mut b), E::Committed);
    assert_eq!(b.count, 0);
}
#[test]
fn stop_fault_is_not_clean_completion() {
    let (mut f, mut b) = ready();
    f.stop();
    b.fail = Some(b.calls + 1);
    assert_eq!(drain(&mut f, &mut b), E::Fault);
    assert!(!f.active);
}
#[test]
fn session_change_flushes_old_audio_before_setting_new_identity() {
    let (mut f, mut b) = ready();
    f.submit(0, 0);
    drain(&mut f, &mut b);
    let old = b.count;
    f.start(999);
    assert_eq!(drain(&mut f, &mut b), E::Online);
    assert_eq!(b.queued, 0);
    assert_eq!(b.session, 999);
    assert_eq!(b.count, old);
    assert!(f.submit(0, 0));
    assert_eq!(drain(&mut f, &mut b), E::Committed);
}
#[test]
fn full_u32_sequence_and_no_double_submission() {
    let (mut f, mut b) = ready();
    assert!(f.submit(u32::MAX, 0));
    assert!(!f.submit(1, 0));
    assert_eq!(drain(&mut f, &mut b), E::Committed);
    assert!(f.submit(0, 0));
    assert_eq!(drain(&mut f, &mut b), E::Committed);
}

#[test]
fn generation_cancellation_has_no_bus_actions() {
    let (mut f, mut b) = ready();
    f.submit(0, 0);
    let n = b.calls;
    assert_eq!(
        io::checked_step(&mut f, &mut b, &[0; 2020], false, false, 7, 7),
        E::None
    );
    assert_eq!(b.calls, n);
    f.stop();
    assert_eq!(
        io::checked_step(&mut f, &mut b, &[0; 2020], false, true, 7, 7),
        E::None
    );
    assert_eq!(f.phase, Phase::WaitStop);
}
#[test]
fn changed_configuration_epoch_fails_before_every_action() {
    struct Bad {
        writes: usize,
        fail: u32,
    }
    impl Bus for Bad {
        fn read(&mut self, o: u32) -> Result<u32, ()> {
            Ok(match o {
                0 => 0x4d425631,
                4 => 0x10000,
                0x184 => {
                    if self.fail == 0 {
                        0x4d424f49
                    } else {
                        io::BUILD
                    }
                }
                0x300 => {
                    if self.fail == 1 {
                        0
                    } else {
                        io::MAGIC
                    }
                }
                0x304 => 0,
                _ => 0,
            })
        }
        fn write(&mut self, _: u32, _: u32) -> Result<(), ()> {
            self.writes += 1;
            Ok(())
        }
        fn pcm(&mut self, _: &[u8]) -> Result<(), ()> {
            self.writes += 1;
            Ok(())
        }
    }
    for phase in [
        Phase::Stop,
        Phase::Frames,
        Phase::Begin,
        Phase::Pcm,
        Phase::Commit,
        Phase::Arm,
    ] {
        for fail in 0..3 {
            let mut f = Feeder::new();
            f.phase = phase;
            let mut b = Bad { writes: 0, fail };
            assert_eq!(
                io::checked_step(&mut f, &mut b, &[0; 2020], true, false, 7, 8),
                E::Fault
            );
            assert_eq!(b.writes, 0);
        }
    }
}

#[test]
fn failed_start_identity_is_fenced_before_stop_write() {
    let (mut f, mut b) = ready();
    f.stop();
    b.fail = Some(b.calls + 1);
    let writes = b.writes.len();
    assert_eq!(
        io::checked_step(&mut f, &mut b, &[0; 2020], true, false, 4, 4),
        E::Fault
    );
    assert_eq!(b.writes.len(), writes);
}

#[test]
fn block_dispositions_count_control_faults_zero_and_each_pending_once() {
    let (mut a, mut r) = (0, 0);
    let mut pending = None;
    assert_eq!(io::settle_block(&mut pending, &mut a, &mut r, false), None);
    assert_eq!((a, r), (0, 0));
    for reason in ["fault", "timeout", "idle", "cancel", "stop", "ambiguous"] {
        pending = Some(0);
        assert_eq!(
            io::settle_block(&mut pending, &mut a, &mut r, false),
            Some(0),
            "{reason}"
        );
        let prior = r;
        assert_eq!(io::settle_block(&mut pending, &mut a, &mut r, false), None);
        assert_eq!(r, prior);
    }
    assert_eq!((a, r), (0, 6));
    pending = Some(u32::MAX);
    assert_eq!(
        io::settle_block(&mut pending, &mut a, &mut r, true),
        Some(u32::MAX)
    );
    assert_eq!((a, r), (1, 6));
    assert_eq!(io::settle_block(&mut pending, &mut a, &mut r, false), None);
    assert_eq!((a, r), (1, 6));
}

#[test]
fn arm_control_fault_does_not_reject_already_confirmed_block() {
    let (mut f, mut b) = ready();
    let (mut accepted, mut rejected) = (0, 0);
    for seq in [0, 1] {
        let mut pending = Some(seq);
        assert!(f.submit(seq, 0));
        assert_eq!(drain(&mut f, &mut b), E::Committed);
        assert_eq!(
            io::settle_block(&mut pending, &mut accepted, &mut rejected, true),
            Some(seq)
        );
        if seq == 1 {
            assert_eq!(f.phase, Phase::Arm);
            b.fail = Some(b.calls + 1);
            assert_eq!(f.step(&mut b, &[0; 2020]), E::Fault);
            assert_eq!(
                io::settle_block(&mut pending, &mut accepted, &mut rejected, false),
                None
            );
        }
    }
    assert_eq!((accepted, rejected), (2, 0));
}
