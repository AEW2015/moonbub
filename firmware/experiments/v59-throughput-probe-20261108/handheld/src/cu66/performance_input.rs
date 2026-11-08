//! Fixed flash-backed control and existing network input; no packet-sized SRAM allocation.
use super::{network_driver::{Error,Header,Source},network_io,network_wire};
pub static FLASH40:[&[u8];40]=[
include_bytes!("fixtures/performance40/frame000.cu66"),
include_bytes!("fixtures/performance40/frame001.cu66"),
include_bytes!("fixtures/performance40/frame002.cu66"),
include_bytes!("fixtures/performance40/frame003.cu66"),
include_bytes!("fixtures/performance40/frame004.cu66"),
include_bytes!("fixtures/performance40/frame005.cu66"),
include_bytes!("fixtures/performance40/frame006.cu66"),
include_bytes!("fixtures/performance40/frame007.cu66"),
include_bytes!("fixtures/performance40/frame008.cu66"),
include_bytes!("fixtures/performance40/frame009.cu66"),
include_bytes!("fixtures/performance40/frame010.cu66"),
include_bytes!("fixtures/performance40/frame011.cu66"),
include_bytes!("fixtures/performance40/frame012.cu66"),
include_bytes!("fixtures/performance40/frame013.cu66"),
include_bytes!("fixtures/performance40/frame014.cu66"),
include_bytes!("fixtures/performance40/frame015.cu66"),
include_bytes!("fixtures/performance40/frame016.cu66"),
include_bytes!("fixtures/performance40/frame017.cu66"),
include_bytes!("fixtures/performance40/frame018.cu66"),
include_bytes!("fixtures/performance40/frame019.cu66"),
include_bytes!("fixtures/performance40/frame020.cu66"),
include_bytes!("fixtures/performance40/frame021.cu66"),
include_bytes!("fixtures/performance40/frame022.cu66"),
include_bytes!("fixtures/performance40/frame023.cu66"),
include_bytes!("fixtures/performance40/frame024.cu66"),
include_bytes!("fixtures/performance40/frame025.cu66"),
include_bytes!("fixtures/performance40/frame026.cu66"),
include_bytes!("fixtures/performance40/frame027.cu66"),
include_bytes!("fixtures/performance40/frame028.cu66"),
include_bytes!("fixtures/performance40/frame029.cu66"),
include_bytes!("fixtures/performance40/frame030.cu66"),
include_bytes!("fixtures/performance40/frame031.cu66"),
include_bytes!("fixtures/performance40/frame032.cu66"),
include_bytes!("fixtures/performance40/frame033.cu66"),
include_bytes!("fixtures/performance40/frame034.cu66"),
include_bytes!("fixtures/performance40/frame035.cu66"),
include_bytes!("fixtures/performance40/frame036.cu66"),
include_bytes!("fixtures/performance40/frame037.cu66"),
include_bytes!("fixtures/performance40/frame038.cu66"),
include_bytes!("fixtures/performance40/frame039.cu66"),
];
pub struct Flash{ordinal:usize,next:usize}
impl Flash{pub fn new()->Self{Self{ordinal:0,next:0}}fn packet(&self)->Result<&'static[u8],Error>{FLASH40.get(self.ordinal).copied().ok_or(Error::Bounds)}}
impl Source for Flash{
 fn header(&mut self)->Result<Header,Error>{if self.next!=0{return Err(Error::Sequence)}let p=self.packet()?;if p.len()<80{return Err(Error::Bounds)}let mut prefix=[0;76];prefix.copy_from_slice(&p[..76]);Ok(Header{prefix,length:p.len(),crc:super::framing::crc32(p)})}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,Error>{if offset!=self.next{return Err(Error::Sequence)}let p=self.packet()?;if offset>=p.len(){return Err(Error::Bounds)}let n=(p.len()-offset).min(1024);out[..n].copy_from_slice(&p[offset..offset+n]);Ok(n)}
 fn stored(&mut self,next:usize)->Result<(),Error>{let n=self.packet()?.len();if next!=(self.next+1024).min(n){return Err(Error::Sequence)}self.next=next;Ok(())}
 fn presented(&mut self)->Result<(),Error>{if self.next!=self.packet()?.len(){return Err(Error::Sequence)}self.ordinal+=1;self.next=0;Ok(())}
}
pub enum Input{Network(network_io::Input),Flash(Flash)}
impl Input{
 pub fn diagnostic_identity(&self)->Option<network_wire::Identity>{match self{Self::Network(n)=>n.diagnostic_identity(),Self::Flash(_)=>None}}
 pub fn failed(&self){if let Self::Network(n)=self{n.failed()}}
 pub fn held(&mut self)->!{match self{Self::Network(n)=>n.held(),Self::Flash(_)=>loop{std::thread::park()}}}
}
impl Source for Input{
 fn header(&mut self)->Result<Header,Error>{match self{Self::Network(n)=>n.header(),Self::Flash(n)=>n.header()}}
 fn read(&mut self,o:usize,b:&mut[u8;1024])->Result<usize,Error>{match self{Self::Network(n)=>n.read(o,b),Self::Flash(n)=>n.read(o,b)}}
 fn stored(&mut self,n:usize)->Result<(),Error>{match self{Self::Network(s)=>s.stored(n),Self::Flash(s)=>s.stored(n)}}
 fn presented(&mut self)->Result<(),Error>{match self{Self::Network(n)=>n.presented(),Self::Flash(n)=>n.presented()}}
}
