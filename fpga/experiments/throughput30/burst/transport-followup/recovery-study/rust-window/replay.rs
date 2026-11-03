// Host-only replay. Target adapter remains no_std; this binary uses stdin/stdout.
#[path="protocol.rs"] mod protocol;
#[path="window.rs"] mod window;
use std::io::{self,Read};
use window::{Sink,Window};
struct Output;
impl Sink for Output {
 fn packet(&mut self,h:protocol::Header,payload:&[u8],done:bool)->Result<(),()> {
  let crc=!protocol::crc_update(!0,payload);
  println!("P {} {} {} {} {:08x}",h.id,h.offset,h.count,u8::from(done),crc);Ok(())
 }
 fn abort(&mut self)->Result<(),()> {println!("A");Ok(())}
}
fn main(){
 let mut bytes=Vec::new();io::stdin().read_to_end(&mut bytes).unwrap();
 let mut offset=0;let mut w=Window::new(7);let mut sink=Output;let mut errors=0usize;
 while offset<bytes.len(){
  assert!(offset+10<=bytes.len());let now=u64::from_be_bytes(bytes[offset..offset+8].try_into().unwrap());
  let n=u16::from_be_bytes(bytes[offset+8..offset+10].try_into().unwrap()) as usize;offset+=10;
  assert!(offset+n<=bytes.len() && n<=window::PACKET_BYTES);
  if w.ingest(7,now,&bytes[offset..offset+n],&mut sink).is_err(){errors+=1;}
  offset+=n;
 }
 eprintln!("ingest_errors={errors}");
}
