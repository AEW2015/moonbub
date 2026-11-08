//! Bounded stop-and-wait lab transport. One peer/session/count, one frame in flight, no full-frame SRAM.
use super::{network_driver::{Error,Header,Source},network_wire::{self as wire,Identity}};
use std::{net::{Ipv4Addr,SocketAddr,UdpSocket},time::{Duration,Instant}};
pub struct Input{socket:UdpSocket,host:Ipv4Addr,peer:Option<SocketAddr>,current:Option<Identity>,last:Option<Identity>,pending:[u8;1024],pending_len:usize,next:usize,expected_count:u16}
impl Input{
 /// Read-only cached identity; no socket operation, ACK or state change.
 pub fn diagnostic_identity(&self)->Option<Identity>{self.current}

 pub fn new(socket:UdpSocket,host:Ipv4Addr)->std::io::Result<Self>{Self::new_for_sequence(socket,host,3)}
 pub fn new_for_sequence(socket:UdpSocket,host:Ipv4Addr,count:usize)->std::io::Result<Self>{if count==0||count>wire::MAX_SEQUENCE_FRAMES as usize{return Err(std::io::Error::new(std::io::ErrorKind::InvalidInput,"finite sequence count"))}socket.set_read_timeout(Some(Duration::from_millis(100)))?;Ok(Self{socket,host,peer:None,current:None,last:None,pending:[0;1024],pending_len:0,next:0,expected_count:count as u16})}
 fn ack(&self,id:Identity,next:usize,status:u8)->Result<(),Error>{let mut b=[0;52];wire::reply(id,next as u32,status,&mut b);let peer=self.peer.ok_or(Error::Sequence)?;let n=self.socket.send_to(&b,peer).map_err(|_|Error::Io)?;if n!=b.len(){return Err(Error::Io)}Ok(())}
 pub fn failed(&self){if let Some(id)=self.current{let _=self.ack(id,self.next,3);}}
 /// Keep the final presentation reply recoverable while retaining accepted native state.
 pub fn held(&mut self)->!{let mut b=[0;wire::MAX_DATAGRAM+1];loop{if let Ok((n,peer))=self.socket.recv_from(&mut b){if Some(peer)==self.peer{if let Ok(p)=wire::decode(&b[..n]){if self.last==Some(p.id){let _=self.ack(p.id,p.id.length as usize,2);}}}}}}
 fn receive(&mut self,want_header:bool,out:&mut[u8;1024])->Result<(Identity,usize),Error>{
  let deadline=Instant::now()+Duration::from_secs(if want_header{120}else{10});let mut b=[0;wire::MAX_DATAGRAM+1];
  loop{
   if Instant::now()>=deadline{return Err(Error::Deadline)}
   let(n,peer)=match self.socket.recv_from(&mut b){Ok(v)=>v,Err(e)if matches!(e.kind(),std::io::ErrorKind::WouldBlock|std::io::ErrorKind::TimedOut)=>continue,Err(_)=>return Err(Error::Io)};
   if peer.ip()!=std::net::IpAddr::V4(self.host)||self.peer.is_some_and(|p|p!=peer){continue}
   let p=match wire::decode(&b[..n]){Ok(p)=>p,Err(_)=>continue};
   if p.id.sequence_count!=self.expected_count{continue}
   if want_header{
    if self.last==Some(p.id){self.ack(p.id,p.id.length as usize,2)?;continue}
    if p.offset!=0||p.body.len()<76{continue}
    if let Some(last)=self.last{if p.id.session!=last.session||p.id.frame<=last.frame{continue}}
    if &p.body[..4]!=b"CU66"||p.body[4]!=1||u32::from_le_bytes(p.body[8..12].try_into().unwrap())!=p.id.frame||u32::from_le_bytes(p.body[12..16].try_into().unwrap())!=p.id.reference{continue}
    self.peer=Some(peer);self.current=Some(p.id);self.next=0;
   }else{
    if self.current!=Some(p.id){continue}
    if (p.offset as usize)<self.next{self.ack(p.id,self.next,if self.next==p.id.length as usize{1}else{0})?;continue}
    if p.offset as usize!=self.next{continue}
   }
   out[..p.body.len()].copy_from_slice(p.body);return Ok((p.id,p.body.len()))
  }
 }
}
impl Source for Input{
 fn header(&mut self)->Result<Header,Error>{let mut b=[0;1024];let(id,n)=self.receive(true,&mut b)?;self.pending[..n].copy_from_slice(&b[..n]);self.pending_len=n;let mut prefix=[0;76];prefix.copy_from_slice(&b[..76]);Ok(Header{prefix,length:id.length as usize,crc:id.crc})}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,Error>{if offset!=self.next{return Err(Error::Sequence)}if self.pending_len!=0{let n=self.pending_len;out[..n].copy_from_slice(&self.pending[..n]);self.pending_len=0;return Ok(n)}let(_,n)=self.receive(false,out)?;Ok(n)}
 fn stored(&mut self,next:usize)->Result<(),Error>{let id=self.current.ok_or(Error::Sequence)?;let expected=(self.next+1024).min(id.length as usize);if next!=expected{return Err(Error::Sequence)}self.next=next;self.ack(id,next,if next==id.length as usize{1}else{0})}
 fn presented(&mut self)->Result<(),Error>{let id=self.current.ok_or(Error::Sequence)?;if self.next!=id.length as usize{return Err(Error::Sequence)}self.ack(id,self.next,2)?;self.last=Some(id);self.current=None;Ok(())}
}
