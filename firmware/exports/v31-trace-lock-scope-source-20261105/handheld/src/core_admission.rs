//! Pure single-arbiter policy. Runtime must call mutations only under CONTROL,
//! never while holding Device, AV/session or another conflicting guard.
//! Tokens have inert Drop: losing one retains its reservation (fail closed).
//! Proof fields are adapter-supplied facts, not evidence of physical completion.
use crate::key_diag_core::DiagnosticExitProof;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    Busy,
    Blocked,
    Stale,
    WrongPhase,
    NotDrained,
    Unconfirmed,
    Exhausted,
    NeedsCompatibleCore,
    IncompatibleCore,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Phase {
    Pending,
    Active,
    Draining,
}
#[derive(Debug, Clone, Copy, Default)]
pub struct Blockers {
    pub restoring: bool,
    pub rate_changing: bool,
    pub benchmark: bool,
    pub recovery_failed: bool,
}
impl Blockers {
    fn any(self) -> bool {
        self.restoring || self.rate_changing || self.benchmark || self.recovery_failed
    }
}
#[derive(Debug, Clone, Copy)]
struct Lease {
    id: u64,
    phase: Phase,
    parent: Option<u64>,
    started: bool,
    quarantined: bool,
}
macro_rules! permit {
    ($name:ident) => {
        #[derive(Debug)]
        pub struct $name {
            domain: u64,
            id: u64,
        }
        impl $name {
            pub fn id(&self) -> u64 {
                self.id
            }
            pub fn software_generation(&self) -> u64 {
                self.domain
            }
        }
    };
}
permit!(VideoPermit);
permit!(AvPermit);

permit!(DiagnosticPermit);
/// Token-local one-use authorization; driver validation never locks CONTROL.
#[derive(Debug)]
pub struct ProgramPermit {
    domain: u64,
    id: u64,
    calls: u32,
    completed: u32,
    unknown: bool,
}
impl ProgramPermit {
    fn new(domain: u64, id: u64) -> Self {
        Self {
            domain,
            id,
            calls: 0,
            completed: 0,
            unknown: false,
        }
    }
    pub fn id(&self) -> u64 {
        self.id
    }
    pub fn software_generation(&self) -> u64 {
        self.domain
    }
    pub fn effects_started(&self) -> bool {
        self.calls != 0
    }
    pub fn calls_confirmed(&self) -> bool {
        !self.unknown && self.calls == self.completed
    }
    pub fn authorize_call(&mut self) -> Result<ProgramAuthorization<'_>, Error> {
        if self.unknown || self.calls != self.completed {
            return Err(Error::Unconfirmed);
        }
        if self.calls == u32::MAX {
            return Err(Error::Exhausted);
        }
        Ok(ProgramAuthorization { permit: Some(self) })
    }
}
#[derive(Debug)]
pub struct ProgramAuthorization<'a> {
    permit: Option<&'a mut ProgramPermit>,
}
impl<'a> ProgramAuthorization<'a> {
    pub fn begin(mut self) -> Result<DriverCall<'a>, Error> {
        let p = self.permit.take().ok_or(Error::Stale)?;
        if p.unknown || p.calls != p.completed {
            return Err(Error::Unconfirmed);
        }
        p.calls = p.calls.checked_add(1).ok_or(Error::Exhausted)?;
        Ok(DriverCall {
            permit: p,
            confirmed: false,
        })
    }
}
#[derive(Debug)]
pub struct DriverCall<'a> {
    permit: &'a mut ProgramPermit,
    confirmed: bool,
}
impl DriverCall<'_> {
    pub fn succeeded(mut self) {
        self.permit.completed += 1;
        self.confirmed = true;
    }
}
impl Drop for DriverCall<'_> {
    fn drop(&mut self) {
        if !self.confirmed {
            self.permit.unknown = true;
        }
    }
}
#[derive(Debug, Clone, Copy)]
pub struct VideoDrain {
    pub worker_joined: bool,
    pub receivers_closed: bool,
    pub local_cleanup_complete: bool,
}
#[derive(Debug, Clone, Copy)]
pub struct AvDrain {
    pub session_cleared: bool,
    pub feeder_idle: bool,
    pub io_drained: bool,
    pub power_restored: bool,
}
/// Adapter-supplied loaded-core facts; no programming is permitted to satisfy
/// an incompatible Video join while an independent AV owner remains present.
#[derive(Debug, Clone, Copy)]
pub struct LoadedVideoCore {
    pub compatible: bool,
    pub already_loaded: bool,
    pub unchanged_program_epoch: bool,
}
#[derive(Debug, Clone, Copy)]
pub enum ProgramFinish {
    NoSideEffects,
    Configured {
        call_returned: bool,
        post_init_complete: bool,
    },
    RecoveryConfirmed {
        identity_verified: bool,
        core_quiescent: bool,
    },
    Unconfirmed,
}
#[derive(Debug)]
pub struct CoreAdmission {
    domain: u64,
    next_id: u64,
    blockers: Blockers,
    video: Option<Lease>,
    av: Option<Lease>,
    program: Option<Lease>,
    diagnostic: Option<Lease>,
}
impl CoreAdmission {
    pub const fn new(software_generation: u64) -> Self {
        Self {
            domain: software_generation,
            next_id: 1,
            blockers: Blockers {
                restoring: false,
                rate_changing: false,
                benchmark: false,
                recovery_failed: false,
            },
            video: None,
            av: None,
            program: None,
            diagnostic: None,
        }
    }
    pub fn set_blockers(&mut self, b: Blockers) {
        self.blockers = b;
    }
    fn fresh(&mut self) -> Result<u64, Error> {
        if self.next_id == u64::MAX {
            return Err(Error::Exhausted);
        }
        let n = self.next_id;
        self.next_id += 1;
        Ok(n)
    }
    fn lease(id: u64, parent: Option<u64>) -> Lease {
        Lease {
            id,
            phase: Phase::Pending,
            parent,
            started: false,
            quarantined: false,
        }
    }
    fn matches(&self, domain: u64, id: u64, lease: Option<Lease>) -> bool {
        domain == self.domain && lease.is_some_and(|l| l.id == id)
    }
    pub fn idle(&self) -> bool {
        self.video.is_none()
            && self.av.is_none()
            && self.program.is_none()
            && self.diagnostic.is_none()
    }
    pub fn diagnostic_reserved(&self) -> bool {
        self.diagnostic.is_some()
    }
    pub fn program_reserved(&self) -> bool {
        self.program.is_some()
    }
    pub fn video_phase(&self) -> Option<Phase> {
        self.video.map(|l| l.phase)
    }
    pub fn av_phase(&self) -> Option<Phase> {
        self.av.map(|l| l.phase)
    }
    pub fn reserve_video(&mut self) -> Result<VideoPermit, Error> {
        if self.blockers.any() {
            return Err(Error::Blocked);
        }
        if self.video.is_some() || self.program.is_some() || self.diagnostic.is_some() {
            return Err(Error::Busy);
        }
        let id = self.fresh()?;
        self.video = Some(Self::lease(id, None));
        Ok(VideoPermit {
            domain: self.domain,
            id,
        })
    }
    pub fn activate_video(&mut self, p: &VideoPermit) -> Result<(), Error> {
        if !self.matches(p.domain, p.id, self.video) {
            return Err(Error::Stale);
        }
        if self.program.is_some() || self.video.unwrap().phase != Phase::Pending {
            return Err(Error::WrongPhase);
        }
        if self.av.is_some() {
            return Err(Error::NeedsCompatibleCore);
        }
        self.video.as_mut().unwrap().phase = Phase::Active;
        Ok(())
    }
    pub fn activate_video_loaded_core(
        &mut self,
        p: &VideoPermit,
        proof: LoadedVideoCore,
    ) -> Result<(), Error> {
        if !self.matches(p.domain, p.id, self.video) {
            return Err(Error::Stale);
        }
        if self.program.is_some() || self.video.unwrap().phase != Phase::Pending {
            return Err(Error::WrongPhase);
        }
        if !(proof.compatible && proof.already_loaded && proof.unchanged_program_epoch) {
            return Err(Error::IncompatibleCore);
        }
        self.video.as_mut().unwrap().phase = Phase::Active;
        Ok(())
    }
    /// Independent AV admission: input-only, tone and audio sessions need no
    /// parent VideoPermit. Pending AV already excludes all programming/diag.
    pub fn reserve_av(&mut self) -> Result<AvPermit, Error> {
        if self.blockers.any() {
            return Err(Error::Blocked);
        }
        if self.av.is_some() || self.program.is_some() || self.diagnostic.is_some() {
            return Err(Error::Busy);
        }
        let id = self.fresh()?;
        self.av = Some(Self::lease(id, None));
        Ok(AvPermit {
            domain: self.domain,
            id,
        })
    }
    pub fn activate_av(&mut self, p: &AvPermit) -> Result<(), Error> {
        if !self.matches(p.domain, p.id, self.av) {
            return Err(Error::Stale);
        }
        if self.av.unwrap().phase != Phase::Pending {
            return Err(Error::WrongPhase);
        }
        self.av.as_mut().unwrap().phase = Phase::Active;
        Ok(())
    }
    pub fn begin_av_drain(&mut self, p: &AvPermit) -> Result<(), Error> {
        if !self.matches(p.domain, p.id, self.av) {
            return Err(Error::Stale);
        }
        self.av.as_mut().unwrap().phase = Phase::Draining;
        Ok(())
    }
    pub fn release_av(&mut self, p: AvPermit, proof: AvDrain) -> Result<(), (Error, AvPermit)> {
        let err = if !self.matches(p.domain, p.id, self.av) {
            Some(Error::Stale)
        } else if self.av.unwrap().phase != Phase::Draining {
            Some(Error::WrongPhase)
        } else if !(proof.session_cleared
            && proof.feeder_idle
            && proof.io_drained
            && proof.power_restored)
        {
            Some(Error::NotDrained)
        } else {
            None
        };
        if let Some(e) = err {
            return Err((e, p));
        }
        self.av = None;
        Ok(())
    }
    pub fn begin_video_drain(&mut self, p: &VideoPermit) -> Result<(), Error> {
        if !self.matches(p.domain, p.id, self.video) {
            return Err(Error::Stale);
        }
        self.video.as_mut().unwrap().phase = Phase::Draining;
        Ok(())
    }
    pub fn release_video(
        &mut self,
        p: VideoPermit,
        proof: VideoDrain,
    ) -> Result<(), (Error, VideoPermit)> {
        let err = if !self.matches(p.domain, p.id, self.video) {
            Some(Error::Stale)
        } else if self.video.unwrap().phase != Phase::Draining {
            Some(Error::WrongPhase)
        } else if self.program.is_some()
            || !(proof.worker_joined && proof.receivers_closed && proof.local_cleanup_complete)
        {
            Some(Error::NotDrained)
        } else {
            None
        };
        if let Some(e) = err {
            return Err((e, p));
        }
        self.video = None;
        Ok(())
    }
    pub fn reserve_program(&mut self) -> Result<ProgramPermit, Error> {
        if self.blockers.any() {
            return Err(Error::Blocked);
        }
        if !self.idle() {
            return Err(Error::Busy);
        }
        let id = self.fresh()?;
        self.program = Some(Self::lease(id, None));
        Ok(ProgramPermit::new(self.domain, id))
    }
    /// Existing queued boot restoration needs an exclusive permit after video/AV
    /// drain, while its restoration blocker still prevents new admissions.
    pub fn reserve_restore_program(&mut self) -> Result<ProgramPermit, Error> {
        if !self.blockers.restoring
            || self.blockers.rate_changing
            || self.blockers.benchmark
            || self.blockers.recovery_failed
        {
            return Err(Error::Blocked);
        }
        if !self.idle() {
            return Err(Error::Busy);
        }
        let id = self.fresh()?;
        self.program = Some(Self::lease(id, None));
        Ok(ProgramPermit::new(self.domain, id))
    }
    pub fn reserve_video_program(&mut self, p: &VideoPermit) -> Result<ProgramPermit, Error> {
        if !self.matches(p.domain, p.id, self.video) {
            return Err(Error::Stale);
        }
        if self.blockers.any() {
            return Err(Error::Blocked);
        }
        if self.video.unwrap().phase == Phase::Draining
            || self.av.is_some()
            || self.program.is_some()
            || self.diagnostic.is_some()
        {
            return Err(Error::Busy);
        }
        let id = self.fresh()?;
        self.program = Some(Self::lease(id, Some(p.id)));
        Ok(ProgramPermit::new(self.domain, id))
    }
    /// Must precede physical replacement; authorization retains the reservation.
    pub fn program_side_effects_begin(&mut self, p: &ProgramPermit) -> Result<(), Error> {
        if !self.matches(p.domain, p.id, self.program) {
            return Err(Error::Stale);
        }
        if self.program.unwrap().parent.is_some_and(|id| {
            self.video
                .is_none_or(|v| v.id != id || v.phase == Phase::Draining)
        }) {
            return Err(Error::WrongPhase);
        }
        let l = self.program.as_mut().unwrap();
        if l.quarantined || l.started {
            return Err(Error::WrongPhase);
        }
        l.started = true;
        Ok(())
    }
    pub fn release_program(
        &mut self,
        p: ProgramPermit,
        proof: ProgramFinish,
    ) -> Result<(), (Error, ProgramPermit)> {
        if !self.matches(p.domain, p.id, self.program) {
            return Err((Error::Stale, p));
        }
        let l = self.program.unwrap();
        let confirmed = match proof {
            ProgramFinish::NoSideEffects => !l.started && !p.effects_started() && !l.quarantined,
            ProgramFinish::Configured {
                call_returned,
                post_init_complete,
            } => {
                (l.started || p.effects_started())
                    && p.calls_confirmed()
                    && !l.quarantined
                    && call_returned
                    && post_init_complete
            }
            ProgramFinish::RecoveryConfirmed {
                identity_verified,
                core_quiescent,
            } => identity_verified && core_quiescent,
            ProgramFinish::Unconfirmed => false,
        };
        if !confirmed {
            self.program.as_mut().unwrap().quarantined = true;
            return Err((Error::Unconfirmed, p));
        }
        self.program = None;
        Ok(())
    }
    pub fn reserve_diagnostic(&mut self) -> Result<DiagnosticPermit, Error> {
        if self.blockers.any() {
            return Err(Error::Blocked);
        }
        if !self.idle() {
            return Err(Error::Busy);
        }
        let id = self.fresh()?;
        self.diagnostic = Some(Self::lease(id, None));
        Ok(DiagnosticPermit {
            domain: self.domain,
            id,
        })
    }
    /// Only the unissued token exists here: DiagnosticCore consumes it before any SPI.
    pub fn release_unissued_diagnostic(
        &mut self,
        p: DiagnosticPermit,
    ) -> Result<(), (Error, DiagnosticPermit)> {
        if !self.matches(p.domain, p.id, self.diagnostic) {
            return Err((Error::Stale, p));
        }
        self.diagnostic = None;
        Ok(())
    }
    pub fn release_diagnostic(
        &mut self,
        p: DiagnosticPermit,
        proof: DiagnosticExitProof,
    ) -> Result<(), (Error, DiagnosticPermit, DiagnosticExitProof)> {
        if !self.matches(p.domain, p.id, self.diagnostic)
            || proof.reservation() != p.id
            || proof.software_generation() != p.domain
        {
            return Err((Error::Stale, p, proof));
        }
        self.diagnostic = None;
        Ok(())
    }
    #[cfg(test)]
    pub fn seed_next_id_for_test(&mut self, id: u64) {
        self.next_id = id;
    }
}
