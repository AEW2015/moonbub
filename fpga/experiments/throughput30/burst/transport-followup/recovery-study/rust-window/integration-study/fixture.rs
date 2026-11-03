// Host-only real-JPEG replay; the modeled sink is not real FPGA hardware.
#[path="protocol.rs"] mod protocol;
#[path="window.rs"] mod window;
#[path="model.rs"] mod model;
use std::{env,fs};
use model::{Driver,DriverError,MockFpga};
use protocol::{crc_update,HEADER};
use window::Error;
fn packets(id:u32,data:&[u8])->Vec<Vec<u8>> {
 let crc=!crc_update(!0,data);let mut out=Vec::new();
 for off in (0..data.len()).step_by(1024) {
  let n=std::cmp::min(1024,data.len()-off);let mut p=vec![0u8;HEADER+n];
  p[..4].copy_from_slice(b"MSV1");p[4]=1;p[5]=1;
  let f=(if off==0{1u16}else{0})|(if off+n==data.len(){2u16}else{0});p[6..8].copy_from_slice(&f.to_be_bytes());
  p[8..12].copy_from_slice(&id.to_be_bytes());p[12..14].copy_from_slice(&720u16.to_be_bytes());p[14..16].copy_from_slice(&480u16.to_be_bytes());
  p[16..20].copy_from_slice(&(data.len() as u32).to_be_bytes());p[20..24].copy_from_slice(&(off as u32).to_be_bytes());
  p[24..26].copy_from_slice(&(n as u16).to_be_bytes());p[28..32].copy_from_slice(&crc.to_be_bytes());
  p[32..40].copy_from_slice(&100u64.to_be_bytes());p[HEADER..].copy_from_slice(&data[off..off+n]);out.push(p);
 }
 out
}
fn main(){
 let path=env::args().nth(1).expect("fixture path");let data=fs::read(path).unwrap();assert!(data.len()>2048 && data.len()<=262144);
 let mut d=Driver::new(1);let mut s=MockFpga::<262144>::new(b"old front",77).unwrap();
 let p=packets(1,&data);let mut order=vec![1,0,3,2];order.extend(4..p.len());
 for (time,i) in order.iter().enumerate(){d.ingest(1,time as u64,&p[*i],&mut s).unwrap();}
 assert!(s.pending());assert_eq!(s.front(),b"old front");assert!(s.vblank());assert_eq!(s.front(),data);
 let mut bad=packets(2,&data);let last=bad.last_mut().unwrap();last[HEADER]^=1;
 for (i,x) in bad.iter().enumerate(){let r=d.ingest(1,1000+i as u64,x,&mut s);if i+1==bad.len(){assert_eq!(r,Err(DriverError::Window(Error::Receiver)));}else{r.unwrap();}}
 assert_eq!(s.front_id(),Some(1));assert_eq!(s.front(),data);assert!(!s.pending());assert!(!s.vblank());
 let next=packets(3,&data);for (i,x) in next.iter().enumerate(){d.ingest(1,2000+i as u64,x,&mut s).unwrap();}
 assert!(s.pending());d.replace_session(2,&mut s).unwrap();assert!(!s.pending());assert!(!s.vblank());assert_eq!(s.front_id(),Some(1));assert_eq!(s.front(),data);
 println!("FIXTURE_PASS jpeg_bytes={} packets={} reordered=2 good_presented=1 corrupt_aborted=1 session_pending_aborted=1 crc={:08x}",data.len(),p.len(),!crc_update(!0,&data));
}
