//! Production lazy-worker ownership and priority mailbox, independent of SDK.
use std::sync::atomic::{AtomicU8, Ordering};
const BUSY: u8 = 1;
const STOP: u8 = 2;
const STATUS: u8 = 4;
const CLEAR: u8 = 8;
pub struct Requests(AtomicU8);
impl Requests {
    pub const fn new() -> Self {
        Self(AtomicU8::new(0))
    }
    pub fn busy(&self) -> bool {
        self.0.load(Ordering::Acquire) & BUSY != 0
    }
    fn claim(&self) -> bool {
        self.0
            .compare_exchange(0, BUSY | STATUS, Ordering::AcqRel, Ordering::Acquire)
            .is_ok()
    }
    fn request(&self, bit: u8) {
        let _ = self
            .0
            .fetch_update(Ordering::AcqRel, Ordering::Acquire, |x| {
                if x & BUSY != 0 {
                    Some(x | bit)
                } else {
                    None
                }
            });
    }
    pub fn stop(&self) {
        self.request(STOP)
    }
    pub fn status(&self) {
        self.request(STATUS)
    }
    pub fn clear(&self) {
        self.request(CLEAR)
    }
    fn take(&self, bit: u8) -> bool {
        self.0.fetch_and(!bit, Ordering::AcqRel) & bit != 0
    }
    pub fn take_stop(&self) -> bool {
        self.take(STOP)
    }
    pub fn take_status(&self) -> bool {
        self.take(STATUS)
    }
    pub fn take_clear(&self) -> bool {
        self.take(CLEAR)
    }
    pub fn finished(&self) {
        self.0.store(0, Ordering::Release)
    }
}
#[derive(Debug, PartialEq, Eq)]
pub enum StartResult {
    Started,
    Busy,
    SpawnFailed,
    SendFailed,
    Quarantined,
}
pub trait Launcher {
    type Job;
    type Sender;
    fn reserve(&mut self) -> Result<Self::Job, ()>;
    /// Must spawn without capturing Job. An error still leaves Job at caller.
    fn spawn_empty(&mut self) -> Result<Self::Sender, ()>;
    fn send(&mut self, sender: &Self::Sender, job: Self::Job) -> Result<(), Self::Job>;
    fn release_unissued(&mut self, job: Self::Job) -> bool;
    fn publish(&mut self, sender: Self::Sender);
}
pub fn launch<L: Launcher>(requests: &Requests, io: &mut L) -> StartResult {
    if !requests.claim() {
        return StartResult::Busy;
    }
    let job = match io.reserve() {
        Ok(j) => j,
        Err(()) => {
            requests.finished();
            return StartResult::Busy;
        }
    };
    let sender = match io.spawn_empty() {
        Ok(s) => s,
        Err(()) => {
            if !io.release_unissued(job) {
                return StartResult::Quarantined;
            }
            requests.finished();
            return StartResult::SpawnFailed;
        }
    };
    if let Err(job) = io.send(&sender, job) {
        if !io.release_unissued(job) {
            return StartResult::Quarantined;
        }
        requests.finished();
        return StartResult::SendFailed;
    }
    io.publish(sender);
    StartResult::Started
}
