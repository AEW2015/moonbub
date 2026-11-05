//! TIM1/v1 atomic timing pair controller, fixed active480x800 and pixel clock.
use super::margin::{Bus,Outcome};
pub const MAGIC:u32=0x5449_4D31;
pub const SCHEMA:u32=0x0001_0003;
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub struct Timing {pub horizontal:u32,pub vertical:u32}
impl Timing {
 pub fn new(v:[u16;6])->Result<Self,Outcome>{let[hs,hb,hf,vs,vb,vf]=v.map(u32::from);if v.iter().any(|&x|x>1023)||hs<1||hf<2||vs<1||vf<1||vs+vb<2||480+hs+hf+hb>1023||800+vs+vf+vb>1023{return Err(Outcome::Range)}Ok(Self{horizontal:hs|(hb<<10)|(hf<<20),vertical:vs|(vb<<10)|(vf<<20)})}
 pub fn decode(horizontal:u32,vertical:u32)->Result<Self,Outcome>{if(horizontal|vertical)&0xC000_0000!=0{return Err(Outcome::InvalidStatus)}Self::new([(horizontal&1023)as u16,((horizontal>>10)&1023)as u16,((horizontal>>20)&1023)as u16,(vertical&1023)as u16,((vertical>>10)&1023)as u16,((vertical>>20)&1023)as u16]).map_err(|_|Outcome::InvalidStatus)}
 pub fn current()->Self{Self::new([4,10,47,4,20,10]).unwrap()}
 pub fn official()->Self{Self::new([4,119,2,4,2,3]).unwrap()}
}
#[derive(Clone,Copy)]pub enum Choice {Current,Official,Custom(Timing),Query}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub struct Status {pub preset:u8,pub pending:bool,pub valid:bool,pub online:bool,pub ready:bool,pub result:u8,pub sequence:u8,pub raw:u32}
impl Status {pub fn decode(raw:u32)->Result<Self,Outcome>{let preset=(raw&127)as u8;let result=((raw>>16)&15)as u8;if preset>2||result>6||raw&!0xFF0F_07FF!=0{return Err(Outcome::InvalidStatus)}Ok(Self{preset,pending:raw&128!=0,valid:raw&256!=0,online:raw&512!=0,ready:raw&1024!=0,result,sequence:(raw>>24)as u8,raw})}}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub struct Report {pub key:u8,pub target:Option<Timing>,pub applied:Option<Timing>,pub status:Option<Status>,pub outcome:Outcome,pub write_attempted:bool,pub apply_attempted:bool}
#[derive(Clone,Copy,PartialEq,Eq)]enum Phase {Idle,Start,StageH,StageV,ApplyCustom,Poll,ReadPair,Verify}
pub struct Controller {phase:Phase,key:u8,choice:Choice,target:Option<Timing>,preset:u8,before:u8,status:Option<Status>,pair:Option<Timing>,steps:u8,written:bool,applied:bool}
impl Controller {
 pub const fn new()->Self{Self{phase:Phase::Idle,key:0,choice:Choice::Query,target:None,preset:0,before:0,status:None,pair:None,steps:0,written:false,applied:false}}
 pub fn active(&self)->bool{self.phase!=Phase::Idle}
 pub fn request(&mut self,key:u8,choice:Choice)->Result<(),Report>{if self.active(){return Err(Report{key,target:None,applied:None,status:None,outcome:Outcome::LocalBusy,write_attempted:false,apply_attempted:false})}if let Choice::Custom(v)=choice{if Timing::decode(v.horizontal,v.vertical).is_err(){return Err(Report{key,target:Some(v),applied:None,status:None,outcome:Outcome::Range,write_attempted:false,apply_attempted:false})}}self.phase=Phase::Start;self.key=key;self.choice=choice;self.target=match choice{Choice::Current=>Some(Timing::current()),Choice::Official=>Some(Timing::official()),Choice::Custom(v)=>Some(v),Choice::Query=>None};self.preset=match choice{Choice::Current=>0,Choice::Official=>1,_=>2};self.status=None;self.pair=None;self.steps=0;self.written=false;self.applied=false;Ok(())}
 fn finish(&mut self,outcome:Outcome)->Report{self.phase=Phase::Idle;if matches!(outcome,Outcome::Io|Outcome::Identity|Outcome::Timeout){self.status=None;self.pair=None}Report{key:self.key,target:self.target,applied:self.status.filter(|s|s.valid).and(self.pair),status:self.status,outcome,write_attempted:self.written,apply_attempted:self.applied}}
 pub fn expire(&mut self)->Option<Report>{self.active().then(||self.finish(Outcome::Timeout))}
 pub fn step(&mut self,bus:&mut impl Bus)->Option<Report>{if !self.active(){return None}self.steps+=1;if self.steps>32{return Some(self.finish(Outcome::Timeout))}match self.advance(bus){Ok(Some(outcome))=>Some(self.finish(outcome)),Ok(None)=>None,Err(outcome)=>Some(self.finish(outcome))}}
 fn identity(bus:&mut impl Bus)->Result<(),Outcome>{let mut read=|off|bus.read(off).map_err(|_|Outcome::Io);if !crate::core_coordinator::display_peer(read(0)?,read(4)?,read(0x184)?)||read(0x090)?!=MAGIC||read(0x09c)?!=SCHEMA{return Err(Outcome::Identity)}Ok(())}
 fn read_status(bus:&mut impl Bus)->Result<Status,Outcome>{Status::decode(bus.read(0x0a8).map_err(|_|Outcome::Io)?)}
 fn write(&mut self,bus:&mut impl Bus,off:u32,value:u32)->Result<(),Outcome>{self.written=true;if off==0x09c{self.applied=true}bus.write(off,value).map_err(|_|Outcome::Io)}
 fn advance(&mut self,bus:&mut impl Bus)->Result<Option<Outcome>,Outcome>{
  Self::identity(bus)?;
  if self.phase==Phase::ReadPair {self.pair=Some(Timing::decode(bus.read(0x0a0).map_err(|_|Outcome::Io)?,bus.read(0x0a4).map_err(|_|Outcome::Io)?)?);self.phase=Phase::Verify;return Ok(None)}
  let status=Self::read_status(bus)?;
  if self.phase==Phase::Verify{
   if self.status.map(|s|s.raw)!=Some(status.raw){self.status=Some(status);self.pair=None;self.phase=Phase::ReadPair;return Ok(None)}
   if matches!(self.choice,Choice::Query){return Ok(Some(Outcome::Status))}
   if !status.online||!status.ready {self.pair=None;self.phase=Phase::Poll;return Ok(None)}
   if !status.pending&&status.valid&&status.sequence!=self.before&&status.preset==self.preset&&self.pair==self.target{return Ok(Some(Outcome::Applied))}
   return Ok(Some(Outcome::Mismatch))
  }
  self.status=Some(status);
  if self.phase==Phase::Start{
   if self.target.is_none(){if !status.valid{return Ok(Some(Outcome::Status))}self.phase=Phase::ReadPair;return Ok(None)}
   if status.pending||!status.online||!status.ready{return Ok(Some(Outcome::Busy))}
   self.before=status.sequence;
   if matches!(self.choice,Choice::Custom(_)){self.phase=Phase::StageH}else{self.write(bus,0x09c,self.preset as u32)?;self.phase=Phase::Poll}return Ok(None)
  }
  if matches!(self.phase,Phase::StageH|Phase::StageV|Phase::ApplyCustom){
   if status.pending||!status.online||!status.ready{return Ok(Some(Outcome::Busy))}
   let target=self.target.ok_or(Outcome::Changed)?;
   match self.phase{
    Phase::StageH=>{self.write(bus,0x094,target.horizontal)?;self.phase=Phase::StageV},
    Phase::StageV=>{self.write(bus,0x098,target.vertical)?;self.phase=Phase::ApplyCustom},
    _=>{let horizontal=bus.read(0x094).map_err(|_|Outcome::Io)?;let vertical=bus.read(0x098).map_err(|_|Outcome::Io)?;if horizontal!=target.horizontal||vertical!=target.vertical{return Ok(Some(Outcome::Mismatch))}self.before=status.sequence;self.write(bus,0x09c,2)?;self.phase=Phase::Poll}
   }return Ok(None)
  }
  if !status.pending&&status.valid&&status.online&&status.ready&&status.sequence!=self.before{self.phase=Phase::ReadPair;return Ok(None)}
  if status.result==5{return Ok(Some(Outcome::LinkReset))}
  // Last result is not a request tag; reject only if not still in flight.
  if !status.pending {if status.result==3{return Ok(Some(Outcome::Range))}if status.result==4{return Ok(Some(Outcome::Busy))}}
  Ok(None)
 }
}
