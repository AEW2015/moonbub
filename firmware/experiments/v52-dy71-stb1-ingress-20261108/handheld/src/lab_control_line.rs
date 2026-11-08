//! Heap-free USB lab-control framing. Only Event::Pass may reach legacy keys.
//! Once ! is seen, capture/discard ownership lasts through LF, even after errors.
//! This parser authorizes nothing: the integration owns nonce/session/lease checks.
pub const MAX_LINE_BYTES:usize=64;
pub const TIMEOUT_MS:u64=2_000;
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Action{Ping,Reboot,Dfu,Host33,Host47}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub struct Request{pub nonce:u64,pub action:Action}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Error{Syntax,Nonce,Overflow,Timeout}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Event{Pass,Consumed,Complete(Result<Request,Error>)}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]enum State{Idle,Capture,Discard}
pub struct Parser{bytes:[u8;MAX_LINE_BYTES],length:usize,started_ms:u64,state:State}
impl Default for Parser{fn default()->Self{Self::new()}}
impl Parser{
 pub const fn new()->Self{Self{bytes:[0;MAX_LINE_BYTES],length:0,started_ms:0,state:State::Idle}}
 fn expired(&self,now_ms:u64)->bool{self.state==State::Capture&&now_ms.saturating_sub(self.started_ms)>=TIMEOUT_MS}
 /// May be called by the existing USB polling loop; no thread/timer is created.
 /// Timeout emits once and retains discard ownership until the next LF.
 pub fn tick(&mut self,now_ms:u64)->Event{if self.expired(now_ms){self.state=State::Discard;self.length=0;Event::Complete(Err(Error::Timeout))}else{Event::Consumed}}
 pub fn feed(&mut self,byte:u8,now_ms:u64)->Event{
  if self.expired(now_ms){self.length=0;self.state=if byte==b'\n'{State::Idle}else{State::Discard};return Event::Complete(Err(Error::Timeout))}
  match self.state{
   State::Idle=>{if byte!=b'!'{return Event::Pass}self.bytes[0]=byte;self.length=1;self.started_ms=now_ms;self.state=State::Capture;Event::Consumed},
   State::Discard=>{if byte==b'\n'{self.state=State::Idle}Event::Consumed},
   State::Capture=>{
    if byte==b'\n'{let result=parse(&self.bytes[..self.length]);self.length=0;self.state=State::Idle;return Event::Complete(result)}
    if self.length==self.bytes.len(){self.length=0;self.state=State::Discard;return Event::Complete(Err(Error::Overflow))}
    self.bytes[self.length]=byte;self.length+=1;Event::Consumed
   }
  }
 }
}
fn parse(mut line:&[u8])->Result<Request,Error>{
 if line.last()==Some(&b'\r'){line=&line[..line.len()-1]}
 if line.len()<28||!line.starts_with(b"!MBLAB1 ")||line[24]!=b' '{return Err(Error::Syntax)}
 let mut nonce=0u64;for b in &line[8..24]{let n=match b{b'0'..=b'9'=>b-b'0',b'a'..=b'f'=>b-b'a'+10,b'A'..=b'F'=>b-b'A'+10,_=>return Err(Error::Nonce)};nonce=(nonce<<4)|n as u64;}
 let action=match &line[25..]{b"PING"=>Action::Ping,b"REBOOT"=>Action::Reboot,b"DFU"=>Action::Dfu,b"HOST33"=>Action::Host33,b"HOST47"=>Action::Host47,_=>return Err(Error::Syntax)};
 Ok(Request{nonce,action})
}

