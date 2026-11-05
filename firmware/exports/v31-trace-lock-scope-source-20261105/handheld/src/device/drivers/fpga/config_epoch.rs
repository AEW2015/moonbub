//! Software configuration ownership fence; not an FPGA/JTAG boot identifier.
#[derive(Default)]
pub struct Epoch(u32);
impl Epoch {
    pub const fn new() -> Self {
        Self(0)
    }
    pub fn begin_program(&mut self) {
        self.0 = self.0.wrapping_add(1)
    }
    pub fn value(&self) -> u32 {
        self.0
    }
}
pub fn current(expected: u32, actual: u32) -> bool {
    expected == actual
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn every_program_attempt_invalidates_even_failure() {
        let mut e = Epoch::new();
        let captured = e.value();
        e.begin_program();
        assert!(!current(captured, e.value()));
        let failed = e.value();
        e.begin_program();
        assert!(!current(failed, e.value()));
    }
    #[test]
    fn wrap_and_exact_match() {
        let mut e = Epoch(u32::MAX);
        e.begin_program();
        assert_eq!(e.value(), 0);
        assert!(current(0, e.value()));
        assert!(!current(u32::MAX, e.value()));
    }
}
