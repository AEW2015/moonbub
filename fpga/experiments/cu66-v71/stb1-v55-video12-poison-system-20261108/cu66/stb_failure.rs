//! Failure-only sampled observations. No normal-path I/O/log, retries or writes.
use super::{framing::crc_extend,local::{Bus,Error}};
use core::fmt::Arguments;
pub const WORDS:usize=13;
pub const ALL:u16=(1u16<<WORDS)-1;
pub const SAMPLE_BUDGET_US:u64=20_000;
#[derive(Debug,Clone,Copy,Default,PartialEq,Eq)]
pub struct Context {
 pub active:bool,pub ordinal:u32,pub frame:u32,pub generation:u64,pub phase:u8,
 pub progress_at_us:u64,pub stored_prefix:u32,pub identity_valid:bool,
 pub session:u64,pub capture_us:u64,pub identity_frame:u32,pub identity_reference:u32,
}
impl Context{
 pub fn with_identity(mut self,id:Option<(u64,u64,u32,u32)>)->Self{
  let(s,t,f,r)=id.unwrap_or((0,0,0,0));self.identity_valid=id.is_some();self.session=s;
  self.capture_us=t;self.identity_frame=f;self.identity_reference=r;self
 }
}
/// result_flags: bit0 all attempted, bit1 all valid, bit2 pre-call budget stop,
/// bit3 epoch error. None of these means atomicity or native readiness.
#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub struct Snapshot {
 pub start_us:u64,pub end_us:u64,pub attempted:u16,pub valid:u16,
 pub result_flags:u8,pub first_error_index:u8,pub first_error_code:u8,
 pub values:[u32;WORDS],pub context:Context,
}
impl Snapshot {
 /// Thirteen reads maximum, one try each. Budget is checked BEFORE each call;
 /// one underlying SDK operation can exceed this scheduling budget.
 pub fn read_once(bus:&mut impl Bus,context:Context)->Self{
  let start_us=bus.now();let mut s=Self{start_us,end_us:start_us,attempted:0,valid:0,
   result_flags:0,first_error_index:255,first_error_code:0,values:[0;WORDS],context};
  for index in 0..WORDS{
   if bus.now().saturating_sub(start_us)>=SAMPLE_BUDGET_US{s.result_flags|=4;break}
   s.attempted|=1u16<<index;
   match bus.read(0x700+index as u32*4){
    Ok(value)=>{s.values[index]=value;s.valid|=1u16<<index;}
    Err(error)=>{let code=match error{Error::Contended=>1,Error::Epoch=>2,Error::Io=>3,_=>4};
     if code==2{s.result_flags|=8;}if s.first_error_index==255{s.first_error_index=index as u8;s.first_error_code=code;}}
   }
  }
  s.end_us=bus.now();if s.attempted==ALL{s.result_flags|=1;}if s.valid==ALL{s.result_flags|=2;}s
 }
 /// CRC binds all context and sampled values using fixed little-endian fields.
 /// It is a diagnostic record checksum, not an RF/native-memory integrity proof.
 pub fn checksum(&self)->u32{
  let mut crc=!0;crc=crc_extend(crc,&self.start_us.to_le_bytes());crc=crc_extend(crc,&self.end_us.to_le_bytes());
  crc=crc_extend(crc,&self.attempted.to_le_bytes());crc=crc_extend(crc,&self.valid.to_le_bytes());
  crc=crc_extend(crc,&[self.result_flags,self.first_error_index,self.first_error_code]);
  let c=&self.context;crc=crc_extend(crc,&[u8::from(c.active)]);crc=crc_extend(crc,&c.ordinal.to_le_bytes());
  crc=crc_extend(crc,&c.frame.to_le_bytes());crc=crc_extend(crc,&c.generation.to_le_bytes());crc=crc_extend(crc,&[c.phase]);
  crc=crc_extend(crc,&c.progress_at_us.to_le_bytes());crc=crc_extend(crc,&c.stored_prefix.to_le_bytes());
  crc=crc_extend(crc,&[u8::from(c.identity_valid)]);crc=crc_extend(crc,&c.session.to_le_bytes());crc=crc_extend(crc,&c.capture_us.to_le_bytes());
  crc=crc_extend(crc,&c.identity_frame.to_le_bytes());crc=crc_extend(crc,&c.identity_reference.to_le_bytes());
  for v in self.values{crc=crc_extend(crc,&v.to_le_bytes());}!crc
 }
 /// Four records ≤192 payload bytes even at maximum integer values. Best-effort,
 /// NONATOMIC post-failure samples; prefix/CRC can be masked while busy. Local
 /// timestamps are sample/progress times, never claimed as failure-onset time.
 pub fn lines(&self,mut emit:impl FnMut(Arguments<'_>)){
  let crc=self.checksum();let c=&self.context;let v=&self.values;
  emit(format_args!("STBF1 H k={} e={} a={:04x} v={:04x} r={:02x} x={} y={} j={} q={} c={:08x}",self.start_us,self.end_us,self.attempted,self.valid,self.result_flags,self.first_error_index,self.first_error_code,c.identity_frame,c.identity_reference,crc));
  emit(format_args!("STBF1 C k={} a={} o={} f={} g={} p={} u={} n={} i={} s={} t={} c={:08x}",self.start_us,u8::from(c.active),c.ordinal,c.frame,c.generation,c.phase,c.progress_at_us,c.stored_prefix,u8::from(c.identity_valid),c.session,c.capture_us,crc));
  emit(format_args!("STBF1 A k={} c={:08x} {:08x} {:08x} {:08x} {:08x} {:08x} {:08x} {:08x}",self.start_us,crc,v[0],v[1],v[2],v[3],v[4],v[5],v[6]));
  emit(format_args!("STBF1 B k={} c={:08x} {:08x} {:08x} {:08x} {:08x} {:08x} {:08x}",self.start_us,crc,v[7],v[8],v[9],v[10],v[11],v[12]));
 }
}
/// Lazy context accessor is not called on success; no normal-path bus reads.
pub fn capture(failed:bool,bus:&mut impl Bus,context:impl FnOnce()->Context)->Option<Snapshot>{
 if failed{Some(Snapshot::read_once(bus,context()))}else{None}
}
