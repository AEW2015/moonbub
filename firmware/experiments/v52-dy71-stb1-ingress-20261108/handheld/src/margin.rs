//! MRG1/v1 runtime margin state machine; no stream or recovery commands.
pub const BASE:u32=0xE000_0000;
pub const BUILD:u32=0x4D42_4F49;
pub fn display_build(build:u32)->bool{build==BUILD||build==0x4D42_4F50}
pub const MAGIC:u32=0x4D52_4731;
pub trait Bus {fn read(&mut self,offset:u32)->Result<u32,()>;fn write(&mut self,offset:u32,value:u32)->Result<(),()>;}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Action { Delta(i16), Set(u8), Query }
impl Action {
    pub fn from_byte(byte: u8) -> Option<Self> {
        Some(match byte { b'[' => Self::Delta(-1), b']' => Self::Delta(1), b'{' => Self::Delta(-10), b'}' => Self::Delta(10), b'=' => Self::Set(40), b'|' => Self::Set(20), b'h' => Self::Query, _ => return None })
    }
    pub fn target(self, current: u8) -> Option<u8> {
        match self { Self::Delta(delta) => Some((current as i32 + delta as i32).clamp(0,80) as u8), Self::Set(value) => Some(value.min(80)), Self::Query => None }
    }
}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Outcome {Status,Applied,Unchanged,Busy,Range,LinkReset,Identity,InvalidStatus,Io,Timeout,Changed,Mismatch,LocalBusy}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Observation {pub requested:u8,pub applied:u8,pub pending:bool,pub valid:bool,pub online:bool,pub ready:bool,pub result:u8,pub sequence:u8}
impl Observation {
 pub fn decode(requested:u32,status:u32)->Result<Self,Outcome>{
  let result=((status>>16)&15)as u8;let applied=(status&127)as u8;
  if requested>80||applied>80||status&!0xFF0F_07FF!=0||result>5{return Err(Outcome::InvalidStatus)}
  Ok(Self{requested:requested as u8,applied,pending:status&128!=0,valid:status&256!=0,online:status&512!=0,ready:status&1024!=0,result,sequence:(status>>24)as u8})
 }
 pub fn applied_valid(self)->Option<u8>{self.valid.then_some(self.applied)}
}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Report {pub key:u8,pub target:Option<u8>,pub observed:Option<Observation>,pub outcome:Outcome,pub write_attempted:bool}
#[derive(Clone,Copy,PartialEq,Eq)]
enum Phase {Idle,Start,Wait}
pub struct Controller {phase:Phase,key:u8,action:Action,target:Option<u8>,before:u8,last:Option<Observation>,steps:u8,attempted:bool}
impl Controller {
 pub const fn new()->Self{Self{phase:Phase::Idle,key:0,action:Action::Query,target:None,before:0,last:None,steps:0,attempted:false}}
 pub fn active(&self)->bool{self.phase!=Phase::Idle}
 pub fn request(&mut self,key:u8)->Result<bool,Report>{
  let Some(action)=Action::from_byte(key)else{return Ok(false)};
  if self.active(){return Err(Report{key,target:None,observed:None,outcome:Outcome::LocalBusy,write_attempted:false})}
  self.phase=Phase::Start;self.key=key;self.action=action;self.target=None;self.last=None;self.steps=0;self.attempted=false;Ok(true)
 }
 fn finish(&mut self,outcome:Outcome)->Report{self.phase=Phase::Idle;if matches!(outcome,Outcome::Io|Outcome::Identity|Outcome::Timeout){self.last=None;}Report{key:self.key,target:self.target,observed:self.last,outcome,write_attempted:self.attempted}}
 pub fn expire(&mut self)->Option<Report>{self.active().then(||self.finish(Outcome::Timeout))}
 /// <=7 QSPI transactions/call, no formatting/sleep. Only 0x084 can be written.
 pub fn step(&mut self,bus:&mut impl Bus)->Option<Report>{
  if !self.active(){return None}self.steps+=1;if self.steps>32{return Some(self.finish(Outcome::Timeout))}
  match self.advance(bus){Ok(Some(outcome))=>Some(self.finish(outcome)),Ok(None)=>None,Err(outcome)=>Some(self.finish(outcome))}
 }
 fn advance(&mut self,bus:&mut impl Bus)->Result<Option<Outcome>,Outcome>{
  let mut read=|offset|bus.read(offset).map_err(|_|Outcome::Io);
  if !crate::core_coordinator::display_peer(read(0)?,read(4)?,read(0x184)?)||read(0x08c)?!=MAGIC{return Err(Outcome::Identity)}
  let observed=Observation::decode(read(0x084)?,read(0x088)?)?;self.last=Some(observed);
  if self.phase==Phase::Start {
   let Some(target)=self.action.target(observed.requested)else{return Ok(Some(Outcome::Status))};self.target=Some(target);
   if observed.pending||!observed.online||!observed.ready{return Ok(Some(Outcome::Busy))}
   if observed.valid&&observed.applied==target&&observed.requested==target{return Ok(Some(Outcome::Unchanged))}
   self.before=observed.sequence;
   // Even an error here can follow a posted/accepted write: never retry it.
   self.attempted=true;bus.write(0x084,target as u32).map_err(|_|Outcome::Io)?;self.phase=Phase::Wait;return Ok(None)
  }
  let target=self.target.ok_or(Outcome::Changed)?;
  if !observed.pending&&observed.valid&&observed.online&&observed.ready&&observed.applied==target&&observed.requested==target&&observed.sequence!=self.before{return Ok(Some(Outcome::Applied))}
  if observed.result==5{return Ok(Some(Outcome::LinkReset))}
  if observed.requested!=target{return Ok(Some(match observed.result{3=>Outcome::Range,4=>Outcome::Busy,_=>Outcome::Changed}))}
  if !observed.pending&&observed.valid&&observed.online&&observed.ready&&observed.sequence!=self.before{return Ok(Some(Outcome::Mismatch))}
  Ok(None)
 }
}
#[cfg(test)] mod tests {
    use super::*;
    #[test]fn exact_seven_selectors_and_all_others_untouched(){for byte in 0..=255{assert_eq!(Action::from_byte(byte).is_some(),b"[]{}=|h".contains(&byte));}assert_eq!(Action::from_byte(b'H'),None);assert_eq!(Action::from_byte(b'o'),None);}
    #[test]fn targets_clamp_without_integer_wrap(){for current in 0..=80{for (byte,delta) in [(b'[',-1),(b']',1),(b'{',-10),(b'}',10)]{assert_eq!(Action::from_byte(byte).unwrap().target(current),Some((current as i32+delta).clamp(0,80)as u8));}}assert_eq!(Action::Set(250).target(0),Some(80));assert_eq!(Action::Delta(i16::MIN).target(0),Some(0));assert_eq!(Action::Delta(i16::MAX).target(80),Some(80));}
    #[test]fn explicit_presets_and_query(){assert_eq!(Action::from_byte(b'=').unwrap().target(79),Some(40));assert_eq!(Action::from_byte(b'|').unwrap().target(0),Some(20));assert_eq!(Action::Query.target(80),None);}
}
