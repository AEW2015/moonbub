//! Production orchestration shared by SDK callbacks and host fake-I/O tests.
//! Call only under CONTROL. No callback, blocking operation or other lock here.
use crate::core_admission::*;
use crate::key_diag_core::{DiagnosticExitProof, BUILD, MAGIC};
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Maintenance {
    Benchmark,
    Rate,
    Restore,
}
#[derive(Debug)]
pub struct MaintenancePermit {
    id: u64,
    kind: Maintenance,
}
#[derive(Debug)]
pub struct Coordinator {
    pub(crate) admission: CoreAdmission,
    video: Option<VideoPermit>,
    av: Option<AvPermit>,
    maintenance: Option<(u64, Maintenance)>,
    next: u64,
    pending_source: bool,
    quarantined: bool,
    recovery_pending: bool,
    diagnostic_peer: bool,
    failed_maintenance: Option<MaintenancePermit>,
    failed_unissued: Option<DiagnosticPermit>,
    failed_program: Option<ProgramPermit>,
    failed_diagnostic: Option<(DiagnosticPermit, DiagnosticExitProof)>,
}
impl Coordinator {
    pub const fn new() -> Self {
        Self {
            admission: CoreAdmission::new(1),
            video: None,
            av: None,
            maintenance: None,
            next: 1,
            pending_source: false,
            quarantined: false,
            recovery_pending: false,
            diagnostic_peer: false,
            failed_maintenance: None,
            failed_unissued: None,
            failed_program: None,
            failed_diagnostic: None,
        }
    }
    fn blockers(&mut self) {
        self.admission.set_blockers(Blockers {
            restoring: self
                .maintenance
                .is_some_and(|(_, m)| m == Maintenance::Restore),
            rate_changing: self
                .maintenance
                .is_some_and(|(_, m)| m == Maintenance::Rate),
            benchmark: self
                .maintenance
                .is_some_and(|(_, m)| m == Maintenance::Benchmark),
            recovery_failed: self.quarantined || self.recovery_pending,
        });
    }
    pub fn quarantine(&mut self) {
        self.quarantined = true;
        self.blockers()
    }
    pub fn quarantined(&self) -> bool {
        self.quarantined
    }
    /// Observation only. A completed held lab worker may retain Benchmark while
    /// an explicit whole-system reboot recovers it; this never releases a lease.
    pub fn lab_reboot_quiet(&self, completed_lab:bool) -> bool {
        !self.recovery_pending && self.video.is_none() && self.av.is_none() && !self.pending_source
            && !self.admission.program_reserved() && !self.admission.diagnostic_reserved()
            && (self.maintenance.is_none() || (completed_lab && self.maintenance.is_some_and(|(_,kind)|kind==Maintenance::Benchmark)))
    }
    pub fn lab_reboot_begin(&mut self, completed_lab:bool)->bool{
        if !self.lab_reboot_quiet(completed_lab){return false}
        self.recovery_pending=true;self.blockers();true
    }
    pub fn lab_reboot_cancel(&mut self){self.recovery_pending=false;self.blockers();}
    pub fn note_peer(&mut self, magic: u32, build: u32) {
        self.diagnostic_peer = magic == MAGIC || build == BUILD;
    }
    pub fn diagnostic_peer(&self) -> bool {
        self.diagnostic_peer
    }
    pub fn receiver_request(&mut self) -> Result<(), Error> {
        if self.quarantined || self.recovery_pending
            || self.diagnostic_peer
            || self.maintenance.is_some()
            || self.admission.program_reserved()
            || self.admission.diagnostic_reserved()
        {
            return Err(Error::Busy);
        }
        // Keep the lease across queued source changes; there is one receiver worker.
        if self.video.is_none() {
            self.video = Some(self.admission.reserve_video()?);
        }
        self.pending_source = true;
        Ok(())
    }
    pub fn source_dequeued(&mut self) {
        self.pending_source = false;
    }
    pub fn receiver_activation_failed(&mut self) {
        self.pending_source = false;
        self.quarantine();
    }
    pub fn receiver_active(&mut self) -> Result<(), Error> {
        let p = self.video.as_ref().ok_or(Error::Stale)?;
        if self.admission.video_phase() == Some(Phase::Pending) {
            self.admission.activate_video(p)?;
        }
        Ok(())
    }
    pub fn receiver_stopped(&mut self, cleanup_confirmed: bool) -> Result<(), Error> {
        // SDK receiver teardown must join/drain its AV guard first.
        if !cleanup_confirmed || self.av.is_some() {
            self.quarantine();
            return Err(Error::NotDrained);
        }
        if self.pending_source {
            return Ok(());
        }
        if let Some(p) = self.video.take() {
            self.admission.begin_video_drain(&p)?;
            if let Err((e, p)) = self.admission.release_video(
                p,
                VideoDrain {
                    worker_joined: true,
                    receivers_closed: true,
                    local_cleanup_complete: true,
                },
            ) {
                self.video = Some(p);
                self.quarantine();
                return Err(e);
            }
        }
        Ok(())
    }
    pub fn cancel_pending(&mut self, worker_active: bool) -> Result<(), Error> {
        self.pending_source = false;
        if !worker_active {
            self.receiver_stopped(true)
        } else {
            Ok(())
        }
    }
    pub fn av_admit(&mut self) -> Result<(), Error> {
        if self.diagnostic_peer || self.quarantined || self.recovery_pending || self.maintenance.is_some() {
            return Err(Error::Busy);
        }
        if self.video.is_none() {
            return Err(Error::WrongPhase);
        }
        if self.av.is_none() {
            let p = self.admission.reserve_av()?;
            self.admission.activate_av(&p)?;
            self.av = Some(p);
        }
        Ok(())
    }
    pub fn av_drained(&mut self, proof: AvDrain) -> Result<(), Error> {
        if let Some(p) = self.av.take() {
            self.admission.begin_av_drain(&p)?;
            if let Err((e, p)) = self.admission.release_av(p, proof) {
                self.av = Some(p);
                self.quarantine();
                return Err(e);
            }
        }
        Ok(())
    }
    pub fn program(&mut self, receiver: bool, restore: bool) -> Result<ProgramPermit, Error> {
        if self.quarantined || self.recovery_pending {
            return Err(Error::Busy);
        }
        if restore {
            return self.admission.reserve_restore_program();
        }
        if receiver {
            self.admission
                .reserve_video_program(self.video.as_ref().ok_or(Error::Stale)?)
        } else {
            self.admission.reserve_program()
        }
    }
    pub fn program_finished(&mut self, p: ProgramPermit, post_init: bool) -> Result<(), Error> {
        let proof = if !p.effects_started() {
            ProgramFinish::NoSideEffects
        } else {
            ProgramFinish::Configured {
                call_returned: p.calls_confirmed(),
                post_init_complete: post_init,
            }
        };
        if let Err((e, retained)) = self.admission.release_program(p, proof) {
            self.failed_program = Some(retained);
            self.quarantine();
            return Err(e);
        }
        Ok(())
    }
    pub fn diagnostic(&mut self) -> Result<DiagnosticPermit, Error> {
        if self.recovery_pending{return Err(Error::Busy)}
        self.admission.reserve_diagnostic()
    }
    pub fn unissued_diagnostic_finished(&mut self, p: DiagnosticPermit) -> Result<(), Error> {
        match self.admission.release_unissued_diagnostic(p) {
            Ok(()) => Ok(()),
            Err((e, p)) => {
                self.failed_unissued = Some(p);
                self.quarantine();
                Err(e)
            }
        }
    }
    pub fn diagnostic_finished(
        &mut self,
        p: DiagnosticPermit,
        proof: DiagnosticExitProof,
    ) -> Result<(), Error> {
        match self.admission.release_diagnostic(p, proof) {
            Ok(()) => Ok(()),
            Err((e, p, proof)) => {
                self.failed_diagnostic = Some((p, proof));
                self.quarantine();
                Err(e)
            }
        }
    }
    pub fn maintenance(&mut self, kind: Maintenance) -> Result<MaintenancePermit, Error> {
        if self.maintenance.is_some()
            || self.recovery_pending
            || self.quarantined
            || self.admission.program_reserved()
            || self.admission.diagnostic_reserved()
        {
            return Err(Error::Busy);
        }
        if kind != Maintenance::Restore && !self.admission.idle() {
            return Err(Error::Busy);
        }
        let id = self.next;
        self.next = self.next.checked_add(1).ok_or(Error::Exhausted)?;
        self.maintenance = Some((id, kind));
        self.blockers();
        Ok(MaintenancePermit { id, kind })
    }
    pub fn restore_begin(&mut self) -> Result<(), Error> {
        let _retained = self.maintenance(Maintenance::Restore)?;
        Ok(())
    }
    pub fn restore_finished(&mut self, confirmed: bool) -> Result<(), Error> {
        let (id, kind) = self.maintenance.ok_or(Error::Stale)?;
        if kind != Maintenance::Restore {
            return Err(Error::WrongPhase);
        }
        self.maintenance_finished(MaintenancePermit { id, kind }, confirmed)
    }
    pub fn maintenance_finished(
        &mut self,
        p: MaintenancePermit,
        confirmed: bool,
    ) -> Result<(), Error> {
        if self.maintenance != Some((p.id, p.kind)) {
            return Err(Error::Stale);
        }
        if !confirmed {
            self.failed_maintenance = Some(p);
            self.quarantine();
            return Err(Error::Unconfirmed);
        }
        self.maintenance = None;
        self.blockers();
        Ok(())
    }
}
/// Exact pairs, never a build-only allowlist. Audio identity stays independent.
pub fn display_peer(magic: u32, schema: u32, build: u32) -> bool {
    schema == 0x00010000
        && ((magic == 0x4d425631 && (build == 0x4d424f49 || build == 0x4d424f50))
            || (magic == MAGIC && build == BUILD))
}

#[cfg(not(test))]
pub static CONTROL: std::sync::Mutex<Coordinator> = std::sync::Mutex::new(Coordinator::new());
// Host-only thread-local depth instruments the SAME production call sites.
// try_lock on a global mutex would falsely flag another thread's valid hold.
#[cfg(test)]
mod checked {
    use super::*;
    use std::ops::{Deref, DerefMut};
    thread_local! {static DEPTH:std::cell::Cell<u32>=const{std::cell::Cell::new(0)};}
    pub fn depth() -> u32 {
        DEPTH.with(|n| n.get())
    }
    pub struct Checked(std::sync::Mutex<Coordinator>);
    pub struct Guard(std::sync::MutexGuard<'static, Coordinator>);
    impl Checked {
        pub const fn new() -> Self {
            Self(std::sync::Mutex::new(Coordinator::new()))
        }
        pub fn lock(&'static self) -> Result<Guard, ()> {
            let g = self.0.lock().map_err(|_| ())?;
            DEPTH.with(|n| n.set(n.get() + 1));
            Ok(Guard(g))
        }
        pub fn try_lock(&'static self) -> Result<Guard, ()> {
            let g = self.0.try_lock().map_err(|_| ())?;
            DEPTH.with(|n| n.set(n.get() + 1));
            Ok(Guard(g))
        }
    }
    impl Deref for Guard {
        type Target = Coordinator;
        fn deref(&self) -> &Coordinator {
            &self.0
        }
    }
    impl DerefMut for Guard {
        fn deref_mut(&mut self) -> &mut Coordinator {
            &mut self.0
        }
    }
    impl Drop for Guard {
        fn drop(&mut self) {
            DEPTH.with(|n| n.set(n.get() - 1));
        }
    }
}
#[cfg(test)]
pub use checked::depth as test_control_depth;
#[cfg(test)]
pub static CONTROL: checked::Checked = checked::Checked::new();
