
#[path = "C:/Users/lavat/codex/moonbub/firmware/handheld/src/streaming/protocol.rs"] mod protocol;
use std::io::Read;
fn main() {
    let mut bytes=Vec::new(); std::io::stdin().read_to_end(&mut bytes).unwrap();
    let mut pos=0; let mut receiver=protocol::Receiver::default();
    while pos<bytes.len() {
        let len=u32::from_be_bytes(bytes[pos..pos+4].try_into().unwrap()) as usize;
        pos+=4;
        if len==0 {receiver=protocol::Receiver::default(); println!("RESET"); continue;}
        let packet=&bytes[pos..pos+len]; pos+=len;
        let header=protocol::Header::parse(packet).is_ok();
        match receiver.accept(packet) {
            Ok((h,done)) => println!("{} 1 {} {} {}",header as u8,done as u8,h.id,h.offset),
            Err(_) => println!("{} 0 0 0 0",header as u8),
        }
    }
    let feedback=protocol::feedback(1,0x845,0x12345678,8192,71,9,123456789);
    for byte in feedback {print!("{:02x}",byte);} println!();
}
