//! Fence a multi-line UI render across FPGA programming without retaining the
//! shared Device lock while Slint renders. Check and publish under the same lock.
#[derive(Clone, Copy, Debug)]
pub struct FrameFence {
    expected: u32,
    stale: bool,
}
impl FrameFence {
    pub const fn new(expected: u32) -> Self {
        Self { expected, stale: false }
    }
    pub fn is_stale(&self) -> bool { self.stale }
    pub fn publish<T>(&mut self, actual: u32, write: impl FnOnce() -> T) -> Option<T> {
        if actual != self.expected { self.stale = true; }
        if self.stale { None } else { Some(write()) }
    }
}
