// Host-only functional check of the unmodified Receiver's state around a
// downstream NACK; no emulator, guest transport, QSPI or real timing.
#[path="protocol.rs"] mod protocol;
use std::{env,fs};
fn main(){
 let data=fs::read(env::args().nth(1).unwrap()).unwrap();let mut p=0usize;let mut rx=protocol::Receiver::default();let mut completed=Vec::new();let mut nacks=0;let mut aborts=0;let mut packets=0;
 while p<data.len(){let n=u16::from_be_bytes([data[p],data[p+1]]) as usize;p+=2;let mut pkt=data[p..p+n].to_vec();p+=n;let id=u32::from_be_bytes(pkt[8..12].try_into().unwrap());let final_pkt=pkt[7]&2!=0;
  if id==1&&final_pkt{let end=pkt.len()-1;pkt[end]^=1;assert_eq!(rx.accept(&pkt),Err(protocol::Error::Integrity));aborts+=1;}
  else {let (h,done)=rx.accept(&pkt).unwrap();assert_eq!(h.id,id);if done {if id==2 {nacks+=1;} else {completed.push(id);}}}
  packets+=1;
 }
 assert_eq!(packets,106);assert_eq!(aborts,1);assert_eq!(nacks,1);assert_eq!(completed,[0,3]);
 println!("HOST_RECEIVER_NACK_POLICY_PASS packets={packets} guest_crc_abort={aborts} simulated_downstream_nack={nacks} completed={completed:?}");
}
