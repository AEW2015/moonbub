#![allow(dead_code)]
#[path="../handheld/src/cu66/framing.rs"]mod framing;
#[path="../handheld/src/cu66/hud.rs"]mod hud;
fn request(payload:&[u8])->Vec<u8>{let mut b=vec![0u8;36+payload.len()];b[..4].copy_from_slice(b"HC70");b[4]=1;b[5]=1;b[8..12].copy_from_slice(&(payload.len()as u32).to_le_bytes());b[12..20].copy_from_slice(&4u64.to_le_bytes());b[20..24].copy_from_slice(&3u32.to_le_bytes());b[24..28].copy_from_slice(&u32::MAX.to_le_bytes());b[28..32].copy_from_slice(&1u32.to_le_bytes());b[32..32+payload.len()].copy_from_slice(payload);let n=b.len()-4;let crc=framing::crc32(&b[..n]);b[n..].copy_from_slice(&crc.to_le_bytes());b}
#[test]fn ffi_framing_and_decode_failures_are_distinct(){
 let mut h=hud::Hud::new(98304).unwrap();assert!(h.transact(b"bad",&mut[0;108]).is_err());assert_eq!(h.diagnostics().stage,1);
 let wire=request(b"bad");assert!(h.transact(&wire,&mut[]).is_err());let d=h.diagnostics();assert_eq!((d.stage,d.ffi,d.opcode,d.frame),(3,-2,1,3));
 let mut h=hud::Hud::new(98304).unwrap();let mut out=[0;108];let reply=h.transact(&wire,&mut out).unwrap();assert_ne!(framing::decode(reply).unwrap().argument,0);let d=h.diagnostics();assert_eq!((d.stage,d.opcode,d.frame,d.generation),(7,1,3,4));assert_ne!(d.reply,0);assert!(d.text_length>0);assert_eq!(d.native[6],0);assert!(d.text[..d.text_length.min(96)].iter().any(|b|*b!=0));
 let a=h.stats().unwrap();let x=h.diagnostics();let y=h.diagnostics();assert_eq!(a,h.stats().unwrap());assert_eq!(x.native,y.native);assert_eq!(x.stats,y.stats);assert_eq!(x.text,y.text);
}

#[test]fn output_framing_and_identity_failures_are_distinguished(){let mut h=hud::Hud::new(98304).unwrap();let wire=request(b"bad");assert!(h.inject_reply_for_test(&wire,b"bad").is_err());assert_eq!(h.diagnostics().stage,5);let mut out=[0;108];let mut reply=h.transact(&wire,&mut out).unwrap().to_vec();reply[20]^=1;let n=reply.len()-4;let c=framing::crc32(&reply[..n]);reply[n..].copy_from_slice(&c.to_le_bytes());assert!(h.inject_reply_for_test(&wire,&reply).is_err());assert_eq!(h.diagnostics().stage,6);}
