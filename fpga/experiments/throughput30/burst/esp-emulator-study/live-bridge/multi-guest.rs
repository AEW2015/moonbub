#[path="streaming/protocol.rs"] mod protocol;
use esp_idf_svc::{eventloop::EspSystemEventLoop,hal::peripherals::Peripherals,wifi::{AuthMethod,BlockingWifi,ClientConfiguration,Configuration,EspWifi}};
use std::{net::{SocketAddr,UdpSocket},time::Duration};
fn emit(sock:&UdpSocket,peer:SocketAddr,seq:&mut u32,kind:u8,id:u32,body:&[u8])->anyhow::Result<()> {
 let mut event=Vec::with_capacity(9+body.len());event.push(kind);event.extend(seq.to_be_bytes());event.extend(id.to_be_bytes());event.extend(body);
 sock.send_to(&event,peer)?;let mut ack=[0u8;32];let (n,from)=sock.recv_from(&mut ack)?;
 anyhow::ensure!(from==peer && n==5 && ack[0]==b'K' && ack[1..5]==seq.to_be_bytes(),"bad adapter acknowledgment");*seq+=1;Ok(())
}
fn main()->anyhow::Result<()> {
 esp_idf_svc::sys::link_patches();esp_idf_svc::log::EspLogger::initialize_default();
 let modem=Peripherals::take()?.modem;let ev=EspSystemEventLoop::take()?;
 let mut wifi=BlockingWifi::wrap(EspWifi::new(modem,ev.clone(),None)?,ev)?;
 wifi.set_configuration(&Configuration::Client(ClientConfiguration{ssid:"emu-test".try_into().unwrap(),password:"".try_into().unwrap(),auth_method:AuthMethod::None,..Default::default()}))?;
 wifi.start()?;wifi.connect()?;wifi.wait_netif_up()?;
 let sock=UdpSocket::bind("0.0.0.0:5533")?;sock.set_read_timeout(Some(Duration::from_secs(300)))?;
 log::info!("MULTI_GUEST_READY");
 let fixtures:[&[u8];3]=[include_bytes!("0000.jpg"),include_bytes!("0001.jpg"),include_bytes!("0002.jpg")];
 let crcs=[0xeceeb9c5,0x9e75ea8b,0x1ea3e1d5];let mut buf=[0u8;1100];let mut rx=protocol::Receiver::default();let mut seq=0u32;let mut bytes=0usize;let mut count=0usize;let mut id=0usize;let mut started=false;let mut frames=0usize;let mut aborts=0usize;
 loop {
  let (n,peer)=sock.recv_from(&mut buf)?;
  let (h,done)=match rx.accept(&buf[..n]) {
   Ok(ok)=>ok,
   Err(e)=>{anyhow::ensure!(id==1 && started && bytes==25600 && count==25 && e==protocol::Error::Integrity,"unexpected reject");
    emit(&sock,peer,&mut seq,b'A',id as u32,&[])?;log::info!("MULTI_GUEST_ABORT id={} bytes={}",id,bytes);aborts+=1;id+=1;bytes=0;count=0;started=false;continue;}
  };
  anyhow::ensure!(id<3 && h.id as usize==id && h.offset as usize==bytes && h.length as usize==fixtures[id].len() && h.crc==crcs[id],"unexpected frame");
  let data=&buf[protocol::HEADER..n];anyhow::ensure!(bytes+data.len()<=fixtures[id].len() && data==&fixtures[id][bytes..bytes+data.len()],"fixture payload mismatch");
  if h.offset==0 {let mut body=[0u8;8];body[..4].copy_from_slice(&h.length.to_be_bytes());body[4..].copy_from_slice(&h.crc.to_be_bytes());emit(&sock,peer,&mut seq,b'B',h.id,&body)?;started=true;}
  let mut body=Vec::with_capacity(6+data.len());body.extend(h.offset.to_be_bytes());body.extend((data.len() as u16).to_be_bytes());body.extend(data);
  emit(&sock,peer,&mut seq,b'D',h.id,&body)?;bytes+=data.len();count+=1;
  if done {anyhow::ensure!(id!=1 && bytes==fixtures[id].len(),"invalid completion");emit(&sock,peer,&mut seq,b'C',h.id,&[])?;log::info!("MULTI_GUEST_COMMIT id={} bytes={} packets={}",id,bytes,count);frames+=1;id+=1;bytes=0;count=0;started=false;if id==3{break}}
 }
 anyhow::ensure!(frames==2 && aborts==1 && seq==84,"bad totals");log::info!("MULTI_GUEST_PASS events={} commits={} aborts={}",seq,frames,aborts);Ok(())
}
