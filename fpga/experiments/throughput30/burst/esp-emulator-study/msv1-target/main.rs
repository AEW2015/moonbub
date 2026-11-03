#[path = "streaming/protocol.rs"] mod protocol;
use protocol::{Error, Receiver};
fn packet(id:u32, offset:u32, chunk:&[u8], all:&[u8])->Vec<u8> {
 let mut p=vec![0;40]; p[..4].copy_from_slice(b"MSV1"); p[4]=1; p[5]=1;
 let flags=(if offset==0 {1u16} else {0}) | (if offset as usize+chunk.len()==all.len(){2}else{0});
 p[6..8].copy_from_slice(&flags.to_be_bytes());p[8..12].copy_from_slice(&id.to_be_bytes());
 p[12..14].copy_from_slice(&720u16.to_be_bytes());p[14..16].copy_from_slice(&480u16.to_be_bytes());
 p[16..20].copy_from_slice(&(all.len() as u32).to_be_bytes());p[20..24].copy_from_slice(&offset.to_be_bytes());
 p[24..26].copy_from_slice(&(chunk.len() as u16).to_be_bytes());p[28..32].copy_from_slice(&(!protocol::crc_update(!0,all)).to_be_bytes());p.extend(chunk);p
}
fn main() {
 esp_idf_svc::sys::link_patches();
 esp_idf_svc::log::EspLogger::initialize_default();
 log::info!("MSV1_TARGET_PROBE_START");
 assert_eq!(!protocol::crc_update(!0,b"123456789"),0xcbf43926);
 let all=vec![42u8;2048];let mut r=Receiver::default();
 assert!(!r.accept(&packet(1,0,&all[..1024],&all)).unwrap().1);
 assert!(r.accept(&packet(1,1024,&all[1024..],&all)).unwrap().1);
 log::info!("PASS two_chunk_valid");
 let mut p=packet(2,0,b"ok",b"ok");p[40]^=1;assert_eq!(r.accept(&p),Err(Error::Integrity));
 log::info!("PASS corrupt_crc_rejected");
 assert!(r.accept(&packet(3,0,b"ok",b"ok")).unwrap().1);
 log::info!("PASS next_frame_recovery");
 let mut malformed=packet(4,0,b"ok",b"ok");malformed[5]=2;assert_eq!(r.accept(&malformed),Err(Error::Format));
 assert_eq!(r.accept(&[0u8;39]),Err(Error::Header));
 log::info!("PASS malformed_headers_rejected");
 let p=packet(5,0,&all[..1024],&all);assert!(!r.accept(&p).unwrap().1);assert_eq!(r.accept(&p),Err(Error::Sequence));
 log::info!("PASS duplicate_rejected");
 let trace=include_bytes!("fixture.trace"); let mut pos=0usize; let mut count=0usize;
 let mut sink_bytes=0usize; let mut sink_crc=!0u32; let mut frame_done=0usize; let mut rr=Receiver::default();
 while pos<trace.len() {
  assert!(pos+2<=trace.len());let n=u16::from_be_bytes([trace[pos],trace[pos+1]]) as usize;pos+=2;
  assert!(pos+n<=trace.len());let datagram=&trace[pos..pos+n];pos+=n;
  let (h,done)=rr.accept(datagram).unwrap();assert_eq!(h.id,0);assert_eq!(h.offset as usize,sink_bytes);
  let payload=&datagram[protocol::HEADER..]; sink_bytes+=payload.len();sink_crc=protocol::crc_update(sink_crc,payload);count+=1;
  if done {frame_done+=1;assert_eq!(h.crc,0xeceeb9c5);}
 }
 assert_eq!(count,26);assert_eq!(frame_done,1);assert_eq!(sink_bytes,26159);assert_eq!(!sink_crc,0xeceeb9c5);
 log::info!("PASS fixture_trace packets={} bytes={} crc32={:08x}",count,sink_bytes,!sink_crc);
 log::info!("MSV1_TARGET_PROBE_PASS");
}
