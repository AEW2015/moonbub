//! P starts one observation, subsequent P pages the retained cache.
//! No worker, decoder command, autoprogramming, or unbounded log burst.
use crate::{cpl1::*,core_coordinator::CONTROL,core_admission::DiagnosticPermit,device::{Device,drivers::fpga::{FpgaSpiWordSize,SpiCommand,MAX_SPI_READ_CLOCK}}};
use std::sync::Mutex;
struct State{cookies:Cookies,capture:Option<Capture>,cached:Option<Snapshot>,page:usize,permit:Option<DiagnosticPermit>}
static STATE:Mutex<State>=Mutex::new(State{cookies:Cookies::new(),capture:None,cached:None,page:0,permit:None});
fn now()->u64{unsafe{esp_idf_svc::sys::esp_timer_get_time() as u64}}
struct Adapter<'a,'b>(&'a mut Device<'b>);
impl Bus for Adapter<'_,'_>{
 fn read(&mut self,o:u32)->Result<u32,()>{self.0.fpga.read_u32(0xe0000000+o).map_err(|_|())}
 fn capture(&mut self,c:u32)->Result<(),()>{self.0.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000500,&c.to_be_bytes()).map_err(|_|())}
}
fn release(s:&mut State){if let Some(p)=s.permit.take(){let failed=CONTROL.lock().unwrap().unissued_diagnostic_finished(p).is_err();if failed{CONTROL.lock().unwrap().quarantine();}}}
#[inline(never)]
pub fn command(){
 if !crate::streaming::diagnostic_trace_idle(){log::info!("USB_TRACE cpl1 v=1 result=busy");return}
 let Ok(mut s)=STATE.try_lock() else{return};
 if let Some(snapshot)=s.cached{
  let page=s.page;s.page=(page+1)%10;if page==9{s.cached=None;}
  // Drop state/device/control before logger formatting/delivery.
  drop(s);
  if let Ok(line)=crate::cpl1::page(&snapshot,page){log::info!("{}",line.as_str())}
  return
 }
 if s.capture.is_some(){log::info!("USB_TRACE cpl1 v=1 result=pending");return}
 let permit={CONTROL.lock().unwrap().diagnostic()};
 let Ok(permit)=permit else{log::info!("USB_TRACE cpl1 v=1 result=busy");return};
 s.permit=Some(permit);
 let result=if let Some(mut d)=Device::try_lock(){let epoch=d.fpga.program_epoch();Capture::begin(&mut Adapter(&mut d),&mut s.cookies,now(),epoch)}else{Err(Error::Io)};
 match result{Ok(c)=>{if c.expired(now()){release(&mut s);drop(s);log::info!("USB_TRACE cpl1 v=1 result=Timeout");}else{s.capture=Some(c);drop(s);log::info!("USB_TRACE cpl1 v=1 result=capturing");}},Err(e)=>{release(&mut s);drop(s);log::info!("USB_TRACE cpl1 v=1 result={:?}",e);}}
}
#[inline(never)]
pub fn tick(){
 let Ok(mut s)=STATE.try_lock() else{return};
 let Some(mut c)=s.capture.take() else{return};
 if !crate::streaming::diagnostic_trace_idle(){release(&mut s);drop(s);log::info!("USB_TRACE cpl1 v=1 result=busy");return}
 let result=if let Some(mut d)=Device::try_lock(){let epoch=d.fpga.program_epoch();c.step(&mut Adapter(&mut d),now(),epoch)}else{
  // Preserve deadline across contention, no sleeps under any lock.
  if c.expired(now()){release(&mut s);drop(s);log::info!("USB_TRACE cpl1 v=1 result=Timeout");return}
  s.capture=Some(c);return
 };
 let result=if c.expired(now()){Err(Error::Timeout)}else{result};
 match result{
  Ok(None)=>s.capture=Some(c),
  Ok(Some(snapshot))=>{s.cached=Some(snapshot);release(&mut s);drop(s);log::info!("USB_TRACE cpl1 v=1 result=retained pages=10");},
  Err(e)=>{release(&mut s);drop(s);log::info!("USB_TRACE cpl1 v=1 result={:?}",e);}
 }
}