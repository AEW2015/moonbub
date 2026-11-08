//! Read-only APC1 snapshot with exact per-read-stage failure attribution.
use super::{
    audio_diag::SnapshotFailure,
    audio_io::{self, Bus},
};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Values {
    pub queued: u32,
    pub played: u32,
    pub underruns: u32,
}
pub struct Observation {
    pub build: Option<u32>,
    pub supported: Option<bool>,
    pub values: Result<Values, SnapshotFailure>,
}
pub fn read(bus: &mut impl Bus) -> Observation {
    let (mut build, mut supported) = (None, None);
    let values = (|| -> Result<Values, SnapshotFailure> {
        macro_rules! read {
            ($off:expr,$stage:expr) => {
                bus.read($off).map_err(|_| SnapshotFailure::Io($stage))?
            };
        }
        let observed = read!(0x184, 0);
        build = Some(observed);
        let magic = read!(0, 1);
        let version = read!(4, 2);
        supported = Some(false);
        if magic != 0x4d425631 || version >> 16 != 1 || observed != audio_io::BUILD {
            return Err(SnapshotFailure::Identity);
        }
        if read!(0x300, 3) != audio_io::MAGIC || read!(0x304, 4) != audio_io::SCHEMA {
            return Err(SnapshotFailure::Identity);
        }
        supported = Some(true);
        let before = read!(0x30c, 5);
        let queued = read!(0x348, 6);
        let played = read!(0x334, 7);
        let underruns = read!(0x338, 8);
        let after = read!(0x30c, 9);
        if before & 1 == 0 || after & 1 == 0 {
            return Err(SnapshotFailure::Offline);
        }
        if before & 0x24 != after & 0x24 {
            return Err(SnapshotFailure::StatusChanged);
        }
        if queued > 4096 {
            return Err(SnapshotFailure::Range);
        }
        Ok(Values {
            queued,
            played,
            underruns,
        })
    })();
    Observation {
        build,
        supported,
        values,
    }
}
