//! Pure bounded AV scheduling decisions. No socket, allocator, device or clock reads.
//! Durations are decision budgets checked between synchronous operations, not WCET.
pub const INPUT_PERIOD_US: u64 = 20_000;
pub const LEASE_US: u64 = 500_000;
pub const FEED_ATTEMPTS: u32 = 20;
pub const FEED_BUDGET_US: u64 = 2_000;
pub const RX_ATTEMPTS: u32 = 4;
pub const RX_BUDGET_US: u64 = 1_000;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Checkpoint { Cancel, Expired, InputDue, Continue }
pub fn checkpoint(now: u64, cancel: bool, lease: Option<u64>, input_due: u64) -> Checkpoint {
    if cancel { Checkpoint::Cancel }
    else if lease.is_some_and(|t| now.saturating_sub(t) >= LEASE_US) { Checkpoint::Expired }
    else if lease.is_some() && now >= input_due { Checkpoint::InputDue }
    else { Checkpoint::Continue }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Step { Progress, Deferred, LockMiss }
pub fn step_outcome(acquired: bool, phase_changed: bool, event: bool) -> Step {
    if !acquired { Step::LockMiss } else if phase_changed || event { Step::Progress } else { Step::Deferred }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum End { Attempts, Time, LockMiss, Deferred }
#[derive(Clone, Copy, Debug)]
pub struct Pass {
    began: u64, limit: u32, budget: u64,
    pub attempts: u32, pub progress: u32, pub end: Option<End>,
}
impl Pass {
    pub fn feeder(now: u64) -> Self { Self::new(now, FEED_ATTEMPTS, FEED_BUDGET_US) }
    pub fn receive(now: u64) -> Self { Self::new(now, RX_ATTEMPTS, RX_BUDGET_US) }
    fn new(now: u64, limit: u32, budget: u64) -> Self {
        Self { began: now, limit, budget, attempts: 0, progress: 0, end: None }
    }
    // Counts an attempted operation only when permission is returned.
    pub fn allow(&mut self, now: u64) -> bool {
        if self.end.is_some() { return false; }
        if now.saturating_sub(self.began) >= self.budget { self.end = Some(End::Time); return false; }
        if self.attempts >= self.limit { self.end = Some(End::Attempts); return false; }
        self.attempts += 1; true
    }
    // A miss or unchanged phase ends this pass. Work resumes on a later tick.
    pub fn observe(&mut self, step: Step) {
        match step {
            Step::Progress => self.progress = self.progress.saturating_add(1),
            Step::Deferred => self.end = Some(End::Deferred),
            Step::LockMiss => self.end = Some(End::LockMiss),
        }
    }
}
#[derive(Clone, Copy, Debug, Default)]
pub struct ServiceMetrics {
    pub passes: u32, pub attempts: u32, pub progress: u32,
    pub lock_deferrals: u32, pub phase_deferrals: u32,
    pub attempt_budget_ends: u32, pub time_budget_ends: u32,
    pub max_pass_us: u64, pub rx_budget_ends: u32,
}
impl ServiceMetrics {
    pub const fn new() -> Self { Self { passes:0, attempts:0, progress:0, lock_deferrals:0, phase_deferrals:0, attempt_budget_ends:0, time_budget_ends:0, max_pass_us:0, rx_budget_ends:0 } }
    pub fn finish(&mut self, pass: Pass, now: u64) {
        self.passes=self.passes.saturating_add(1);
        self.attempts=self.attempts.saturating_add(pass.attempts);
        self.progress=self.progress.saturating_add(pass.progress);
        self.max_pass_us=self.max_pass_us.max(now.saturating_sub(pass.began));
        let target=match pass.end { Some(End::LockMiss)=>Some(&mut self.lock_deferrals), Some(End::Deferred)=>Some(&mut self.phase_deferrals), Some(End::Attempts)=>Some(&mut self.attempt_budget_ends), Some(End::Time)=>Some(&mut self.time_budget_ends),None=>None };
        if let Some(n)=target { *n=n.saturating_add(1); }
    }
}
#[derive(Clone, Copy, Debug)]
pub struct InputMetrics {
    pub due_us: u64, pub attempts: u32, pub sent: u32, pub errors: u32,
    pub encode_errors: u32, pub short_sends: u32, pub late_attempts: u32,
    pub missed_periods: u32, pub max_lateness_us: u64,
    pub max_success_gap_us: u64, pub sequence_gaps: u32,
    pub last_success_us: Option<u64>, pub last_sequence: Option<u32>,
}
impl InputMetrics {
    pub const fn new() -> Self { Self { due_us:0, attempts:0,sent:0,errors:0,encode_errors:0,short_sends:0,late_attempts:0,missed_periods:0,max_lateness_us:0,max_success_gap_us:0,sequence_gaps:0,last_success_us:None,last_sequence:None } }
    pub fn attempt(&mut self, now:u64, scheduled:bool) {
        self.attempts=self.attempts.saturating_add(1);
        if scheduled {
            let late=now.saturating_sub(self.due_us);
            if late>0 { self.late_attempts=self.late_attempts.saturating_add(1); }
            self.max_lateness_us=self.max_lateness_us.max(late);
            self.missed_periods=self.missed_periods.saturating_add((late/INPUT_PERIOD_US).min(u32::MAX as u64) as u32);
            // No catch-up burst. Repeat-START replies do not postpone periodic input.
            self.due_us=now.saturating_add(INPUT_PERIOD_US);
        }
    }
    pub fn sent(&mut self, now:u64, sequence:u32, bytes:Result<usize,()>, expected:usize) {
        match bytes {
            Ok(n) if n==expected => {
                self.sent=self.sent.saturating_add(1);
                if let Some(last)=self.last_success_us { self.max_success_gap_us=self.max_success_gap_us.max(now.saturating_sub(last)); }
                if let Some(last)=self.last_sequence { self.sequence_gaps=self.sequence_gaps.saturating_add(sequence.wrapping_sub(last).saturating_sub(1)); }
                self.last_success_us=Some(now);self.last_sequence=Some(sequence);
            }
            other => {self.errors=self.errors.saturating_add(1);if other.is_ok(){self.short_sends=self.short_sends.saturating_add(1);}}
        }
    }
    pub fn encode_failed(&mut self) { self.encode_errors=self.encode_errors.saturating_add(1); }
}
#[cfg(test)]mod tests {
 use super::*;
 #[test]fn first_lock_miss_ends_pass_without_burning_attempts(){let mut p=Pass::feeder(0);assert!(p.allow(0));p.observe(Step::LockMiss);for now in [1,10,200]{assert!(!p.allow(now));}assert_eq!(p.attempts,1);assert_eq!(p.progress,0);}
 #[test]fn progress_and_both_budgets_are_independent(){let mut p=Pass::feeder(0);for _ in 0..20{assert!(p.allow(0));p.observe(Step::Progress);}assert!(!p.allow(1));assert_eq!(p.end,Some(End::Attempts));let mut p=Pass::feeder(0);assert!(p.allow(1999));assert!(!p.allow(2000));assert_eq!(p.end,Some(End::Time));}
 #[test]fn no_progress_status_poll_yields(){let mut p=Pass::feeder(0);assert!(p.allow(1));p.observe(Step::Deferred);assert!(!p.allow(2));}
 #[test]fn deadlines_prioritize_cancel_then_expiry_then_input(){assert_eq!(checkpoint(500000,true,Some(0),0),Checkpoint::Cancel);assert_eq!(checkpoint(500000,false,Some(0),0),Checkpoint::Expired);assert_eq!(checkpoint(499999,false,Some(0),0),Checkpoint::InputDue);assert_eq!(checkpoint(900000,false,None,0),Checkpoint::Continue);}
 #[test]fn input_local_failures_consume_sequences_and_no_catchup_burst(){let mut i=InputMetrics::new();i.due_us=100;i.attempt(100,true);i.sent(102,0,Ok(80),80);i.attempt(60100,true);assert_eq!(i.missed_periods,2);i.sent(60101,1,Err(()),80);i.attempt(80100,true);i.sent(80102,2,Ok(79),80);i.attempt(100100,true);i.sent(100101,3,Ok(80),80);assert_eq!((i.sent,i.errors,i.short_sends,i.sequence_gaps),(2,2,1,2));assert_eq!(i.max_success_gap_us,99999);assert_eq!(i.due_us,120100);}
 #[test]fn input_wrap_and_repeat_start_do_not_invent_sequence_gap_or_postpone_due(){let mut i=InputMetrics::new();i.due_us=50;i.attempt(50,true);i.sent(50,u32::MAX,Ok(80),80);i.attempt(60,false);i.sent(60,0,Ok(80),80);assert_eq!(i.sequence_gaps,0);assert_eq!(i.due_us,20050);}
}
