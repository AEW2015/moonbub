//! Helpers called while the shared CONTROL mutex is held.
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
pub fn cancel(wanted: &AtomicBool, generation: &AtomicU32) {
    generation.fetch_add(1, Ordering::AcqRel);
    wanted.store(false, Ordering::Release);
}
pub fn may_admit(wanted: bool, generation: u32, request: u32) -> bool {
    wanted && generation == request
}
/// Used by the one serialized network/local worker before claiming ACTIVE.
pub fn may_admit_source(wanted:bool,generation:u32,request:u32,rate_changing:bool,restoring:bool,recovery_failed:bool)->bool {
    may_admit(wanted,generation,request)&&!rate_changing&&!restoring&&!recovery_failed
}
/// e clears activity/wanted but deliberately retains the local view context.
pub fn requires_local_exit(local_wanted:bool,local_active:bool,local_context:bool)->bool {
    local_wanted||local_active||local_context
}
/// Admission checks and creation are serialized by CONTROL; drop is lock-free.
pub struct RateReservation<'a>(&'a AtomicBool);
impl<'a> RateReservation<'a> {
    pub fn acquire(flag: &'a AtomicBool) -> Option<Self> {
        if flag.swap(true, Ordering::AcqRel) { None } else { Some(Self(flag)) }
    }
}
impl Drop for RateReservation<'_> {
    fn drop(&mut self) { self.0.store(false, Ordering::Release); }
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, Mutex, mpsc};
    use std::thread;
    #[test]fn source_admission_fails_closed_on_restore_rate_or_recovery(){for flags in 0..8{assert_eq!(may_admit_source(true,7,7,flags&1!=0,flags&2!=0,flags&4!=0),flags==0);}assert!(!may_admit_source(false,7,7,false,false,false));assert!(!may_admit_source(true,8,7,false,false,false));}
    #[test]fn rapid_local_network_mode_switch_only_admits_latest_generation(){let wanted=AtomicBool::new(true);let generation=AtomicU32::new(u32::MAX);let mut pending=vec![("local1",u32::MAX)];for source in ["local2","network","local3"]{let request=generation.fetch_add(1,Ordering::AcqRel).wrapping_add(1);pending.push((source,request));}let admitted=pending.iter().filter(|(_,request)|may_admit_source(wanted.load(Ordering::Acquire),generation.load(Ordering::Acquire),*request,false,false,false)).map(|(source,_)|*source).collect::<Vec<_>>();assert_eq!(admitted,["local3"]);cancel(&wanted,&generation);assert!(pending.iter().all(|(_,request)|!may_admit_source(wanted.load(Ordering::Acquire),generation.load(Ordering::Acquire),*request,false,false,false)));}
    #[test]fn recovery_quarantine_cannot_be_bypassed_by_a_new_source_token(){let wanted=AtomicBool::new(true);let generation=AtomicU32::new(10);cancel(&wanted,&generation);wanted.store(true,Ordering::Release);let fresh=generation.fetch_add(1,Ordering::AcqRel).wrapping_add(1);assert!(!may_admit_source(true,fresh,fresh,false,false,true));assert!(!may_admit_source(true,fresh,fresh,false,true,false));}
    #[test]fn e_then_x_restores_local_menu_even_after_worker_has_stopped(){assert!(requires_local_exit(true,true,true));assert!(requires_local_exit(false,true,true));assert!(requires_local_exit(false,false,true));assert!(!requires_local_exit(false,false,false));}
    #[test]fn e_then_c_uses_normal_network_disconnect_after_source_admission(){let wanted=AtomicBool::new(true);let generation=AtomicU32::new(7);cancel(&wanted,&generation);assert!(requires_local_exit(false,false,true));wanted.store(true,Ordering::Release);let network=generation.fetch_add(1,Ordering::AcqRel).wrapping_add(1);assert!(may_admit_source(true,network,network,false,false,false));let network_admitted_local_context=false;assert!(!requires_local_exit(false,false,network_admitted_local_context));}
    #[test] fn stale_worker_cannot_start_after_serialized_cancel_and_selection() {
        let lock=Arc::new(Mutex::new(())); let wanted=Arc::new(AtomicBool::new(true));
        let generation=Arc::new(AtomicU32::new(7)); let (tx,rx)=mpsc::channel();
        let guard=lock.lock().unwrap(); cancel(&wanted,&generation);
        let (l,w,g)=(lock.clone(),wanted.clone(),generation.clone());
        let worker=thread::spawn(move || { tx.send(()).unwrap(); let _g=l.lock().unwrap();
            may_admit(w.load(Ordering::Acquire),g.load(Ordering::Acquire),7) });
        rx.recv().unwrap(); assert!(!wanted.load(Ordering::Acquire));
        // A clock selection may publish here under the same guard.
        drop(guard); assert!(!worker.join().unwrap());
    }
    #[test] fn selector_cannot_observe_idle_while_admitted_worker_is_running() {
        let lock=Arc::new(Mutex::new(())); let active=Arc::new(AtomicBool::new(false));
        let guard=lock.lock().unwrap();
        assert!(may_admit(true,3,3)); active.store(true,Ordering::Release);
        let (tx,rx)=mpsc::channel(); let (l,a)=(lock.clone(),active.clone());
        let selector=thread::spawn(move || { tx.send(()).unwrap(); let _g=l.lock().unwrap(); !a.load(Ordering::Acquire) });
        rx.recv().unwrap(); drop(guard); assert!(!selector.join().unwrap());
    }
    #[test] fn cancellation_invalidates_pending_even_at_generation_wrap() {
        let w=AtomicBool::new(true); let g=AtomicU32::new(u32::MAX);
        cancel(&w,&g); assert_eq!(g.load(Ordering::Acquire),0);
        assert!(!may_admit(w.load(Ordering::Acquire),g.load(Ordering::Acquire),u32::MAX));
    }
    #[test] fn benchmark_publication_excludes_selector_until_finished() {
        let lock=Arc::new(Mutex::new(())); let benchmark=Arc::new(AtomicBool::new(false));
        let guard=lock.lock().unwrap(); benchmark.store(true,Ordering::Release);
        let (tx,rx)=mpsc::channel(); let (l,b)=(lock.clone(),benchmark.clone());
        let selector=thread::spawn(move || { tx.send(()).unwrap(); let _g=l.lock().unwrap(); !b.load(Ordering::Acquire) });
        rx.recv().unwrap(); drop(guard); assert!(!selector.join().unwrap());
        benchmark.store(false,Ordering::Release);
        let _g=lock.lock().unwrap(); assert!(!benchmark.load(Ordering::Acquire));
    }
    #[test] fn reservation_releases_on_success_error_and_unwind() {
        let flag=AtomicBool::new(false);
        { let _r=RateReservation::acquire(&flag).unwrap(); assert!(flag.load(Ordering::Acquire));
          assert!(RateReservation::acquire(&flag).is_none()); }
        assert!(!flag.load(Ordering::Acquire));
        fn fail(flag:&AtomicBool)->Result<(),()> { let _r=RateReservation::acquire(flag).ok_or(())?; Err(()) }
        assert_eq!(fail(&flag),Err(())); assert!(!flag.load(Ordering::Acquire));
        let _=std::panic::catch_unwind(|| { let _r=RateReservation::acquire(&flag).unwrap(); panic!("injected"); });
        assert!(!flag.load(Ordering::Acquire));
    }
    #[test] fn reservation_blocks_admission_without_holding_control_during_io() {
        let control=Arc::new(Mutex::new(())); let flag=Arc::new(AtomicBool::new(false));
        let reservation={ let _g=control.lock().unwrap(); RateReservation::acquire(&flag).unwrap() };
        let (c,f)=(control.clone(),flag.clone());
        let admission=thread::spawn(move || { let _g=c.lock().unwrap(); !f.load(Ordering::Acquire) });
        assert!(!admission.join().unwrap()); // CONTROL was available, reservation blocked admission.
        drop(reservation);
        let _g=control.lock().unwrap(); assert!(!flag.load(Ordering::Acquire));
    }
}
