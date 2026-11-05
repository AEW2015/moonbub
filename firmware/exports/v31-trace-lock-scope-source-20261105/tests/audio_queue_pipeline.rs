#![allow(dead_code)]
#[path = "../handheld/src/streaming/service_policy.rs"]
mod service_policy;

#[path = "../handheld/src/streaming/audio_io.rs"]
mod audio_io;
#[path = "../handheld/src/streaming/av_session.rs"]
mod av_session;
#[path = "../handheld/src/streaming/av_wire.rs"]
mod av_wire;
#[path = "../handheld/src/streaming/audio_diag.rs"]
mod diag;
#[path = "../handheld/src/streaming/protocol.rs"]
mod protocol;
#[path = "../handheld/src/streaming/compressed_queue.rs"]
mod q;
use audio_io::{Bus, Feeder, Phase, ResultEvent as E};
#[derive(Default)]
struct Backend {
    session: u32,
    seq: u32,
    commits: u32,
    result: u32,
    staging: bool,
    queued: u32,
    pcm_writes: u32,
}
impl Bus for Backend {
    fn read(&mut self, o: u32) -> Result<u32, ()> {
        Ok(match o {
            0x30c => {
                1 | (self.result << 8)
                    | if self.staging { 2 } else { 0 }
                    | if self.result == 3 { 64 } else { 0 }
            }
            0x320 => 8 - self.queued,
            0x324 => self.commits,
            0x328 => self.seq,
            0x32c => self.session,
            _ => panic!(),
        })
    }
    fn write(&mut self, o: u32, v: u32) -> Result<(), ()> {
        match o {
            0x31c => self.session = v,
            0x310 | 0x318 => {}
            0x314 => self.seq = v,
            0x308 => match v {
                0 => {
                    self.queued = 0;
                    self.staging = false;
                    self.result = 5;
                }
                1 => self.result = 1,
                2 => {
                    self.staging = true;
                    self.result = 2;
                }
                3 => {
                    assert!(self.staging);
                    self.staging = false;
                    self.commits = self.commits.wrapping_add(1);
                    self.result = 3;
                    self.queued += 1;
                }
                _ => panic!(),
            },
            _ => panic!(),
        }
        Ok(())
    }
    fn pcm(&mut self, data: &[u8]) -> Result<(), ()> {
        assert_eq!(data.len(), 2020);
        assert!(self.staging);
        self.pcm_writes += 1;
        Ok(())
    }
}
fn ready() -> (Feeder, Backend) {
    let (mut f, mut b) = (Feeder::new(), Backend::default());
    f.start(9);
    for _ in 0..4 {
        if f.step(&mut b, &[0; 2020]) == E::Online {
            return (f, b);
        }
    }
    panic!()
}
#[test]
fn fifteen_ms_bus_stall_retains_second_audio_packet() {
    let (mut f, mut b) = ready();
    let mut queue = q::Queue::new();
    let mut bytes = vec![0; q::STORAGE_BYTES];
    let mut pending = None;
    let (mut accepted, mut rejected) = (0, 0);
    let mut next = 0;
    for now in (0..50_000u64).step_by(1000) {
        if next < 4 && now >= next * 10_457 {
            assert!(queue
                .push(
                    q::Meta {
                        session: 9,
                        sequence: next as u32,
                        arrival_us: now
                    },
                    &[next as u8; 512],
                    &mut bytes
                )
                .unwrap()
                .is_none());
            next += 1;
        }
        assert!(!queue.stale(now));
        if f.phase == Phase::Idle && f.active && pending.is_none() {
            if let Some(m) = queue.pop() {
                assert!(f.submit(m.sequence, 0));
                pending = Some(m.sequence);
            }
        }
        for _ in 0..20 {
            if now < 15_000 {
                break;
            }
            if f.phase == Phase::Idle {
                break;
            }
            match f.step(&mut b, &[0; 2020]) {
                E::Committed => {
                    audio_io::settle_block(&mut pending, &mut accepted, &mut rejected, true);
                }
                E::Armed | E::None => {}
                e => panic!("{e:?}"),
            }
        }
        b.queued = 0;
    }
    assert_eq!((accepted, rejected), (4, 0));
    assert!(queue.high_water >= 1);
    assert_eq!(b.pcm_writes, 4);
}
#[test]
fn bounded_burst_records_first_and_last_evicted_sequences() {
    let mut queue = q::Queue::new();
    let mut bytes = vec![0; q::STORAGE_BYTES];
    let mut d = diag::Diagnostics::new();
    for seq in 0..10 {
        if let Some(old) = queue
            .push(
                q::Meta {
                    session: 9,
                    sequence: seq,
                    arrival_us: 0,
                },
                &[seq as u8; 512],
                &mut bytes,
            )
            .unwrap()
        {
            d.drop_block(old.sequence, diag::Reason::QueueFull, Phase::Pcm, 0, 4);
        }
    }
    assert_eq!(queue.len(), 4);
    assert_eq!(d.first.unwrap().sequence, 0);
    assert_eq!(d.last.unwrap().sequence, 5);
    assert_eq!(d.drops[diag::Reason::QueueFull as usize], 6);
    for seq in 6..10 {
        assert_eq!(queue.pop().unwrap().sequence, seq);
    }
}
#[test]
fn stale_queue_never_overwrites_or_replays_pending_pcm() {
    let (mut f, mut b) = ready();
    f.submit(42, 0);
    let mut queue = q::Queue::new();
    let mut bytes = vec![0; q::STORAGE_BYTES];
    for seq in [43, 44] {
        queue
            .push(
                q::Meta {
                    session: 9,
                    sequence: seq,
                    arrival_us: 0,
                },
                &[0; 512],
                &mut bytes,
            )
            .unwrap();
    }
    let mut d = diag::Diagnostics::new();
    while queue.stale(32_000) {
        let old = queue.pop().unwrap();
        d.drop_block(
            old.sequence,
            diag::Reason::QueueAge,
            f.phase,
            32_000,
            queue.len() + 1,
        );
    }
    assert_eq!(d.first.unwrap().sequence, 43);
    assert_eq!(d.last.unwrap().sequence, 44);
    for _ in 0..20 {
        if f.step(&mut b, &[0; 2020]) == E::Committed {
            break;
        }
    }
    assert_eq!(b.seq, 42);
    assert_eq!(b.pcm_writes, 1);
    assert_eq!(queue.len(), 0);
}
#[test]
fn cancelled_source_flushes_four_compressed_and_one_unpublished_pcm() {
    let (mut f, mut b) = ready();
    f.submit(7, 0);
    let mut queue = q::Queue::new();
    let mut bytes = vec![0; q::STORAGE_BYTES];
    for seq in 8..12 {
        queue
            .push(
                q::Meta {
                    session: 9,
                    sequence: seq,
                    arrival_us: 0,
                },
                &[0; 512],
                &mut bytes,
            )
            .unwrap();
    }
    let (mut count, mut accepted, mut rejected) = (0, 0, 0);
    while queue.pop().is_some() {
        count += 1;
    }
    let mut pending = Some(7);
    audio_io::settle_block(&mut pending, &mut accepted, &mut rejected, false);
    f.stop();
    for _ in 0..5 {
        if f.step(&mut b, &[0; 2020]) == E::Stopped {
            break;
        }
    }
    assert_eq!((count, accepted, rejected), (4, 0, 1));
    assert_eq!(b.pcm_writes, 0);
    assert!(!b.staging);
}
#[test]
fn independent_input_and_keepalive_continue_during_lock_stall() {
    use av_wire::{Kind, Packet};
    let p = |kind, cookie, sequence, payload| Packet {
        kind,
        cookie,
        sequence,
        flags: 0,
        timestamp: 0,
        payload,
    };
    let mut session = av_session::Session::new();
    session.receive(p(Kind::Hello, 1, 0, &[]), 5, 0, 99);
    let nonce = 1u64.to_be_bytes();
    session.receive(p(Kind::Start, 99, 1, &nonce), 5, 1, 0);
    let mut inputs = 0;
    for t in (0..100_000).step_by(1000) {
        assert!(!session.expire(t));
        if t % 20_000 == 0 {
            assert_eq!(session.next_input().unwrap().1, inputs);
            inputs += 1;
        }
    }
    assert_eq!(inputs, 5);
    assert!(session.expire(500_001));
}
#[test]
fn diagnostic_and_ring_metadata_are_small_no_pcm_or_payload_inline() {
    assert!(std::mem::size_of::<q::Queue>() <= 160);
    assert!(std::mem::size_of::<diag::Diagnostics>() <= 512);
    assert!(std::mem::size_of::<diag::DropRecord>() <= 48);
    assert_eq!(q::STORAGE_BYTES, 2048);
}
