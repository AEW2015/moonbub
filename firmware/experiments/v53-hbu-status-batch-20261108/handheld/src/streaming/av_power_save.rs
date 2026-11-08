//! AV-only Wi-Fi power-save scope. Getter, verification and exact restoration.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    ReadInitial,
    InvalidInitial,
    Set,
    Verify,
    Restore,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stage {
    Enter,
    Restore,
}
#[derive(Clone, Copy, Debug)]
pub struct Report {
    pub stage: Stage,
    pub initial: Option<u32>,
    pub actual: Option<u32>,
    pub error: Option<Error>,
}
pub trait Radio {
    fn get(&mut self) -> Result<u32, ()>;
    fn set(&mut self, mode: u32) -> Result<(), ()>;
    fn report(&mut self, _: Report) {}
}
pub struct Guard<R: Radio> {
    radio: R,
    initial: u32,
    attempted: bool,
    closed: Option<Result<u32, Error>>,
}
impl<R: Radio> Guard<R> {
    pub fn enter(mut radio: R) -> Result<Self, Error> {
        let initial = match radio.get() {
            Ok(v) if v <= 2 => v,
            Ok(v) => {
                radio.report(Report {
                    stage: Stage::Enter,
                    initial: Some(v),
                    actual: Some(v),
                    error: Some(Error::InvalidInitial),
                });
                return Err(Error::InvalidInitial);
            }
            Err(()) => {
                radio.report(Report {
                    stage: Stage::Enter,
                    initial: None,
                    actual: None,
                    error: Some(Error::ReadInitial),
                });
                return Err(Error::ReadInitial);
            }
        };
        let mut guard = Self {
            radio,
            initial,
            attempted: false,
            closed: None,
        };
        if initial == 0 {
            guard.radio.report(Report {
                stage: Stage::Enter,
                initial: Some(initial),
                actual: Some(0),
                error: None,
            });
            return Ok(guard);
        }
        guard.attempted = true;
        let set = guard.radio.set(0);
        let actual = guard.radio.get().ok();
        let error = if set.is_err() {
            Some(Error::Set)
        } else if actual != Some(0) {
            Some(Error::Verify)
        } else {
            None
        };
        guard.radio.report(Report {
            stage: Stage::Enter,
            initial: Some(initial),
            actual,
            error,
        });
        if let Some(error) = error {
            if guard.finish().is_err() {
                return Err(Error::Restore);
            }
            return Err(error);
        }
        Ok(guard)
    }
    pub fn finish(&mut self) -> Result<u32, Error> {
        if let Some(result) = self.closed {
            return result;
        }
        let mut set_ok = true;
        if self.attempted {
            set_ok = self.radio.set(self.initial).is_ok()
        }
        let mut actual = self.radio.get().ok();
        if !self.attempted && actual.is_some() && actual != Some(self.initial) {
            set_ok = self.radio.set(self.initial).is_ok();
            actual = self.radio.get().ok();
        }
        let result = if set_ok && actual == Some(self.initial) {
            Ok(self.initial)
        } else {
            Err(Error::Restore)
        };
        self.closed = Some(result);
        self.radio.report(Report {
            stage: Stage::Restore,
            initial: Some(self.initial),
            actual,
            error: result.err(),
        });
        result
    }
}
impl<R: Radio> Drop for Guard<R> {
    fn drop(&mut self) {
        if self.closed.is_none() {
            let _ = self.finish();
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::{cell::RefCell, rc::Rc};
    #[derive(Default)]
    struct State {
        mode: u32,
        gets: usize,
        sets: Vec<u32>,
        fail_get: usize,
        fail_set: usize,
        reports: Vec<Report>,
    }
    #[derive(Clone)]
    struct Fake(Rc<RefCell<State>>);
    impl Radio for Fake {
        fn get(&mut self) -> Result<u32, ()> {
            let mut s = self.0.borrow_mut();
            s.gets += 1;
            if s.gets == s.fail_get {
                Err(())
            } else {
                Ok(s.mode)
            }
        }
        fn set(&mut self, m: u32) -> Result<(), ()> {
            let mut s = self.0.borrow_mut();
            s.sets.push(m);
            s.mode = m;
            if s.sets.len() == s.fail_set {
                Err(())
            } else {
                Ok(())
            }
        }
        fn report(&mut self, r: Report) {
            self.0.borrow_mut().reports.push(r)
        }
    }
    fn radio(mode: u32) -> (Fake, Rc<RefCell<State>>) {
        let s = Rc::new(RefCell::new(State {
            mode,
            ..Default::default()
        }));
        (Fake(s.clone()), s)
    }
    #[test]
    fn capture_and_restore_each_actual_mode() {
        for mode in 0..=2 {
            let (r, s) = radio(mode);
            let mut g = Guard::enter(r).unwrap();
            assert_eq!(s.borrow().mode, 0);
            assert_eq!(g.finish(), Ok(mode));
            assert_eq!(s.borrow().mode, mode);
            assert_eq!(
                s.borrow().sets,
                if mode == 0 { vec![] } else { vec![0, mode] }
            );
            let count = s.borrow().sets.len();
            drop(g);
            assert_eq!(s.borrow().sets.len(), count);
        }
    }
    #[test]
    fn idle_listener_and_video_only_never_touch_radio() {
        let (r, s) = radio(1);
        let idle: Option<Guard<Fake>> = None;
        drop(idle);
        drop(r);
        assert_eq!(s.borrow().gets, 0);
        assert!(s.borrow().sets.is_empty());
    }
    #[test]
    fn initial_get_failure_and_invalid_mode_never_set() {
        for invalid in [false, true] {
            let (r, s) = radio(if invalid { 99 } else { 1 });
            if !invalid {
                s.borrow_mut().fail_get = 1
            }
            assert!(Guard::enter(r).is_err());
            assert!(s.borrow().sets.is_empty());
        }
    }
    #[test]
    fn ambiguous_set_and_verify_failure_restore_captured_identity() {
        for fault in [1, 2] {
            let (r, s) = radio(2);
            if fault == 1 {
                s.borrow_mut().fail_set = 1
            } else {
                s.borrow_mut().fail_get = 2
            }
            assert!(Guard::enter(r).is_err());
            assert_eq!(s.borrow().mode, 2);
            assert_eq!(s.borrow().sets, [0, 2]);
        }
    }
    #[test]
    fn restore_failure_is_reported_and_never_success() {
        let (r, s) = radio(1);
        let mut g = Guard::enter(r).unwrap();
        s.borrow_mut().fail_set = 2;
        assert_eq!(g.finish(), Err(Error::Restore));
        assert_eq!(g.finish(), Err(Error::Restore));
        assert!(s
            .borrow()
            .reports
            .iter()
            .any(|r| r.stage == Stage::Restore && r.error == Some(Error::Restore)));
    }
    #[test]
    fn normal_cancel_session_error_and_unwind_restore() {
        for cause in 0..3 {
            let (r, s) = radio(1);
            if cause == 2 {
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    let _g = Guard::enter(r).unwrap();
                    panic!("injected")
                }));
                assert!(result.is_err());
            } else {
                let _g = Guard::enter(r).unwrap();
            }
            assert_eq!(s.borrow().mode, 1);
            assert_eq!(s.borrow().sets, [0, 1]);
        }
    }
    #[test]
    fn repeated_sessions_capture_fresh_actual_mode() {
        let (r, s) = radio(1);
        drop(Guard::enter(r.clone()).unwrap());
        s.borrow_mut().mode = 2;
        drop(Guard::enter(r).unwrap());
        assert_eq!(s.borrow().sets, [0, 1, 0, 2]);
    }
}
