//! Fixed retained diagnostics. No hardware access, allocation, worker thread or lease mutation.
use core::fmt::{self,Arguments,Write};
use std::sync::Mutex;
use super::{network_driver::{self,Error,Header,Report,Source},report_export};

pub const EXPORT_INTERVAL_MS:u64=40;
#[derive(Clone,Copy,Debug,Default)]pub struct Health{pub reads:u64,pub writes:u64,pub qspi:u64,pub free:usize,pub largest:usize,pub stack_low:usize,pub min_free:usize}
#[derive(Clone,Copy,Debug,Default)]pub struct Progress{
 pub active_valid:bool,pub ordinal:u32,pub frame_id:u32,pub generation:u64,pub phase:u8,pub at_us:u64,
 pub current_length:u32,pub read_bytes:u64,pub stored_prefix:u32,pub presentation_acks:u32,
}
pub struct RecordingSource<S>{pub inner:S,pub progress:Progress}
impl<S> RecordingSource<S>{pub fn new(inner:S)->Self{Self{inner,progress:Progress::default()}}}
impl<S:Source> Source for RecordingSource<S>{
 fn header(&mut self)->Result<Header,Error>{let h=self.inner.header()?;self.progress.current_length=h.length as u32;self.progress.stored_prefix=0;Ok(h)}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,Error>{let n=self.inner.read(offset,out)?;self.progress.read_bytes=self.progress.read_bytes.saturating_add(n as u64);Ok(n)}
 fn stored(&mut self,next:usize)->Result<(),Error>{self.inner.stored(next)?;self.progress.stored_prefix=next as u32;Ok(())}
 fn presented(&mut self)->Result<(),Error>{self.inner.presented()?;self.progress.presentation_acks=self.progress.presentation_acks.saturating_add(1);Ok(())}
 fn active(&mut self,ordinal:u32,frame_id:u32,generation:u64,phase:u8,at_us:u64){
  self.progress.active_valid=true;self.progress.ordinal=ordinal;self.progress.frame_id=frame_id;self.progress.generation=generation;self.progress.phase=phase;self.progress.at_us=at_us;
  self.inner.active(ordinal,frame_id,generation,phase,at_us);
 }
}
#[derive(Clone,Copy)]pub struct PassiveFpga{pub values:[Result<u32,Error>;6]}
impl PassiveFpga{pub fn read_once(bus:&mut impl super::local::Bus)->Self{Self{values:[bus.read(0x350),bus.read(0x354),bus.read(0x358),bus.read(0x35c),bus.read(0x360),bus.read(0x110)]}}}
#[derive(Clone,Copy)]pub struct Snapshot{pub native:Option<super::hud::Diagnostics>,pub fpga:Option<PassiveFpga>,pub report:Option<Report>,pub error:Option<Error>,pub health:Health,pub progress:Progress}
impl Snapshot{
 pub fn result(result:Result<&Report,&Error>,health:Health,progress:Progress)->Self{
  match result{Ok(r)=>Self{native:None,fpga:None,report:Some(*r),error:None,health,progress},Err(e)=>Self{native:None,fpga:None,report:None,error:Some(*e),health,progress}}
 }
 pub fn with_diagnostics(mut self,n:super::hud::Diagnostics,f:Option<PassiveFpga>)->Self{self.native=Some(n);self.fpga=f;self}
 fn lines(&self,mut emit:impl FnMut(Arguments<'_>)){
  match(&self.report,&self.error){(Some(r),None)=>report_export::report(r,|a|emit(a)),(None,Some(e))=>report_export::failure(e,|a|emit(a)),_=>emit(format_args!("snapshot_error inconsistent_outcome=true"))}
  if let Some(n)=self.native{
   emit(format_args!("native valid={} stage={} ffi={} op={} reply={} mask={:x}",n.valid,n.stage,n.ffi,n.opcode,n.reply,n.payload_mask));
   emit(format_args!("native_reply valid={} tag_valid={} written={} expected_tag={} observed_tag={}",n.reply_valid,n.tag_valid,n.written,Hex(&n.expected_tag),Hex(&n.observed_tag)));
   emit(format_args!("native_gate_tag words={:08x}/{:08x}/{:08x}/{:08x}",n.native[16],n.native[17],n.native[18],n.native[19]));
   emit(format_args!("native_accepted valid={} generation={} frame={} reference={}",n.native[23],n.native[20],n.native[21],n.native[22]));
   emit(format_args!("native_call valid={} generation={} frame={} reference={}",n.identity_valid,n.generation,n.frame,n.reference));
   emit(format_args!("native_gate phase={} verified={} frame={} reference={} generation={} words={}",n.native[0],n.native[1],n.native[2],n.native[3],n.native[4],n.native[5]));
   emit(format_args!("native_alloc kind={} requested={} live={} free={} largest={} probes={}",n.native[6],n.native[7],n.native[8],n.native[9],n.native[10],n.native[15]));
   emit(format_args!("native_stats limit={} live={} peak={} maximum={} allocations={} failures={}",n.stats[0],n.stats[1],n.stats[2],n.stats[3],n.stats[4],n.stats[5]));
   emit(format_args!("native_text bytes={} copied={} truncated={}",n.text_length,n.text_length.min(96),n.text_length>96));
   for i in 0..3{let end=n.text_length.min(96).min((i+1)*32);let start=(i*32).min(end);emit(format_args!("native_text part={} hex={}",i,Hex(&n.text[start..end])));}
  }
  if let Some(f)=self.fpga{for(i,v)in f.values.iter().enumerate(){emit(format_args!("fpga_passive field={} result={:?}",i,v));}}
  let p=self.progress;
  emit(format_args!("active valid={} ordinal={} id={} generation={}",p.active_valid,p.ordinal,p.frame_id,p.generation));
  emit(format_args!("progress phase={} at_us={} length={} stored={} read_bytes={} acked={}",p.phase,p.at_us,p.current_length,p.stored_prefix,p.read_bytes,p.presentation_acks));
  let h=self.health;report_export::health(h.reads,h.writes,h.qspi,h.free,h.largest,h.stack_low,h.min_free,|a|emit(a));
 }
}
struct Hex<'a>(&'a[u8]);
impl fmt::Display for Hex<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{for b in self.0{write!(f,"{:02x}",b)?;}Ok(())}}
struct Digest(u32);
impl Write for Digest{fn write_str(&mut self,s:&str)->fmt::Result{for b in s.bytes(){self.0=(self.0^b as u32).wrapping_mul(16777619);}Ok(())}}
fn metadata(snapshot:&Snapshot)->(u16,u32){let(mut n,mut digest)=(0u16,Digest(2166136261));snapshot.lines(|a|{n+=1;let _=digest.write_fmt(a);let _=digest.write_str("\n");});(n,digest.0)}
#[derive(Clone,Copy)]struct Cursor{epoch:u32,attempt:u32,count:u16,hash:u32,next:u16,due_ms:u64}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum ExportError{Busy,NoSnapshot,EpochExhausted,AttemptExhausted}
pub struct Store{epoch:u32,attempt:u32,snapshot:Option<Snapshot>,cursor:Option<Cursor>}
impl Store{
 pub const fn new()->Self{Self{epoch:0,attempt:0,snapshot:None,cursor:None}}
 pub fn publish(&mut self,snapshot:Snapshot,now_ms:u64)->Result<u32,ExportError>{
  if self.cursor.is_some(){return Err(ExportError::Busy)}
  let epoch=self.epoch.checked_add(1).ok_or(ExportError::EpochExhausted)?;
  self.epoch=epoch;self.attempt=0;self.snapshot=Some(snapshot);self.request(now_ms)
 }
 pub fn request(&mut self,now_ms:u64)->Result<u32,ExportError>{
  if self.cursor.is_some(){return Err(ExportError::Busy)}
  let snapshot=self.snapshot.as_ref().ok_or(ExportError::NoSnapshot)?;
  let attempt=self.attempt.checked_add(1).ok_or(ExportError::AttemptExhausted)?;
  let(count,hash)=metadata(snapshot);self.attempt=attempt;
  self.cursor=Some(Cursor{epoch:self.epoch,attempt,count,hash,next:0,due_ms:now_ms});Ok(self.epoch)
 }
 pub fn busy(&self)->bool{self.cursor.is_some()}
 /// At most one record/call, even if the caller was delayed. No catch-up burst.
 pub fn tick(&mut self,now_ms:u64,mut emit:impl FnMut(Arguments<'_>))->bool{
  let Some(mut c)=self.cursor else{return false};if now_ms<c.due_ms{return false}
  if c.next==0{emit(format_args!("DY45 BEGIN e={} a={} n={} hash={:08x} tx_loss=unknown",c.epoch,c.attempt,c.count,c.hash));}
  else if c.next==c.count+1{emit(format_args!("DY45 END e={} a={} n={} hash={:08x} tx_loss=unknown",c.epoch,c.attempt,c.count,c.hash));}
  else{
   let wanted=c.next-1;let mut index=0u16;
   if let Some(snapshot)=&self.snapshot{snapshot.lines(|a|{if index==wanted{emit(format_args!("DY45 e={} a={} i={} n={} {}",c.epoch,c.attempt,index,c.count,a));}index+=1;});}
  }
  c.next+=1;c.due_ms=now_ms.saturating_add(EXPORT_INTERVAL_MS);
  self.cursor=if c.next>c.count+1{None}else{Some(c)};true
 }
}
static SAVED:Mutex<Store>=Mutex::new(Store::new());
pub fn publish(snapshot:Snapshot,now_ms:u64)->Result<u32,ExportError>{SAVED.lock().unwrap().publish(snapshot,now_ms)}
pub fn request(now_ms:u64)->Result<u32,ExportError>{SAVED.lock().unwrap().request(now_ms)}
pub fn exporting()->bool{SAVED.lock().unwrap().busy()}
pub fn tick(now_ms:u64,emit:impl FnMut(Arguments<'_>))->bool{SAVED.lock().unwrap().tick(now_ms,emit)}

// Phase values are the actual driver's observational hook, not inferred completion.
pub const PRESENTED_PHASE:u8=network_driver::phase::PRESENTED;
