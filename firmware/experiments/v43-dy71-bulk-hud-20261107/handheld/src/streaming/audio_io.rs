//! APC1 bounded single-feeder state machine; one bus action per step.
pub const BUILD: u32 = 0x4d424f50;
pub const MAGIC: u32 = 0x41504331;
pub const SCHEMA: u32 = 0x00010001;
pub trait Bus {
    fn read(&mut self, offset: u32) -> Result<u32, ()>;
    fn write(&mut self, offset: u32, value: u32) -> Result<(), ()>;
    fn pcm(&mut self, data: &[u8]) -> Result<(), ()>;
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Idle,
    Stop,
    WaitStop,
    Session,
    Counter,
    Ready,
    Frames,
    Sequence,
    Crc,
    Begin,
    Staging,
    Pcm,
    Commit,
    Receipt1,
    ReceiptSeq,
    ReceiptSession,
    Receipt2,
    ReceiptStatus,
    Arm,
    Failed,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ResultEvent {
    None,
    Online,
    Committed,
    Armed,
    Rejected,
    Stopped,
    Fault,
}
pub struct Feeder {
    pub phase: Phase,
    pub session: u32,
    pub sequence: u32,
    pub blocks: u32,
    pub baseline: u32,
    pub crc: u32,
    pub staged: bool,
    pub active: bool,
    stopping: bool,
    receipt: u32,
    last_seq: u32,
    last_session: u32,
}
impl Feeder {
    pub const fn new() -> Self {
        Self {
            phase: Phase::Idle,
            session: 0,
            sequence: 0,
            blocks: 0,
            baseline: 0,
            crc: 0,
            staged: false,
            active: false,
            stopping: false,
            receipt: 0,
            last_seq: 0,
            last_session: 0,
        }
    }
    pub fn start(&mut self, session: u32) {
        self.session = session;
        self.blocks = 0;
        self.active = false;
        self.stopping = false;
        self.phase = Phase::Stop;
    }
    pub fn stop(&mut self) {
        self.stopping = true;
        self.active = false;
        self.phase = Phase::Stop;
    }
    pub fn submit(&mut self, sequence: u32, crc: u32) -> bool {
        if self.phase != Phase::Idle || !self.active {
            return false;
        }
        self.sequence = sequence;
        self.crc = crc;
        self.phase = Phase::Counter;
        true
    }
    pub fn fail(&mut self) -> ResultEvent {
        self.phase = Phase::Failed;
        self.active = false;
        ResultEvent::Fault
    }
    pub fn step(&mut self, bus: &mut impl Bus, pcm: &[u8]) -> ResultEvent {
        let result = (|| -> Result<ResultEvent, ()> {
            match self.phase {
                Phase::Idle | Phase::Failed => return Ok(ResultEvent::None),
                Phase::Stop => {
                    bus.write(0x308, 0)?;
                    self.phase = Phase::WaitStop;
                }
                Phase::WaitStop => {
                    let s = bus.read(0x30c)?;
                    if s & 0x2f == 1 && (s >> 8) & 255 == 5 {
                        self.staged = false;
                        if self.stopping {
                            self.phase = Phase::Idle;
                            return Ok(ResultEvent::Stopped);
                        }
                        self.phase = Phase::Session
                    }
                }
                Phase::Session => {
                    bus.write(0x31c, self.session)?;
                    self.active = true;
                    self.phase = Phase::Idle;
                    return Ok(ResultEvent::Online);
                }
                Phase::Counter => {
                    self.baseline = bus.read(0x324)?;
                    self.phase = Phase::Ready
                }
                Phase::Ready => {
                    let s = bus.read(0x320)?;
                    if s & 15 == 0 {
                        self.phase = Phase::Idle;
                        return Ok(ResultEvent::Rejected);
                    }
                    self.phase = Phase::Frames
                }
                Phase::Frames => {
                    bus.write(0x310, 505)?;
                    self.phase = Phase::Sequence
                }
                Phase::Sequence => {
                    bus.write(0x314, self.sequence)?;
                    self.phase = Phase::Crc
                }
                Phase::Crc => {
                    bus.write(0x318, self.crc)?;
                    self.phase = Phase::Begin
                }
                Phase::Begin => {
                    bus.write(0x308, 2)?;
                    self.staged = true;
                    self.phase = Phase::Staging
                }
                Phase::Staging => {
                    let s = bus.read(0x30c)?;
                    if s & 3 != 3 || ((s >> 8) & 255) != 2 {
                        return Err(());
                    }
                    self.phase = Phase::Pcm
                }
                Phase::Pcm => {
                    if pcm.len() != 2020 {
                        return Err(());
                    }
                    bus.pcm(pcm)?;
                    self.phase = Phase::Commit
                }
                Phase::Commit => {
                    self.phase = Phase::Receipt1;
                    let _ = bus.write(0x308, 3);
                }
                Phase::Receipt1 => {
                    self.receipt = bus.read(0x324)?;
                    self.phase = Phase::ReceiptSeq
                }
                Phase::ReceiptSeq => {
                    self.last_seq = bus.read(0x328)?;
                    self.phase = Phase::ReceiptSession
                }
                Phase::ReceiptSession => {
                    self.last_session = bus.read(0x32c)?;
                    self.phase = Phase::Receipt2
                }
                Phase::Receipt2 => {
                    let after = bus.read(0x324)?;
                    if self.receipt != after
                        || after.wrapping_sub(self.baseline) != 1
                        || self.last_seq != self.sequence
                        || self.last_session != self.session
                    {
                        return Err(());
                    }
                    self.phase = Phase::ReceiptStatus;
                }
                Phase::ReceiptStatus => {
                    let status = bus.read(0x30c)?;
                    if status & 0xffff0080 != 0 || status & 0x43 != 0x41 || (status >> 8) & 255 != 3
                    {
                        return Err(());
                    }
                    self.staged = false;
                    self.blocks = self.blocks.saturating_add(1);
                    if self.blocks == 2 {
                        self.phase = Phase::Arm;
                        return Ok(ResultEvent::Committed);
                    } else {
                        self.phase = Phase::Idle;
                        return Ok(ResultEvent::Committed);
                    }
                }
                Phase::Arm => {
                    bus.write(0x308, 1)?;
                    self.phase = Phase::Idle;
                    return Ok(ResultEvent::Armed);
                }
            }
            Ok(ResultEvent::None)
        })();
        match result {
            Ok(event) => event,
            Err(()) => self.fail(),
        }
    }
}

/// Full identity is needed on STOP/start. All actions are fenced by the Device-owned epoch.
pub fn identity(bus: &mut impl Bus) -> Result<(), ()> {
    if bus.read(0)? != 0x4d425631
        || bus.read(4)? >> 16 != 1
        || bus.read(0x184)? != BUILD
        || bus.read(0x300)? != MAGIC
        || bus.read(0x304)? != SCHEMA
    {
        Err(())
    } else {
        Ok(())
    }
}
pub fn checked_step(
    feeder: &mut Feeder,
    bus: &mut impl Bus,
    pcm: &[u8],
    current_generation: bool,
    recovery: bool,
    expected_epoch: u32,
    actual_epoch: u32,
) -> ResultEvent {
    if !current_generation && !recovery {
        return ResultEvent::None;
    }
    if recovery && !matches!(feeder.phase, Phase::Stop | Phase::WaitStop) {
        return feeder.fail();
    }
    if expected_epoch != actual_epoch {
        return feeder.fail();
    }
    if feeder.phase == Phase::Stop && identity(bus).is_err() {
        return feeder.fail();
    }
    feeder.step(bus, pcm)
}

/// Count a submitted audio block at most once; control-only faults have no block.
pub fn settle_block(
    pending: &mut Option<u32>,
    accepted: &mut u32,
    rejected_or_unconfirmed: &mut u32,
    committed: bool,
) -> Option<u32> {
    let sequence = pending.take()?;
    if committed {
        *accepted = accepted.saturating_add(1)
    } else {
        *rejected_or_unconfirmed = rejected_or_unconfirmed.saturating_add(1)
    }
    Some(sequence)
}
