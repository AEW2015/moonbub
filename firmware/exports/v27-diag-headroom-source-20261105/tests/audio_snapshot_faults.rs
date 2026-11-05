#![allow(dead_code)]
#[path = "../handheld/src/streaming/service_policy.rs"]
mod service_policy;

#[path = "../handheld/src/streaming/audio_diag.rs"]
mod audio_diag;
#[path = "../handheld/src/streaming/audio_io.rs"]
mod audio_io;
#[path = "../handheld/src/streaming/audio_snapshot.rs"]
mod snapshot;
use audio_diag::SnapshotFailure as F;
use audio_io::Bus;
struct Fake {
    reads: usize,
    fail: Option<usize>,
    before: u32,
    after: u32,
    queued: u32,
    build: u32,
    magic: u32,
    schema: u32,
}
impl Default for Fake {
    fn default() -> Self {
        Self {
            reads: 0,
            fail: None,
            before: 1,
            after: 1,
            queued: 1010,
            build: audio_io::BUILD,
            magic: audio_io::MAGIC,
            schema: audio_io::SCHEMA,
        }
    }
}
impl Bus for Fake {
    fn read(&mut self, o: u32) -> Result<u32, ()> {
        let stage = self.reads;
        self.reads += 1;
        if self.fail == Some(stage) {
            return Err(());
        }
        Ok(match o {
            0 => 0x4d425631,
            4 => 0x10000,
            0x184 => self.build,
            0x300 => self.magic,
            0x304 => self.schema,
            0x30c => {
                if stage == 5 {
                    self.before
                } else {
                    self.after
                }
            }
            0x348 => self.queued,
            0x334 => u32::MAX,
            0x338 => 45,
            _ => panic!(),
        })
    }
    fn write(&mut self, _: u32, _: u32) -> Result<(), ()> {
        panic!("snapshot must not write")
    }
    fn pcm(&mut self, _: &[u8]) -> Result<(), ()> {
        panic!()
    }
}
#[test]
fn actual_every_read_stage_io_is_exact() {
    for stage in 0..10 {
        let mut b = Fake {
            fail: Some(stage),
            ..Default::default()
        };
        let result = snapshot::read(&mut b);
        assert_eq!(result.values, Err(F::Io(stage as u8)));
        assert_eq!(b.reads, stage + 1);
    }
}
#[test]
fn actual_valid_reads_full_boundaries_without_writes() {
    for queued in [0, 4096] {
        let mut b = Fake {
            queued,
            ..Default::default()
        };
        let o = snapshot::read(&mut b);
        assert_eq!(o.build, Some(audio_io::BUILD));
        assert_eq!(o.supported, Some(true));
        assert_eq!(
            o.values,
            Ok(snapshot::Values {
                queued,
                played: u32::MAX,
                underruns: 45
            })
        );
        assert_eq!(b.reads, 10);
    }
}
#[test]
fn actual_status_failures_are_not_merged() {
    for (before, after, queued, expected) in [
        (0, 1, 1010, F::Offline),
        (1, 0, 1010, F::Offline),
        (1, 5, 1010, F::StatusChanged),
        (1, 1, 4097, F::Range),
    ] {
        let mut b = Fake {
            before,
            after,
            queued,
            ..Default::default()
        };
        assert_eq!(snapshot::read(&mut b).values, Err(expected));
    }
}
#[test]
fn actual_identity_failure_is_supported_false_and_no_payload_reads() {
    for field in 0..3 {
        let mut b = Fake::default();
        match field {
            0 => b.build = 0x4d424f49,
            1 => b.magic = 0,
            2 => b.schema = 0,
            _ => {}
        }
        let o = snapshot::read(&mut b);
        assert_eq!(o.values, Err(F::Identity));
        assert_eq!(o.supported, Some(false));
        assert!(b.reads <= 5);
    }
}
