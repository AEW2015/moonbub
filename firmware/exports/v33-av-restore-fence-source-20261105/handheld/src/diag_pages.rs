//! Allocation-free ASCII diagnostic pages. No SDK, Device, heap or logging.
use core::fmt::{self, Write};
use crate::streaming::telemetry::FrameTrace;
pub const PAYLOAD_BYTES: usize = 192;
pub const LOG_FRAMING_RESERVE: usize = 64;
pub const VARIANT: &str = "v33-av-restore-fence-20261105";
#[derive(Clone, Copy)]
pub struct Context {pub capture: u32,pub generation: u32,pub epoch: u32,pub frame: u32}
pub struct Line {bytes:[u8;PAYLOAD_BYTES],length:usize}
impl Line {
 pub const fn new()->Self {Self{bytes:[0;PAYLOAD_BYTES],length:0}}
 pub fn as_str(&self)->&str {core::str::from_utf8(&self.bytes[..self.length]).unwrap_or("USB_D24 v=1 p=format_error")}
}
impl Write for Line {
 fn write_str(&mut self,s:&str)->fmt::Result {
  if !s.is_ascii() || s.contains(['\r','\n']) || self.length+s.len()>self.bytes.len(){return Err(fmt::Error)}
  self.bytes[self.length..self.length+s.len()].copy_from_slice(s.as_bytes());self.length+=s.len();Ok(())
 }
}
pub fn page(c:Context,name:&str,fields:fmt::Arguments<'_>)->Result<Line,fmt::Error>{
 let mut line=Line::new();
 write!(line,"USB_D24 v=1 c={} g={} e={} f={} p={} ",c.capture,c.generation,c.epoch,c.frame,name)?;
 line.write_fmt(fields)?;Ok(line)
}
/// Descriptor arrays have a fixed bound; no unbounded CStr walk or allocation.
pub struct Text<'a,T>(pub &'a [T]);
impl<T:Copy+Into<i16>> fmt::Display for Text<'_,T>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
 for &b in self.0 {let b=b.into() as u8;if b==0{break}let c=if (0x21..=0x7e).contains(&b){b as char}else{'_'};f.write_char(c)?;}Ok(())
}}
pub struct Hex<'a>(pub &'a [u8]);
impl fmt::Display for Hex<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{for b in self.0{write!(f,"{:02x}",b)?}Ok(())}}
pub fn app(c:Context,index:u8,project:&[core::ffi::c_char],version:&[core::ffi::c_char],idf:&[core::ffi::c_char],date:&[core::ffi::c_char],time:&[core::ffi::c_char],sha:&[u8;32])->Result<Line,fmt::Error>{
 match index{
  0=>page(c,"app",format_args!("project={} version={}",Text(project),Text(version))),
  1=>page(c,"sdk",format_args!("idf={} date={} time={}",Text(idf),Text(date),Text(time))),
  _=>page(c,"elf",format_args!("sdk_elf_sha256={}",Hex(sha))),
 }
}
pub fn boundary(c:Context,end:bool,generation_after:u32,epoch_after:u32)->Result<Line,fmt::Error>{
 if end{page(c,"end",format_args!("g_after={} e_after={} sampled=true",generation_after,epoch_after))}
 else{page(c,"begin",format_args!("sampled=true frame_epoch_binding=false"))}
}
pub fn runtime(c:Context,index:u8,reason:u32,uptime:u64,free:usize,largest:usize,usb_stack:u32)->Result<Line,fmt::Error>{
 match index{
  0=>page(c,"reset",format_args!("reason={} up_us={}",reason,uptime)),
  1=>page(c,"variant",format_args!("name={}",VARIANT)),
  _=>page(c,"memory",format_args!("free={} largest={} usb_stack={}",free,largest,usb_stack)),
 }
}
pub fn frame(c:Context,completed:bool,index:u8,t:&FrameTrace)->Result<Line,fmt::Error>{
 let names=if completed{["fc0","fc1","fc2","fc3","fc4","fc5","fc6"]}else{["fd0","fd1","fd2","fd3","fd4","fd5","fd6"]};
 let name=names[index.min(6) as usize];
 match index{
  0=>page(c,name,format_args!("valid={} packets={} bytes={}",t.valid,t.packets,t.bytes)),
  1=>page(c,name,format_args!("start={} last={} end={}",t.started_us,t.last_packet_us,t.finished_us)),
  2=>page(c,name,format_args!("gap_min={} gap_max={} queue_max={}",t.min_interarrival_us,t.max_interarrival_us,t.max_queue_residence_us)),
  3=>page(c,name,format_args!("proc_max={} last_cons={} cons_gap={}",t.max_consumer_processing_us,t.last_consumer_us,t.max_consumer_gap_us)),
  4=>page(c,name,format_args!("begin={} calls={} qspi_total={}",t.begin_us,t.qspi_calls,t.qspi_total_us)),
  5=>page(c,name,format_args!("qspi_max={} lock_total={} lock_max={}",t.qspi_max_us,t.lock_total_us,t.lock_max_us)),
  _=>page(c,name,format_args!("remain={} gap={} expected={} observed={}",t.min_frame_remaining,t.gap_valid,t.expected_offset,t.observed_offset)),
 }
}
#[derive(Clone,Copy,Default)]
pub struct QueueSample {pub capacity:u32,pub count:u32,pub first_id:u32,pub first_offset:u32,pub first_valid:bool,pub first_since_consumer_us:u32,pub first_since_producer_us:u32,pub first_consumer_busy:bool,pub first_queued:u32,pub socket_errors:u32,pub producer_stack:u32,pub consumer_stack:u32,pub producer_priority:u32,pub consumer_priority:u32,pub queued:u32,pub high:u32}
pub fn queue(c:Context,index:u8,q:QueueSample)->Result<Line,fmt::Error>{
 match index{
  0=>page(c,"q0",format_args!("cap={} drops={} queued={} high={}",q.capacity,q.count,q.queued,q.high)),
  1=>page(c,"q1",format_args!("first_valid={} first_id={} offset={} queued={}",q.first_valid,q.first_id,q.first_offset,q.first_queued)),
  2=>page(c,"q2",format_args!("since_cons={} since_prod={} busy={} socket_err={}",q.first_since_consumer_us,q.first_since_producer_us,q.first_consumer_busy,q.socket_errors)),
  _=>page(c,"q3",format_args!("prod_stack={} cons_stack={} prod_prio={} cons_prio={}",q.producer_stack,q.consumer_stack,q.producer_priority,q.consumer_priority)),
 }
}
pub fn producer(c:Context,index:u8,t:crate::streaming::telemetry::ProducerTiming)->Result<Line,fmt::Error>{
 if index==0{page(c,"pr0",format_args!("datagrams={} last={} below_1ms={}",t.datagrams,t.last_us,t.gaps_below_1000us))}
 else{page(c,"pr1",format_args!("gap_min={} gap_max={}",t.min_gap_us,t.max_gap_us))}
}
