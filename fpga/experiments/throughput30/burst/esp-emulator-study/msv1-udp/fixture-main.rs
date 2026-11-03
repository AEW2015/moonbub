#[path="streaming/protocol.rs"] mod protocol;
use esp_idf_svc::{eventloop::EspSystemEventLoop,hal::peripherals::Peripherals,wifi::{AuthMethod,BlockingWifi,ClientConfiguration,Configuration,EspWifi}};
use std::{net::UdpSocket,time::Duration};
fn main()->anyhow::Result<()> {
 esp_idf_svc::sys::link_patches();esp_idf_svc::log::EspLogger::initialize_default();
 let modem=Peripherals::take()?.modem;let event_loop=EspSystemEventLoop::take()?;
 let mut wifi=BlockingWifi::wrap(EspWifi::new(modem,event_loop.clone(),None)?,event_loop)?;
 wifi.set_configuration(&Configuration::Client(ClientConfiguration{ssid:"emu-test".try_into().unwrap(),password:"".try_into().unwrap(),auth_method:AuthMethod::None,..Default::default()}))?;
 wifi.start()?;wifi.connect()?;wifi.wait_netif_up()?;
 let socket=UdpSocket::bind("0.0.0.0:5533")?;socket.set_read_timeout(Some(Duration::from_secs(10)))?;
 log::info!("UDP_HARNESS_READY");
 let expected=include_bytes!("fixture.jpg");
 let mut buf=[0u8;1100];let mut rx=protocol::Receiver::default();let mut count=0usize;let mut bytes=0usize;let mut crc=!0u32;
 loop {
  let (n,peer)=socket.recv_from(&mut buf)?;let (h,done)=rx.accept(&buf[..n]).map_err(|e| anyhow::anyhow!("receiver error {:?}",e))?;
  assert_eq!(h.id,0);assert_eq!(h.offset as usize,bytes);let data=&buf[protocol::HEADER..n];
  assert!(bytes+data.len()<=expected.len());assert_eq!(data,&expected[bytes..bytes+data.len()]);bytes+=data.len();crc=protocol::crc_update(crc,data);count+=1;
  socket.send_to(b"ok",peer)?;
  if done{break}
 }
 assert_eq!(count,26);assert_eq!(bytes,26159);assert_eq!(!crc,0xeceeb9c5);
 log::info!("UDP_RECEIVER_PASS packets={} bytes={} crc32={:08x}",count,bytes,!crc);
 Ok(())
}
