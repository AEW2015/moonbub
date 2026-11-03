// Host-only interoperability probe for Moonbub's unmodified Rust receiver.
// Build alongside protocol.rs copied from the inspected Moonbub checkout.
#[path="protocol.rs"] mod protocol;
use std::io::{self, Read};
fn main() {
 let mut input=Vec::new();io::stdin().read_to_end(&mut input).unwrap();
 let mut offset=0usize; let mut receiver=protocol::Receiver::default();
 while offset<input.len() {
  assert!(offset+2<=input.len()); let len=u16::from_be_bytes([input[offset],input[offset+1]]) as usize;offset+=2;
  assert!(offset+len<=input.len());
  if len==0 { receiver.abort(); println!("abort"); continue; }
  match receiver.accept(&input[offset..offset+len]) {
   Ok((_,done))=>println!("{}",if done {"done"} else {"partial"}),
   Err(_)=>println!("error"),
  }
  offset+=len;
 }
}
