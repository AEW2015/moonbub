#[path="streaming/protocol.rs"] mod protocol;
use esp_idf_svc::{eventloop::EspSystemEventLoop,hal::peripherals::Peripherals,wifi::{AuthMethod,BlockingWifi,ClientConfiguration,Configuration,EspWifi}};
use std::{net::{SocketAddr,UdpSocket},time::Duration};
fn emit(sock:&UdpSocket,peer:SocketAddr,seq:&mut u32,kind:u8,id:u32,body:&[u8])->anyhow::Result<()> {
 let mut event=Vec::with_capacity(9+body.len());event.push(kind);event.extend(seq.to_be_bytes());event.extend(id.to_be_bytes());event.extend(body);
 sock.send_to(&event,peer)?;let mut ack=[0u8;32];let (n,from)=sock.recv_from(&mut ack)?;
 anyhow::ensure!(from==peer && n==5 && ack[0]==b'K' && ack[1..5]==seq.to_be_bytes(),"bad adapter acknowledgment");
 *seq+=1;Ok(())
}
fn main()->anyhow::Result<()> {
 esp_idf_svc::sys::link_patches();esp_idf_svc::log::EspLogger::initialize_default();
 let modem=Peripherals::take()?.modem;let ev=EspSystemEventLoop::take()?;
 let mut wifi=BlockingWifi::wrap(EspWifi::new(modem,ev.clone(),None)?,ev)?;
 wifi.set_configuration(&Configuration::Client(ClientConfiguration{ssid:"emu-test".try_into().unwrap(),password:"".try_into().unwrap(),auth_method:AuthMethod::None,..Default::default()}))?;
 wifi.start()?;wifi.connect()?;wifi.wait_netif_up()?;
 let sock=UdpSocket::bind("0.0.0.0:5533")?;sock.set_read_timeout(Some(Duration::from_secs(300)))?;
 log::info!("BRIDGE_GUEST_READY");
 let expected=include_bytes!("fixture.jpg");let mut buf=[0u8;1100];let mut rx=protocol::Receiver::default();let mut seq=0u32;let mut bytes=0usize;let mut count=0usize;let mut current_id=None;
 loop {
  let (n,peer)=sock.recv_from(&mut buf)?;
  let (h,done)=match rx.accept(&buf[..n]) { Ok(ok)=>ok,Err(e)=>{anyhow::ensure!(e==protocol::Error::Integrity && current_id==Some(0) && bytes==25600 && count==25,"unexpected receiver reject");emit(&sock,peer,&mut seq,b'A',0,&[])?;anyhow::ensure!(seq==27,"unexpected abort sequence");log::info!("BRIDGE_GUEST_ABORT_PASS accepted_packets={} bytes={} events={}",count,bytes,seq);return Ok(())} };
  anyhow::ensure!(h.id==0 && h.offset as usize==bytes && h.length==26159 && h.crc==0xeceeb9c5,"unexpected frame");
  let data=&buf[protocol::HEADER..n];anyhow::ensure!(bytes+data.len()<=expected.len() && data==&expected[bytes..bytes+data.len()],"fixture payload mismatch");
  if h.offset==0 { let mut body=[0u8;8];body[..4].copy_from_slice(&h.length.to_be_bytes());body[4..].copy_from_slice(&h.crc.to_be_bytes());emit(&sock,peer,&mut seq,b'B',h.id,&body)?;current_id=Some(h.id); }
  let mut body=Vec::with_capacity(6+data.len());body.extend(h.offset.to_be_bytes());body.extend((data.len() as u16).to_be_bytes());body.extend(data);
  emit(&sock,peer,&mut seq,b'D',h.id,&body)?;bytes+=data.len();count+=1;
  if done {emit(&sock,peer,&mut seq,b'C',h.id,&[])?;break;}
 }
 anyhow::ensure!(bytes==26159 && count==26 && seq==28,"incomplete bridge");
 log::info!("BRIDGE_GUEST_PASS packets={} bytes={} events={}",count,bytes,seq);Ok(())
}
