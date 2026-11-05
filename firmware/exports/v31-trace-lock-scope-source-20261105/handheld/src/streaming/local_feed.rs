//! Shared policy for flash-to-FPGA local frames; no heap or platform dependency.
use super::protocol;
pub const CHUNK:usize=4096;
pub const FRAME_BUDGET_US:u64=500_000;
pub trait Sink {
 type Error;
 fn current(&self,generation:u32)->bool;
 fn ready(&mut self)->Result<bool,Self::Error>;
 fn begin(&mut self,header:protocol::Header)->Result<(),Self::Error>;
 fn write(&mut self,bytes:&[u8])->Result<(),Self::Error>;
 fn commit(&mut self)->Result<(),Self::Error>;
 fn presented(&mut self,id:u32)->Result<bool,Self::Error>;
}
#[derive(Debug,PartialEq,Eq)]pub enum Error<E>{Bounds,Cancelled,Timeout,Integrity,Sink(E)}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Progress{More,Committed,Presented}
#[derive(Clone,Copy,PartialEq,Eq)]enum Phase{Ready,Begin,Write,Commit,Present,Done,Failed}
pub struct Feed<'a>{bytes:&'a[u8],header:protocol::Header,generation:u32,started:u64,offset:usize,crc:u32,phase:Phase}
impl<'a> Feed<'a>{
 pub fn new(bytes:&'a[u8],crc:u32,id:u32,generation:u32,now:u64)->Result<Self,Error<()>>{
  if bytes.is_empty()||bytes.len()>protocol::MAX_FRAME as usize{return Err(Error::Bounds)}
  Ok(Self{bytes,header:protocol::Header{flags:3,id,width:720,height:480,length:bytes.len()as u32,offset:0,count:0,crc,capture_us:now},generation,started:now,offset:0,crc:!0,phase:Phase::Ready})
 }
 pub fn step<S:Sink>(&mut self,sink:&mut S,now:u64)->Result<Progress,Error<S::Error>>{
  if self.phase==Phase::Failed{return Err(Error::Cancelled)}
  if self.phase==Phase::Done{return Ok(Progress::Presented)}
  if !sink.current(self.generation){self.phase=Phase::Failed;return Err(Error::Cancelled)}
  if now.saturating_sub(self.started)>=FRAME_BUDGET_US{self.phase=Phase::Failed;return Err(Error::Timeout)}
  let result=self.advance(sink);
  if result.is_err(){self.phase=Phase::Failed}result
 }
 fn advance<S:Sink>(&mut self,sink:&mut S)->Result<Progress,Error<S::Error>>{
  match self.phase{
   Phase::Ready=>{if sink.ready().map_err(Error::Sink)?{self.phase=Phase::Begin}},
   Phase::Begin=>{sink.begin(self.header).map_err(Error::Sink)?;self.phase=Phase::Write},
   Phase::Write=>{let end=(self.offset+CHUNK).min(self.bytes.len());let data=&self.bytes[self.offset..end];sink.write(data).map_err(Error::Sink)?;self.crc=protocol::crc_update(self.crc,data);self.offset=end;if end==self.bytes.len(){self.phase=Phase::Commit}},
   Phase::Commit=>{if !self.crc!=self.header.crc{return Err(Error::Integrity)}sink.commit().map_err(Error::Sink)?;self.phase=Phase::Present;return Ok(Progress::Committed)},
   Phase::Present=>{if sink.presented(self.header.id).map_err(Error::Sink)?{self.phase=Phase::Done;return Ok(Progress::Presented)}},
   Phase::Done=>return Ok(Progress::Presented),Phase::Failed=>return Err(Error::Cancelled),
  }Ok(Progress::More)
 }
}
/// Pacing never catches up with bursts after a slow frame.
pub fn next_due(started:u64,completed:u64)->u64{started.saturating_add(200_000).max(completed)}
/// One serialized outstanding frame. A repeated ID alone is never completion.
pub fn completion_observed(before_decoded:u32,before_presented:u32,decoded:u32,presented:u32,last_id:u32,expected_id:u32)->bool{
 decoded.wrapping_sub(before_decoded)==1&&presented.wrapping_sub(before_presented)==1&&last_id==expected_id
}
