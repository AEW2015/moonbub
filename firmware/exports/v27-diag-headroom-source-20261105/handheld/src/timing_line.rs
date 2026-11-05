//! Fixed storage; malformed/overflow/timed-out lines drain through LF.
pub enum Event { Pass, Consumed, Complete(Result<[u16;6],Error>) }
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Error {Format,Overflow,Timeout}
pub struct Parser {buffer:[u8;48],length:u8,collecting:bool,discard:bool,invalid:bool,started:u64}
impl Parser {
 pub const fn new()->Self{Self{buffer:[0;48],length:0,collecting:false,discard:false,invalid:false,started:0}}
 pub fn timeout(&mut self,now:u64)->Option<Error>{if self.collecting&&!self.discard&&now.saturating_sub(self.started)>=1500{self.discard=true;Some(Error::Timeout)}else{None}}
 pub fn feed(&mut self,byte:u8,now:u64)->Event{
  if !self.collecting{if byte!=b'T'{return Event::Pass}self.collecting=true;self.discard=false;self.invalid=false;self.length=0;self.started=now;return Event::Consumed}
  if !self.discard&&now.saturating_sub(self.started)>=1500{self.discard=true;if byte==b'\n'{self.collecting=false}return Event::Complete(Err(Error::Timeout))}
  if byte==b'\n'{self.collecting=false;if self.discard{return Event::Consumed}if self.invalid{return Event::Complete(Err(Error::Format))}return Event::Complete(parse(&self.buffer[..self.length as usize]))}
  if self.discard{return Event::Consumed}
  if self.length as usize==self.buffer.len(){self.discard=true;return Event::Complete(Err(Error::Overflow))}
  if !(byte.is_ascii_digit()||byte==b','||byte==b'\r'){self.invalid=true}
  self.buffer[self.length as usize]=byte;self.length+=1;Event::Consumed
 }
}
fn parse(mut bytes:&[u8])->Result<[u16;6],Error>{
 if bytes.last()==Some(&b'\r'){bytes=&bytes[..bytes.len()-1]}
 let mut result=[0u16;6];let(mut field,mut digits)=(0usize,0usize);
 for &byte in bytes{if byte==b','{if digits==0||field>=5{return Err(Error::Format)}field+=1;digits=0;}else if byte.is_ascii_digit(){result[field]=result[field].checked_mul(10).and_then(|v|v.checked_add((byte-b'0')as u16)).ok_or(Error::Overflow)?;digits+=1;}else{return Err(Error::Format)}}
 if field!=5||digits==0{return Err(Error::Format)}Ok(result)
}
