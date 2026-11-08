//! CPL1 retained observer only. No decoder command/address escape hatch.
//! Tags are opaque numeric u32 limbs, least-significant limb first.
pub const ID:u32=0x314c5043;
pub const SCHEMA:u32=0x10000;
pub const IMAGE:u32=0x43505231;
pub const WORDS:usize=40;
pub trait Bus { fn read(&mut self,offset:u32)->Result<u32,()>; fn capture(&mut self,cookie:u32)->Result<(),()>; }
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Error { Io,Identity,Cookie,Generation,Quarantine,Flags,Timeout,Epoch,Exhausted }
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Snapshot { pub words:[u32;WORDS] }
impl Snapshot {
 pub fn cookie(&self)->u32{self.words[0]}
 pub fn generation(&self)->u32{self.words[1]}
 /// CRC is actual retained final LE16 column-major RGB565, not an expectation.
 pub fn canvas_crc(&self)->Option<u32>{(self.words[35]&1!=0).then_some(self.words[33])}
 fn validate(&self)->Result<(),Error>{
  if self.words[2]!=SCHEMA{return Err(Error::Identity)}
  let f=self.words[3]; let canvas=self.words[35];
  if f&(1<<3)!=0{return Err(Error::Quarantine)}
  if f&!0x1fff!=0||f&0x1800!=0||self.words[25]&!0x7f!=0||canvas&!31!=0||canvas&16!=0||self.words[38]!=0||self.words[39]!=0{return Err(Error::Flags)}
  if self.words[25]&3!=3{return Err(Error::Flags)}
  if self.words[24]&!0x3ff0f!=0{return Err(Error::Flags)}
  if canvas&1!=0&&(self.words[32]==0||self.words[34]!=345600||canvas&0x1c!=0||self.words[36]!=0){return Err(Error::Flags)}
  Ok(())
 }
}
/// Never reset this allocator on FPGA logical reset/reconfiguration. Exhausts
/// instead of wrapping. No persistent identity across ESP reboot: current-capture
/// only, no cross-boot ownership/ACK/reference continuity is qualified.
pub struct Cookies { next:u32 }
impl Cookies {
 pub const fn new()->Self{Self{next:1}}
 pub fn take(&mut self,old:u32)->Result<u32,Error>{loop{let v=self.next;if v==0{return Err(Error::Exhausted)}self.next=v.checked_add(1).unwrap_or(0);if v!=old{return Ok(v)}}}
}
pub struct Capture { words:[u32;WORDS],cookie:u32,generation:u32,next:usize,deadline:u64,epoch:u32 }
fn identity(b:&mut impl Bus)->Result<(),Error>{
 let v=[b.read(0).map_err(|_|Error::Io)?,b.read(4).map_err(|_|Error::Io)?,b.read(8).map_err(|_|Error::Io)?,b.read(0x184).map_err(|_|Error::Io)?];
 if v!=[ID,SCHEMA,0,IMAGE]{return Err(Error::Identity)}Ok(())
}
fn pair(b:&mut impl Bus)->Result<(u32,u32),Error>{Ok((b.read(0x500).map_err(|_|Error::Io)?,b.read(0x504).map_err(|_|Error::Io)?))}
impl Capture {
 pub fn begin(b:&mut impl Bus,cookies:&mut Cookies,now:u64,epoch:u32)->Result<Self,Error>{
  identity(b)?;let old=pair(b)?;
  if old.1>=u32::MAX-1{return Err(Error::Generation)}
  identity(b)?;if pair(b)?!=old{return Err(Error::Generation)}
  let cookie=cookies.take(old.0)?;b.capture(cookie).map_err(|_|Error::Io)?;
  Ok(Self{words:[0;WORDS],cookie,generation:old.1+1,next:0,deadline:now.saturating_add(500000),epoch})
 }
 fn guard(&self,b:&mut impl Bus)->Result<(),Error>{identity(b)?;let(c,g)=pair(b)?;if c!=self.cookie||c==0{return Err(Error::Cookie)}if g!=self.generation||g==u32::MAX{return Err(Error::Generation)}Ok(())}
 pub fn expired(&self,now:u64)->bool{now>=self.deadline}
 /// Four words per step, bounded16 reads; no waits or formatting inside Bus.
 pub fn step(&mut self,b:&mut impl Bus,now:u64,epoch:u32)->Result<Option<Snapshot>,Error>{
  if now>=self.deadline{return Err(Error::Timeout)}if epoch!=self.epoch{return Err(Error::Epoch)}
  self.guard(b)?;
  let end=(self.next+4).min(WORDS);
  for i in self.next..end{self.words[i]=b.read(0x500+i as u32*4).map_err(|_|Error::Io)?;}
  self.guard(b)?;self.next=end;
  // Check quarantine/reserved flags as soon as the first group is present.
  if self.words[3]&(1<<3)!=0{return Err(Error::Quarantine)}
  if end==WORDS{let s=Snapshot{words:self.words};if s.cookie()!=self.cookie{return Err(Error::Cookie)}if s.generation()!=self.generation{return Err(Error::Generation)}s.validate()?;Ok(Some(s))}else{Ok(None)}
 }
}
/// 10 fixed pages, each four raw numeric words. Offsets give exact semantics
/// against the frozen contract; no reinterpretation of pad launches as ACKs.
pub fn page(s:&Snapshot,index:usize)->Result<crate::diag_pages::Line,core::fmt::Error>{
 use core::fmt::Write;
 if index>=10{return Err(core::fmt::Error)}
 let mut out=crate::diag_pages::Line::new();let i=index*4;
 write!(out,"USB_TRACE cpl1 v=1 page={} cookie={:08x} gen={} off={:03x} words={:08x},{:08x},{:08x},{:08x}",index,s.cookie(),s.generation(),0x500+i*4,s.words[i],s.words[i+1],s.words[i+2],s.words[i+3])?;
 if out.as_str().len()>192{return Err(core::fmt::Error)}Ok(out)
}

#[cfg(test)]mod allocator_tests{use super::*;#[test]fn allocator_exhausts_without_wrap(){let mut c=Cookies{next:u32::MAX};assert_eq!(c.take(0),Ok(u32::MAX));assert_eq!(c.take(0),Err(Error::Exhausted));}}
