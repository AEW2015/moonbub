//! Pure AKD1 controller. No SDK, locks, timers, allocation or hardware calls.
//! Read outcomes assume an ordered transport; the later adapter must prove that.
use crate::core_admission::DiagnosticPermit;
pub const BUILD: u32 = 0x4d424b31;
pub const MAGIC: u32 = 0x31444b41;
pub const SCHEMA: u32 = 0x00010000;
pub const FIXTURE_BYTES: u32 = 48203;
pub const SAMPLES: u32 = 518400;
pub const WATCHDOG: u32 = 10000000;
pub const TAG: [u32; 4] = [0xee7dc9c6, 0x10bef275, 0x19ffddad, 0x855898f0];
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Register {
    CoreMagic,
    CoreSchema,
    CoreCapabilities,
    Build,
    Magic,
    Schema,
    State,
    Cycles,
    Samples,
    Bytes,
    Fault,
    OwnerLow,
    OwnerHigh,
    Epoch,
    Frame,
    Tag0,
    Tag1,
    Tag2,
    Tag3,
    Rejects,
    Sequence,
    FixtureBytes,
    Watchdog,
}
impl Register {
    pub const fn offset(self) -> u16 {
        match self {
            Self::CoreMagic => 0,
            Self::CoreSchema => 4,
            Self::CoreCapabilities => 8,
            Self::Build => 0x184,
            Self::Magic => 0x400,
            Self::Schema => 0x404,
            Self::State => 0x40c,
            Self::Cycles => 0x410,
            Self::Samples => 0x414,
            Self::Bytes => 0x418,
            Self::Fault => 0x41c,
            Self::OwnerLow => 0x420,
            Self::OwnerHigh => 0x424,
            Self::Epoch => 0x428,
            Self::Frame => 0x42c,
            Self::Tag0 => 0x430,
            Self::Tag1 => 0x434,
            Self::Tag2 => 0x438,
            Self::Tag3 => 0x43c,
            Self::Rejects => 0x440,
            Self::Sequence => 0x444,
            Self::FixtureBytes => 0x448,
            Self::Watchdog => 0x44c,
        }
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    Start,
    Abort,
    Clear,
}
impl Command {
    pub const fn value(self) -> u32 {
        match self {
            Self::Start => 1,
            Self::Abort => 2,
            Self::Clear => 4,
        }
    }
    pub const fn offset(self) -> u16 {
        0x408
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Read(Register),
    Write(Command),
}
#[derive(Debug)]
pub struct Operation {
    domain: u64,
    reservation: u64,
    ticket: u64,
    action: Action,
}
impl Operation {
    pub fn ticket(&self) -> u64 {
        self.ticket
    }
    pub fn action(&self) -> Action {
        self.action
    }
}
#[derive(Debug, Clone, Copy)]
pub enum Outcome {
    Read(u32),
    Written,
    NoLock,
    IoError,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Stage {
    Identity,
    Baseline,
    Start,
    Acknowledge,
    Poll,
    TerminalBefore,
    Payload,
    TerminalAfter,
    AbortIdentity,
    AbortBefore,
    Abort,
    AbortPoll,
    Held,
    ClearIdentity,
    ClearBefore,
    Clear,
    ClearAck,
    Cleared,
    Refused,
    Quarantined,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Reason {
    Identity,
    UnownedState,
    MalformedState,
    Owner,
    Sequence,
    Rejected,
    Torn,
    Io,
    AmbiguousWrite,
    Clock,
    Deadline,
    ActionBudget,
    Ticket,
    ReplyType,
    CancelledBeforeStart,
    OwnerExhausted,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ResultKind {
    Completed,
    HardwareFailed,
    Aborted,
    DataMismatch,
}
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
struct Header {
    status: u32,
    sequence: u32,
    owner: u64,
    rejects: u32,
}
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Payload {
    pub cycles: u32,
    pub samples: u32,
    pub bytes: u32,
    pub fault: u32,
    pub epoch: u32,
    pub frame: u32,
    pub tag: [u32; 4],
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Record {
    pub kind: ResultKind,
    pub owner: u64,
    pub sequence: u32,
    pub status: u32,
    pub payload: Payload,
}
#[derive(Debug, Clone, Copy)]
pub struct Budgets {
    pub job_us: u64,
    pub job_actions: u32,
    pub recovery_us: u64,
    pub recovery_actions: u32,
}
impl Default for Budgets {
    fn default() -> Self {
        Self {
            job_us: 1000000,
            job_actions: 512,
            recovery_us: 200000,
            recovery_actions: 64,
        }
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Budget {
    Job,
    Stop,
    Clear,
}
#[derive(Debug)]
pub struct DiagnosticExitProof {
    reservation: u64,
    domain: u64,
}
impl DiagnosticExitProof {
    pub fn reservation(&self) -> u64 {
        self.reservation
    }
    pub fn software_generation(&self) -> u64 {
        self.domain
    }
}
#[derive(Debug)]
pub struct DiagnosticCore {
    permit: DiagnosticPermit,
    reservation: u64,
    domain: u64,
    program_epoch: u32,
    stage: Stage,
    index: usize,
    baseline: Header,
    before: Header,
    after: Header,
    payload: Payload,
    expected_owner: u64,
    next_ticket: u64,
    outstanding: Option<(u64, Action)>,
    budgets: Budgets,
    budget: Budget,
    since: u64,
    last_now: u64,
    actions: u32,
    may_started: bool,
    stop_requested: bool,
    reading_abort: bool,
    reason: Option<Reason>,
    record: Option<Record>,
}
const IDENTITY: [Register; 8] = [
    Register::CoreMagic,
    Register::CoreSchema,
    Register::CoreCapabilities,
    Register::Build,
    Register::Magic,
    Register::Schema,
    Register::FixtureBytes,
    Register::Watchdog,
];
const EXPECTED: [u32; 8] = [
    MAGIC,
    SCHEMA,
    0,
    BUILD,
    MAGIC,
    SCHEMA,
    FIXTURE_BYTES,
    WATCHDOG,
];
const HEADER: [Register; 5] = [
    Register::State,
    Register::Sequence,
    Register::OwnerLow,
    Register::OwnerHigh,
    Register::Rejects,
];
const PAYLOAD: [Register; 10] = [
    Register::Cycles,
    Register::Samples,
    Register::Bytes,
    Register::Fault,
    Register::Epoch,
    Register::Frame,
    Register::Tag0,
    Register::Tag1,
    Register::Tag2,
    Register::Tag3,
];
fn valid_status(s: u32) -> bool {
    matches!(s, 0 | 9 | 10 | 0x13 | 0x24 | 13 | 0x46)
}
fn terminal(s: u32) -> bool {
    matches!(s, 0x13 | 0x24)
}
fn put_header(h: &mut Header, i: usize, v: u32) {
    match i {
        0 => h.status = v,
        1 => h.sequence = v,
        2 => h.owner = (h.owner & 0xffffffff00000000) | v as u64,
        3 => h.owner = (h.owner & 0xffffffff) | ((v as u64) << 32),
        _ => h.rejects = v,
    }
}
impl DiagnosticCore {
    pub fn new(
        permit: DiagnosticPermit,
        program_epoch: u32,
        now_us: u64,
        budgets: Budgets,
    ) -> Self {
        Self {
            reservation: permit.id(),
            domain: permit.software_generation(),
            permit,
            program_epoch,
            stage: Stage::Identity,
            index: 0,
            baseline: Header::default(),
            before: Header::default(),
            after: Header::default(),
            payload: Payload::default(),
            expected_owner: 0,
            next_ticket: 1,
            outstanding: None,
            budgets,
            budget: Budget::Job,
            since: now_us,
            last_now: now_us,
            actions: 0,
            may_started: false,
            stop_requested: false,
            reading_abort: false,
            reason: None,
            record: None,
        }
    }
    pub fn stage(&self) -> Stage {
        self.stage
    }
    pub fn reason(&self) -> Option<Reason> {
        self.reason
    }
    pub fn record(&self) -> Option<&Record> {
        self.record.as_ref()
    }
    pub fn actions_in_phase(&self) -> u32 {
        self.actions
    }
    fn at(&mut self, s: Stage) {
        self.stage = s;
        self.index = 0;
    }
    fn refuse(&mut self, r: Reason) {
        self.reason = Some(r);
        self.at(if self.may_started {
            Stage::Quarantined
        } else {
            Stage::Refused
        });
    }
    fn quarantine(&mut self, r: Reason) {
        self.reason = Some(r);
        self.at(Stage::Quarantined);
    }
    fn abort_begin(&mut self, now: u64) {
        self.budget = Budget::Stop;
        self.since = now;
        self.actions = 0;
        self.stop_requested = false;
        self.reading_abort = true;
        self.at(Stage::AbortIdentity);
    }
    pub fn request_stop(&mut self, now: u64) {
        if matches!(self.stage, Stage::Held | Stage::Cleared | Stage::Refused) {
            return;
        }
        // An unowned/unknown state discovered before our START cannot be turned into
        // a clean cancellation simply by pressing STOP.
        if self.stage == Stage::Quarantined && !self.may_started {
            return;
        }
        self.stop_requested = true;
        if self.outstanding.is_none() {
            if self.may_started {
                self.abort_begin(now)
            } else {
                self.refuse(Reason::CancelledBeforeStart)
            }
        }
    }
    pub fn request_clear(&mut self, now: u64) -> bool {
        if self.stage != Stage::Held || self.outstanding.is_some() {
            return false;
        }
        self.budget = Budget::Clear;
        self.since = now;
        self.actions = 0;
        self.at(Stage::ClearIdentity);
        true
    }
    fn limits(&self) -> (u64, u32) {
        if self.budget == Budget::Job {
            (self.budgets.job_us, self.budgets.job_actions)
        } else {
            (self.budgets.recovery_us, self.budgets.recovery_actions)
        }
    }
    fn check_time(&mut self, now: u64) -> bool {
        if now < self.last_now {
            self.quarantine(Reason::Clock);
            return false;
        }
        self.last_now = now;
        if now - self.since >= self.limits().0 {
            self.reason = Some(Reason::Deadline);
            if self.budget == Budget::Job && self.may_started {
                self.abort_begin(now)
            } else if !self.may_started {
                self.at(Stage::Refused)
            } else {
                self.at(Stage::Quarantined)
            }
            return false;
        }
        true
    }
    pub fn next_operation(&mut self, now: u64) -> Option<Operation> {
        if self.outstanding.is_some()
            || matches!(
                self.stage,
                Stage::Held | Stage::Cleared | Stage::Refused | Stage::Quarantined
            )
        {
            return None;
        }
        if !self.check_time(now) {
            return None;
        }
        if self.actions >= self.limits().1 {
            self.reason = Some(Reason::ActionBudget);
            if self.budget == Budget::Job && self.may_started {
                self.abort_begin(now)
            } else if !self.may_started {
                self.at(Stage::Refused)
            } else {
                self.at(Stage::Quarantined)
            }
            return None;
        }
        if self.next_ticket == u64::MAX {
            self.quarantine(Reason::Ticket);
            return None;
        }
        let action = match self.stage {
            Stage::Identity | Stage::AbortIdentity | Stage::ClearIdentity => {
                Action::Read(IDENTITY[self.index])
            }
            Stage::Baseline | Stage::Acknowledge => Action::Read(HEADER[self.index]),
            Stage::TerminalBefore
            | Stage::TerminalAfter
            | Stage::AbortBefore
            | Stage::ClearBefore
            | Stage::ClearAck => Action::Read(HEADER[self.index]),
            Stage::Start => Action::Write(Command::Start),
            Stage::Abort => Action::Write(Command::Abort),
            Stage::Clear => Action::Write(Command::Clear),
            Stage::Poll | Stage::AbortPoll => Action::Read(Register::State),
            Stage::Payload => Action::Read(PAYLOAD[self.index]),
            _ => return None,
        };
        let ticket = self.next_ticket;
        self.next_ticket += 1;
        self.actions += 1;
        self.outstanding = Some((ticket, action));
        Some(Operation {
            domain: self.domain,
            reservation: self.reservation,
            ticket,
            action,
        })
    }
    pub fn complete(
        &mut self,
        operation: Operation,
        outcome: Outcome,
        program_epoch: u32,
        now: u64,
    ) {
        if operation.domain != self.domain
            || operation.reservation != self.reservation
            || self.outstanding != Some((operation.ticket, operation.action))
        {
            self.quarantine(Reason::Ticket);
            return;
        }
        self.outstanding = None;
        if matches!(operation.action, Action::Write(Command::Start))
            && !matches!(outcome, Outcome::NoLock)
        {
            self.may_started = true;
        }
        if program_epoch != self.program_epoch {
            self.quarantine(Reason::Identity);
            return;
        }
        if !self.check_time(now) {
            return;
        }
        if matches!(outcome, Outcome::NoLock) {
            if self.stop_requested {
                if self.may_started {
                    self.abort_begin(now)
                } else {
                    self.refuse(Reason::CancelledBeforeStart)
                }
            }
            return;
        }
        if matches!(outcome, Outcome::IoError) {
            self.quarantine(if matches!(operation.action, Action::Write(_)) {
                Reason::AmbiguousWrite
            } else {
                Reason::Io
            });
            return;
        }
        if self.stop_requested {
            if self.may_started {
                self.abort_begin(now)
            } else {
                self.refuse(Reason::CancelledBeforeStart)
            }
            return;
        }
        match (operation.action, outcome) {
            (Action::Write(Command::Start), Outcome::Written) => {
                self.before = Header::default();
                self.at(Stage::Acknowledge)
            }
            (Action::Write(Command::Abort), Outcome::Written) => self.at(Stage::AbortPoll),
            (Action::Write(Command::Clear), Outcome::Written) => {
                self.after = Header::default();
                self.at(Stage::ClearAck)
            }
            (Action::Read(_), Outcome::Read(v)) => self.read(v),
            _ => self.quarantine(Reason::ReplyType),
        }
    }
    fn read(&mut self, v: u32) {
        match self.stage {
            Stage::Identity | Stage::AbortIdentity | Stage::ClearIdentity => {
                if v != EXPECTED[self.index] {
                    self.refuse(Reason::Identity);
                    return;
                }
                self.index += 1;
                if self.index == IDENTITY.len() {
                    let next = match self.stage {
                        Stage::Identity => Stage::Baseline,
                        Stage::AbortIdentity => Stage::AbortBefore,
                        _ => Stage::ClearBefore,
                    };
                    self.before = Header::default();
                    self.at(next);
                }
            }
            Stage::Baseline
            | Stage::Acknowledge
            | Stage::AbortBefore
            | Stage::ClearBefore
            | Stage::TerminalBefore => {
                put_header(&mut self.before, self.index, v);
                self.index += 1;
                let need = if matches!(self.stage, Stage::Baseline | Stage::Acknowledge) {
                    5
                } else {
                    4
                };
                if self.index < need {
                    return;
                }
                if !valid_status(self.before.status) {
                    self.quarantine(Reason::MalformedState);
                    return;
                }
                match self.stage {
                    Stage::Baseline => {
                        if self.before.status != 0 {
                            self.quarantine(Reason::UnownedState);
                            return;
                        }
                        self.baseline = self.before;
                        if self.before.owner >= u64::MAX - 1 {
                            self.refuse(Reason::OwnerExhausted);
                            return;
                        }
                        self.expected_owner = self.before.owner + 1;
                        self.at(Stage::Start);
                    }
                    Stage::Acknowledge => {
                        if self.before.owner != self.expected_owner {
                            self.quarantine(Reason::Owner);
                            return;
                        }
                        if self.before.rejects != self.baseline.rejects {
                            self.quarantine(Reason::Rejected);
                            return;
                        }
                        if self.before.sequence != self.baseline.sequence
                            && self.before.sequence != self.baseline.sequence.wrapping_add(1)
                        {
                            self.quarantine(Reason::Sequence);
                            return;
                        }
                        if terminal(self.before.status) {
                            self.at(Stage::TerminalBefore)
                        } else if matches!(self.before.status, 9 | 10) {
                            self.at(Stage::Poll)
                        } else {
                            self.quarantine(Reason::UnownedState)
                        }
                    }
                    Stage::AbortBefore => {
                        if self.before.owner != self.expected_owner {
                            self.quarantine(Reason::Owner);
                            return;
                        }
                        if self.before.sequence != self.baseline.sequence
                            && self.before.sequence != self.baseline.sequence.wrapping_add(1)
                        {
                            self.quarantine(Reason::Sequence);
                            return;
                        }
                        self.at(Stage::Abort);
                    }
                    Stage::ClearBefore => {
                        let r = self.record.unwrap();
                        if self.before.owner != r.owner
                            || self.before.sequence != r.sequence
                            || self.before.status != r.status
                        {
                            self.quarantine(Reason::Torn);
                            return;
                        }
                        self.at(Stage::Clear);
                    }
                    Stage::TerminalBefore => {
                        let expected = if self.reading_abort {
                            self.before.status == 0x46
                        } else {
                            terminal(self.before.status)
                        };
                        if !expected || self.before.owner != self.expected_owner {
                            self.quarantine(Reason::Owner);
                            return;
                        }
                        if self.reading_abort {
                            if self.before.sequence != self.baseline.sequence
                                && self.before.sequence != self.baseline.sequence.wrapping_add(1)
                            {
                                self.quarantine(Reason::Sequence);
                                return;
                            }
                        } else if self.before.sequence != self.baseline.sequence.wrapping_add(1) {
                            self.quarantine(Reason::Sequence);
                            return;
                        }
                        self.payload = Payload::default();
                        self.at(Stage::Payload);
                    }
                    _ => {}
                }
            }
            Stage::Poll | Stage::AbortPoll => {
                if !valid_status(v) {
                    self.quarantine(Reason::MalformedState)
                } else if self.stage == Stage::AbortPoll && v == 0x46
                    || self.stage == Stage::Poll && terminal(v)
                {
                    self.before = Header::default();
                    self.at(Stage::TerminalBefore)
                } else if matches!(v, 9 | 10 | 13) { /* keep polling */
                } else {
                    self.quarantine(Reason::UnownedState)
                }
            }
            Stage::Payload => {
                match self.index {
                    0 => self.payload.cycles = v,
                    1 => self.payload.samples = v,
                    2 => self.payload.bytes = v,
                    3 => self.payload.fault = v,
                    4 => self.payload.epoch = v,
                    5 => self.payload.frame = v,
                    i => self.payload.tag[i - 6] = v,
                };
                self.index += 1;
                if self.index == PAYLOAD.len() {
                    self.after = Header::default();
                    self.at(Stage::TerminalAfter)
                }
            }
            Stage::TerminalAfter | Stage::ClearAck => {
                put_header(&mut self.after, self.index, v);
                self.index += 1;
                if self.index < 4 {
                    return;
                }
                if self.stage == Stage::ClearAck {
                    let r = self.record.unwrap();
                    if self.after.status != 0
                        || self.after.owner != r.owner
                        || self.after.sequence != r.sequence
                    {
                        self.quarantine(Reason::Torn)
                    } else {
                        self.at(Stage::Cleared)
                    }
                    return;
                }
                if (self.before.status, self.before.sequence, self.before.owner)
                    != (self.after.status, self.after.sequence, self.after.owner)
                {
                    self.quarantine(Reason::Torn);
                    return;
                }
                let p = self.payload;
                let bounded =
                    p.cycles <= WATCHDOG && p.samples <= SAMPLES && p.bytes <= FIXTURE_BYTES;
                let kind = if self.reading_abort {
                    if !bounded || p.fault != 0 || p.tag != [0; 4] {
                        self.quarantine(Reason::Torn);
                        return;
                    }
                    ResultKind::Aborted
                } else if self.before.status == 0x24 {
                    if !bounded {
                        self.quarantine(Reason::Torn);
                        return;
                    }
                    ResultKind::HardwareFailed
                } else if bounded
                    && p.samples == SAMPLES
                    && p.bytes == FIXTURE_BYTES
                    && p.fault == 0
                    && p.epoch == 1
                    && p.frame == 0
                    && p.tag == TAG
                {
                    ResultKind::Completed
                } else {
                    ResultKind::DataMismatch
                };
                self.record = Some(Record {
                    kind,
                    owner: self.before.owner,
                    sequence: self.before.sequence,
                    status: self.before.status,
                    payload: p,
                });
                self.at(Stage::Held);
            }
            _ => self.quarantine(Reason::ReplyType),
        }
    }
    pub fn into_exit(
        self,
    ) -> Result<(DiagnosticPermit, DiagnosticExitProof, Option<Record>), Self> {
        if self.outstanding.is_none()
            && (self.stage == Stage::Cleared || self.stage == Stage::Refused && !self.may_started)
        {
            Ok((
                self.permit,
                DiagnosticExitProof {
                    reservation: self.reservation,
                    domain: self.domain,
                },
                self.record,
            ))
        } else {
            Err(self)
        }
    }
}
