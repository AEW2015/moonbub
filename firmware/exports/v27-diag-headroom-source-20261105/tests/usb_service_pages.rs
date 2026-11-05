#![allow(dead_code)]
extern crate self as log;
use std::sync::{Mutex,atomic::{AtomicU32,Ordering}};
#[path="../handheld/src/streaming/audio_io.rs"]mod audio_io;
#[path="../handheld/src/streaming/audio_diag.rs"]mod audio_diag;
#[path="../handheld/src/streaming/service_policy.rs"]mod service_policy;
use audio_diag::{Diagnostics,DropRecord,Reason};
static DIAGNOSTICS:Mutex<Diagnostics>=Mutex::new(Diagnostics::new());static DIAG_PAGE:AtomicU32=AtomicU32::new(0);static OUTPUT:Mutex<Vec<String>>=Mutex::new(Vec::new());
#[macro_export]macro_rules!info{($($arg:tt)*)=>{crate::capture(format!($($arg)*))}}
fn capture(text:String){assert!(DIAGNOSTICS.try_lock().is_ok(),"logging while diagnostic mutex held");OUTPUT.lock().unwrap().push(text);}
pub fn log_diagnostics() {
    match DIAG_PAGE.fetch_add(1, Ordering::Relaxed) % 8 {
        0 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (
                    d.session_serial,
                    d.valid_audio,
                    d.enqueued,
                    d.dequeued,
                    d.queued,
                    d.queue_high,
                    d.busy_deferrals,
                    d.stale_or_foreign,
                    d.malformed,
                )
            };
            log::info!("USB_TRACE avq page=queue serial={} valid={} in={} out={} queued={} high={} busy_defer={} stale_foreign={} malformed={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8);
        }
        1 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (
                    d.lock_misses,
                    d.max_consecutive_misses,
                    d.successful_steps,
                    d.max_pending_us,
                    d.max_phase_us,
                    d.max_lock_hold_us,
                    d.max_loop_gap_us,
                    d.max_arrival_gap_us,
                    d.task_priority,
                    d.task_core,
                )
            };
            log::info!("USB_TRACE avq page=steps miss={} burst={} steps={} pending_max_us={} phase_max_us={} held_max_us={} loop_gap_us={} arrival_gap_us={} prio={} core_sample={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8,x.9);
        }
        2 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (
                    d.snapshot_ok,
                    d.snapshot_lock_miss,
                    d.snapshot_io,
                    d.snapshot_identity,
                    d.snapshot_offline,
                    d.snapshot_changed,
                    d.snapshot_range,
                    d.max_snapshot_us,
                )
            };
            log::info!("USB_TRACE avq page=snapshot ok={} miss={} io={:?} identity={} offline={} changed={} range={} max_us={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7);
        }
        3 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (d.drops, d.control_faults, d.io_faults, d.max_queue_age_us)
            };
            log::info!("USB_TRACE avq page=drops order=full,age,ima,unusable,fpga,io,timeout,cancel,end,source,idle counts={:?} control_fault={} io_fault={} queue_age_max_us={}",x.0,x.1,x.2,x.3);
        }
        4 => {
            let record = DIAGNOSTICS.lock().unwrap().first;
            log::info!("USB_TRACE avq page=FIRST drop={:?}", record);
        }
        5 => {
            let record = DIAGNOSTICS.lock().unwrap().last;
            log::info!("USB_TRACE avq page=LAST drop={:?}", record);
        }
        6 => {
            let x = { let d = DIAGNOSTICS.lock().unwrap(); let s = d.service;
                (s.passes,s.attempts,s.progress,s.lock_deferrals,s.phase_deferrals,s.attempt_budget_ends,s.time_budget_ends,s.max_pass_us,s.rx_budget_ends) };
            log::info!("USB_TRACE avq page=service passes={} attempts={} progress={} lock_defer={} phase_defer={} attempts_end={} time_end={} max_us={} rx_end={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8);
        }
        _ => {
            let x = { let d = DIAGNOSTICS.lock().unwrap(); let i = d.input;
                (i.attempts,i.sent,i.errors,i.encode_errors,i.short_sends,i.sequence_gaps,i.late_attempts,i.missed_periods,i.max_lateness_us,i.max_success_gap_us) };
            log::info!("USB_TRACE avq page=input attempts={} sent={} errors={} encode={} short={} seq_gaps={} late={} missed_periods={} lateness_max_us={} send_gap_max_us={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8,x.9);
        }
    }
}

#[test]fn actual_production_pages_are_bounded_and_first_last_sequence_preserved(){let mut d=DIAGNOSTICS.lock().unwrap();d.session_serial=u32::MAX;d.snapshot_ok=u32::MAX;d.snapshot_lock_miss=u32::MAX;d.snapshot_identity=u32::MAX;d.snapshot_offline=u32::MAX;d.snapshot_changed=u32::MAX;d.snapshot_range=u32::MAX;d.max_snapshot_us=u64::MAX;d.control_faults=u32::MAX;d.io_faults=u32::MAX;d.max_queue_age_us=u64::MAX;d.task_priority=u32::MAX;d.task_core=u32::MAX;d.valid_audio=u32::MAX;d.enqueued=u32::MAX;d.dequeued=u32::MAX;d.queued=4;d.queue_high=4;d.busy_deferrals=u32::MAX;d.stale_or_foreign=u32::MAX;d.malformed=u32::MAX;d.lock_misses=u32::MAX;d.max_consecutive_misses=u32::MAX;d.successful_steps=u32::MAX;d.max_pending_us=u64::MAX;d.max_phase_us=u64::MAX;d.max_lock_hold_us=u64::MAX;d.max_loop_gap_us=u64::MAX;d.max_arrival_gap_us=u64::MAX;d.snapshot_io=[u32::MAX;10];d.drops=[u32::MAX;11];d.first=Some(DropRecord{sequence:0,monotonic_us:u64::MAX,reason:Reason::SourceMismatch,phase:audio_io::Phase::ReceiptSession,pending_age_us:u64::MAX,queued_count:4,session_serial:u32::MAX});let mut last=d.first.unwrap();last.sequence=u32::MAX;d.last=Some(last);d.service.passes=u32::MAX;d.service.attempts=u32::MAX;d.service.progress=u32::MAX;d.service.lock_deferrals=u32::MAX;d.service.phase_deferrals=u32::MAX;d.service.attempt_budget_ends=u32::MAX;d.service.time_budget_ends=u32::MAX;d.service.max_pass_us=u64::MAX;d.service.rx_budget_ends=u32::MAX;d.input.attempts=u32::MAX;d.input.sent=u32::MAX;d.input.errors=u32::MAX;d.input.encode_errors=u32::MAX;d.input.short_sends=u32::MAX;d.input.sequence_gaps=u32::MAX;d.input.late_attempts=u32::MAX;d.input.missed_periods=u32::MAX;d.input.max_lateness_us=u64::MAX;d.input.max_success_gap_us=u64::MAX;drop(d);for _ in 0..8{log_diagnostics();}let lines=OUTPUT.lock().unwrap();assert_eq!(lines.len(),8);for line in lines.iter(){assert!(line.len()+48<512,"oversize{}",line.len());}assert!(lines[4].contains("sequence: 0"));assert!(lines[5].contains("sequence: 4294967295"));}
