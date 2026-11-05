extern crate self as log;
extern crate self as esp_idf_svc;
use std::sync::{Mutex,atomic::{AtomicBool,Ordering}};
static LINES:Mutex<Vec<String>>=Mutex::new(Vec::new());
static IDLE:AtomicBool=AtomicBool::new(true);
#[macro_export] macro_rules! info {($($args:tt)*)=>{{$crate::LINES.lock().unwrap().push(format!($($args)*));}};}
pub mod sys {pub unsafe fn esp_timer_get_time()->i64{1000000}}
#[path="../handheld/src/streaming/diagnostic_trace.rs"]pub mod trace_impl;
mod streaming {
    pub use crate::trace_impl as diagnostic_trace;
    pub fn diagnostic_trace_idle()->bool{crate::IDLE.load(crate::Ordering::Relaxed)}
}
#[path="../handheld/src/video_trace_usb.rs"]mod usb;
fn reset(){IDLE.store(true,Ordering::Relaxed);LINES.lock().unwrap().clear();usb::command(b'F');usb::command(b'M');LINES.lock().unwrap().clear();}
#[test]fn busy_arm_does_not_erase(){reset();let epoch=trace_impl::summary().unwrap().epoch;IDLE.store(false,Ordering::Relaxed);usb::command(b'M');assert_eq!(trace_impl::summary().unwrap().epoch,epoch);assert!(LINES.lock().unwrap()[0].contains("result=busy"));}
#[test]fn export_requires_stop_and_freeze(){reset();usb::command(b'K');assert!(LINES.lock().unwrap().last().unwrap().contains("not_frozen"));usb::command(b'F');IDLE.store(false,Ordering::Relaxed);usb::command(b'K');assert!(LINES.lock().unwrap().last().unwrap().contains("result=busy"));}
#[test]fn stable_record_pages_and_bounded_lines(){
 reset();use trace_impl::*;
 let p=Position{frame:u32::MAX,offset:u32::MAX,frame_valid:true,offset_valid:true};
 let c=Context{incoming:p,active:p,queued:u32::MAX,queue_valid:true};
 let mut e=Event::new(Kind::Failure,u64::MAX-2,c);e.received_us=u64::MAX-3;e.detail=u16::MAX;e.lock_us=u64::MAX;e.qspi_us=u64::MAX;record(e);
 usb::command(b'F');LINES.lock().unwrap().clear();
 for _ in 0..9{usb::command(b'K');}
 let lines=LINES.lock().unwrap();assert_eq!(lines.len(),9);
 for (i,line) in lines.iter().enumerate(){assert!(line.len()+64<=320,"{} bytes: {}",line.len(),line);assert!(line.contains("epoch="));assert!(line.contains("seq="));if i<5{assert!(line.contains(&format!("e=0 p={}",i)));}else{assert!(line.contains(&format!("f=0 p={}",i-5)));}}
 drop(lines);let before=summary().unwrap();usb::command(b'K');assert_eq!(summary().unwrap().first_sequence,before.first_sequence);assert_eq!(summary().unwrap().last_sequence,before.last_sequence);
}
#[test]fn summary_is_paged_without_ring_copy(){reset();usb::command(b'F');LINES.lock().unwrap().clear();for _ in 0..(17+trace_impl::PHASE_COUNT){usb::command(b'J');}let lines=LINES.lock().unwrap();assert_eq!(lines.len(),17+trace_impl::PHASE_COUNT);for(i,line)in lines.iter().enumerate(){assert!(line.contains(&format!("s={} ",i)));assert!(line.len()+64<=320);}}

#[test]fn summary_requires_quiet_receiver(){reset();IDLE.store(false,Ordering::Relaxed);usb::command(b'J');assert!(LINES.lock().unwrap().last().unwrap().contains("result=busy"));}

#[test]fn v2_exports_per_kind_counts_on_bounded_versioned_pages(){
 reset();use trace_impl::*;
 TRACE.with_test_lock(||assert!(!record(Event::new(Kind::Complete,50,Context::UNKNOWN))));
 usb::command(b'F');LINES.lock().unwrap().clear();
 for _ in 0..33{usb::command(b'J');}
 let lines=LINES.lock().unwrap();assert_eq!(lines.len(),33);
 assert!(lines.iter().all(|line|line.contains("rxdiag v=2")));
 assert!(lines[0].contains("pages=33"));
 assert!(lines[31].contains("kind=6 lost=1 loss_valid=true"));
 for line in lines.iter(){assert!(line.len()+64<=320,"{}",line);}
}
