//! Explicit local USB lab controls. No persistent config changes or lease release.
use crate::lab_control_line::{Action,Event,Parser,Request};
use std::net::Ipv4Addr;
use std::sync::atomic::{AtomicU32,Ordering};
static HOST:AtomicU32=AtomicU32::new(0);
pub fn host_override()->Option<Ipv4Addr>{let n=HOST.load(Ordering::Acquire);if n==0{None}else{Some(Ipv4Addr::from(n))}}
pub struct Driver{parser:Parser}
fn now_ms()->u64{unsafe{esp_idf_svc::sys::esp_timer_get_time()as u64/1000}}
impl Driver{
 pub fn new()->Self{Self{parser:Parser::new()}}
 pub fn tick(&mut self){handle(self.parser.tick(now_ms()));}
 pub fn command(&mut self,b:u8)->bool{let e=self.parser.feed(b,now_ms());if e==Event::Pass{false}else{handle(e);true}}
}
fn handle(e:Event){if let Event::Complete(result)=e{match result{Ok(r)=>dispatch(r),Err(e)=>log::info!("MBLAB1 nonce=0000000000000000 action=INVALID result={:?}",e)}}}
fn dispatch(r:Request){
 let action=match r.action{Action::Ping=>"PING",Action::Reboot=>"REBOOT",Action::Dfu=>"DFU",Action::Host33=>"HOST33",Action::Host47=>"HOST47"};
 if r.action==Action::Ping{log::info!("MBLAB1 nonce={:016x} action={} result=OK",r.nonce,action);return}
 let completed=crate::cu66::network_usb::lab_completed();
 let ready=crate::streaming::diagnostic_trace_idle()
     && !crate::cu66::report_snapshot::exporting()
     && crate::core_coordinator::CONTROL.lock().unwrap().lab_reboot_quiet(completed);
 if !ready || (crate::cu66::network_usb::lab_active()&&!completed) {
  log::info!("MBLAB1 nonce={:016x} action={} result=BUSY",r.nonce,action);return
 }
 match r.action{
  Action::Host33|Action::Host47=>{
   if crate::cu66::network_usb::lab_active(){log::info!("MBLAB1 nonce={:016x} action={} result=BUSY",r.nonce,action);return}
   let last=if r.action==Action::Host33{33}else{47};HOST.store(u32::from(Ipv4Addr::new(192,168,0,last)),Ordering::Release);
   log::info!("MBLAB1 nonce={:016x} action={} result=OK",r.nonce,action);
  }
  Action::Reboot|Action::Dfu=>{
   // Recovery is an explicit whole-system restart, never a forged commit/abort.
   if !crate::core_coordinator::CONTROL.lock().unwrap().lab_reboot_begin(completed){log::info!("MBLAB1 nonce={:016x} action={} result=BUSY",r.nonce,action);return}
   if crate::control::schedule_lab_reboot(r.action==Action::Dfu).is_ok(){
    log::info!("MBLAB1 nonce={:016x} action={} result=OK",r.nonce,action);
   }else{
    crate::core_coordinator::CONTROL.lock().unwrap().lab_reboot_cancel();
    log::info!("MBLAB1 nonce={:016x} action={} result=ERROR",r.nonce,action);
   }
  }
  Action::Ping=>{}
 }
}
