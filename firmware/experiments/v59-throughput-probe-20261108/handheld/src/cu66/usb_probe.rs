//! USB W: explicit CPU-only key/P HU smoke, no FPGA/QSPI/network/file writes.
//! One bounded lazy worker; original JPEG/AV ownership gates are retained.
use super::{framing::{crc32,crc_extend,decode},hud::Hud};
use crate::{core_coordinator::CONTROL,diag_dispatch::{self,Launcher}};
use std::sync::mpsc;
static REQUESTS:diag_dispatch::Requests=diag_dispatch::Requests::new();
const STACK:usize=8192;
const KEY:&[u8]=include_bytes!("fixtures/prepare0.bin");
const PRED:&[u8]=include_bytes!("fixtures/prepare1.bin");
fn command(op:u8,g:u64,f:u32,r:u32,arg:u32,p:&[u8],b:&mut[u8;64])->usize{let n=32+p.len();b.fill(0);b[..4].copy_from_slice(b"HC70");b[4]=1;b[5]=op;b[8..12].copy_from_slice(&(p.len()as u32).to_le_bytes());b[12..20].copy_from_slice(&g.to_le_bytes());b[20..24].copy_from_slice(&f.to_le_bytes());b[24..28].copy_from_slice(&r.to_le_bytes());b[28..32].copy_from_slice(&arg.to_le_bytes());b[32..n].copy_from_slice(p);let crc=crc32(&b[..n]);b[n..n+4].copy_from_slice(&crc.to_le_bytes());n+4}
struct Spawn;
impl Launcher for Spawn{
 type Job=crate::core_admission::DiagnosticPermit;type Sender=mpsc::SyncSender<Self::Job>;
 fn reserve(&mut self)->Result<Self::Job,()>{CONTROL.lock().unwrap().diagnostic().map_err(|_|())}
 fn spawn_empty(&mut self)->Result<Self::Sender,()>{let(tx,rx)=mpsc::sync_channel(1);std::thread::Builder::new().name("Cu66HudProbe".into()).stack_size(STACK).spawn(move||{if let Ok(permit)=rx.recv(){worker();if CONTROL.lock().unwrap().unissued_diagnostic_finished(permit).is_err(){CONTROL.lock().unwrap().quarantine();}REQUESTS.finished();}}).map_err(|_|())?;Ok(tx)}
 fn send(&mut self,tx:&Self::Sender,p:Self::Job)->Result<(),Self::Job>{tx.send(p).map_err(|e|e.0)}
 fn release_unissued(&mut self,p:Self::Job)->bool{CONTROL.lock().unwrap().unissued_diagnostic_finished(p).is_ok()}
 fn publish(&mut self,tx:Self::Sender){drop(tx)}
}
fn heap()->usize{unsafe{esp_idf_svc::sys::heap_caps_get_free_size((esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32)}}
pub fn start(){let free=heap();if free<150_000{log::info!("USB_CU66_HUD result=heap_budget free={} required=150000",free);return}if !crate::streaming::diagnostic_trace_idle(){log::info!("USB_CU66_HUD result=busy");return}let result=diag_dispatch::launch(&REQUESTS,&mut Spawn);log::info!("USB_CU66_HUD launch={:?} hardware_access=false",result);}
#[inline(never)]fn worker(){
 let start=unsafe{esp_idf_svc::sys::esp_timer_get_time()};
 let result=run();let stack=unsafe{esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())};
 log::info!("USB_CU66_HUD result={:?} elapsed_us={} stack_low={} hardware_access=false network_capability=false",result,unsafe{esp_idf_svc::sys::esp_timer_get_time()}-start,stack);
}
#[inline(never)]fn run()->Result<[usize;6],&'static str>{
 let mut hud=Hud::new(131072).map_err(|_|"allocation")?;let mut out=[0u8;1060];let mut req=[0u8;64];
 let cases=[(KEY,897877670),(PRED,2601004892)];
 for(wire,expected)in cases{
  let id=decode(wire).map_err(|_|"fixture")?;
  let begin=unsafe{esp_idf_svc::sys::esp_timer_get_time()};
  let r=hud.transact(wire,&mut out).map_err(|_|"prepare")?;if decode(r).map_err(|_|"reply")?.argument!=0{return Err("semantic")}
  let cpu=unsafe{esp_idf_svc::sys::esp_timer_get_time()}-begin;let mut crc=!0;
  for offset in (0u32..21120).step_by(512){let count=(21120-offset).min(512);let mut payload=[0u8;8];payload[..4].copy_from_slice(&offset.to_le_bytes());payload[4..].copy_from_slice(&count.to_le_bytes());let n=command(3,id.generation,id.frame,id.reference,0,&payload,&mut req);let r=hud.transact(&req[..n],&mut out).map_err(|_|"read")?;let r=decode(r).map_err(|_|"read_reply")?;if r.argument!=0||r.payload.len()!=count as usize*2{return Err("read_length")}crc=crc_extend(crc,r.payload);}
  if !crc!=expected{return Err("readback_crc")}
  let mut ack=[0u8;20];ack[..4].copy_from_slice(&21120u32.to_le_bytes());ack[4..].copy_from_slice(&wire[32+38..32+54]);let n=command(4,id.generation,id.frame,id.reference,1,&ack,&mut req);
  if decode(hud.transact(&req[..n],&mut out).map_err(|_|"ack")?).map_err(|_|"ack_reply")?.argument!=0{return Err("ack_gate")}
  for _ in 0..2{let n=command(5,id.generation,id.frame,id.reference,0,&[],&mut req);if decode(hud.transact(&req[..n],&mut out).map_err(|_|"commit")?).map_err(|_|"commit_reply")?.argument!=0{return Err("commit_gate")}}
  log::info!("USB_CU66_HUD frame={} prepare_us={} read_words=21120 read_crc={:08x} allocator={:?}",id.frame,cpu,!crc,hud.stats().map_err(|_|"stats")?);
 }
 let stats=hud.stats().map_err(|_|"stats")?;
 drop(hud);
 // Exercise actual C++ throw/catch on the target, with allocation space still available.
 let before_negative=heap();
 let mut limited=Hud::new(1024).map_err(|_|"negative_create")?;
 let before_throw=heap();
 let negative=decode(limited.transact(KEY,&mut out).map_err(|_|"negative_exception")?).map_err(|_|"negative_reply")?;
 if negative.argument!=4{return Err("allocation_not_rejected")}
 let failed=limited.stats().map_err(|_|"negative_stats")?;if failed[5]==0{return Err("missing_allocation_failure")}
 let after_throw=heap();drop(limited);let after_drop=heap();
 log::info!("USB_CU66_HUD caught_allocation_failure=true allocator={:?} heap_before_negative={} heap_before_throw={} heap_after_throw={} heap_after_drop={} heap_scope=raw_internal_getters",failed,before_negative,before_throw,after_throw,after_drop);
 Ok(stats)
}
