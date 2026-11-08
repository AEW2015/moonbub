#![allow(dead_code)]
mod network_driver {
 #[derive(Debug)]pub enum Error{Bounds,Sequence}
 pub struct Header{pub prefix:[u8;76],pub length:usize,pub crc:u32}
 pub trait Source{fn header(&mut self)->Result<Header,Error>;fn read(&mut self,o:usize,b:&mut[u8;1024])->Result<usize,Error>;fn stored(&mut self,n:usize)->Result<(),Error>;fn presented(&mut self)->Result<(),Error>;}
}
mod network_wire { pub struct Identity; }
mod network_io {
 pub struct Input;impl Input{pub fn diagnostic_identity(&self)->Option<super::network_wire::Identity>{None}pub fn failed(&self){}pub fn held(&mut self)->!{panic!()}}
 impl super::network_driver::Source for Input{fn header(&mut self)->Result<super::network_driver::Header,super::network_driver::Error>{panic!()}fn read(&mut self,_:usize,_:&mut[u8;1024])->Result<usize,super::network_driver::Error>{panic!()}fn stored(&mut self,_:usize)->Result<(),super::network_driver::Error>{panic!()}fn presented(&mut self)->Result<(),super::network_driver::Error>{panic!()}}
}
#[path="C:/moon/dev/experiments/v59-throughput-probe-20261108/handheld/src/cu66/framing.rs"]mod framing;
#[path="C:/moon/dev/experiments/v59-throughput-probe-20261108/handheld/src/cu66/performance_input.rs"]mod performance_input;
use network_driver::Source;
#[test]fn flash_all40_exact_bytes_finite_and_ordered(){let mut s=performance_input::Flash::new();let mut b=[0;1024];let mut total=0;for (i,p)in performance_input::FLASH40.iter().enumerate(){assert!(s.presented().is_err());assert!(s.read(1,&mut b).is_err());let h=s.header().unwrap();assert_eq!(&h.prefix,&p[..76]);assert_eq!(h.length,p.len());assert_eq!(h.crc,framing::crc32(p));assert_eq!(u32::from_le_bytes(h.prefix[8..12].try_into().unwrap()),i as u32);let mut offset=0;while offset<p.len(){let n=s.read(offset,&mut b).unwrap();assert_eq!(&b[..n],&p[offset..offset+n]);assert!(s.stored(offset+n-1).is_err());s.stored(offset+n).unwrap();offset+=n;total+=n;}assert!(s.read(offset,&mut b).is_err());s.presented().unwrap();}assert!(s.header().is_err());assert!(s.presented().is_err());println!("FLASH40 exact bytes={} bounded_state_bytes={} finite=true ordered=true",total,std::mem::size_of::<performance_input::Flash>());}
