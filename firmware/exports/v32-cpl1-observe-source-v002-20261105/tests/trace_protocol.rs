//! Identity diagnostics compile the actual production protocol, not a model copy.
#[path = "../handheld/src/streaming/protocol.rs"]
mod protocol;
use protocol::{Error,Header,Receiver};
fn packet(h:Header)->Vec<u8>{
 let mut p=vec![0;protocol::HEADER+h.count as usize];p[..4].copy_from_slice(b"MSV1");p[4]=1;p[5]=1;
 p[6..8].copy_from_slice(&h.flags.to_be_bytes());p[8..12].copy_from_slice(&h.id.to_be_bytes());
 p[12..14].copy_from_slice(&h.width.to_be_bytes());p[14..16].copy_from_slice(&h.height.to_be_bytes());
 p[16..20].copy_from_slice(&h.length.to_be_bytes());p[20..24].copy_from_slice(&h.offset.to_be_bytes());p[24..26].copy_from_slice(&h.count.to_be_bytes());
 p[28..32].copy_from_slice(&h.crc.to_be_bytes());p[32..40].copy_from_slice(&h.capture_us.to_be_bytes());p
}
fn header(id:u32,offset:u32)->Header{Header{flags:if offset==0{1}else{0},id,width:720,height:480,length:32768,offset,count:1024,crc:0x12345678,capture_us:987654321}}
fn prefix()->Receiver{let mut r=Receiver::default();for offset in(0..16384).step_by(1024){r.accept(&packet(header(100,offset))).unwrap();}r}
#[test]fn active_accessor_is_preaccept_identity_and_nonmutating(){
 let r=prefix();let(h,off)=r.active_identity().unwrap();assert_eq!((h.id,h.offset,off),(100,0,16384));
 assert_eq!(r.expected_offset(),Some(16384));let before=r.active_identity();assert_eq!(r.active_identity(),before);
}
#[test]fn backward_cross_frame_is_distinct_from_same_frame_duplicate(){
 let mut r=prefix();let cross=header(101,1024);let before=r.active_identity();
 assert_eq!(r.sequence_mismatch(cross),1|64);assert_eq!(r.active_identity(),before);
 assert_eq!(r.accept(&packet(cross)),Err(Error::Sequence));assert_eq!(r.active_identity(),None);
 let mut r=prefix();let duplicate=header(100,1024);assert_eq!(r.sequence_mismatch(duplicate),64);
 assert_eq!(r.accept(&packet(duplicate)),Err(Error::Sequence));assert_eq!(r.active_identity(),None);
}
#[test]fn every_compared_header_field_has_its_own_diagnostic_bit(){
 let r=prefix();let mut h=header(101,1024);h.width=1280;h.height=720;h.length=65536;h.crc^=1;h.capture_us+=1;
 assert_eq!(r.sequence_mismatch(h),127);assert_eq!(r.active_identity().unwrap().1,16384);
}
#[test]fn valid_new_sof_does_not_compare_against_superseded_active_fields(){
 let mut r=prefix();let h=header(101,0);assert_eq!(r.sequence_mismatch(h),0);r.accept(&packet(h)).unwrap();
 assert_eq!(r.active_identity().map(|(h,o)|(h.id,o)),Some((101,1024)));
 let stale=header(100,0);assert_eq!(r.sequence_mismatch(stale),256);assert_eq!(r.accept(&packet(stale)),Err(Error::Sequence));
 assert_eq!(r.active_identity(),None);
}
#[test]fn no_active_and_header_parse_failure_keep_validity_explicit(){
 let r=Receiver::default();assert_eq!(r.active_identity(),None);assert_eq!(r.sequence_mismatch(header(101,1024)),128);
 let mut bad=header(101,0);bad.flags=0;assert_eq!(Header::parse(&packet(bad)),Err(Error::Sequence));assert_eq!(r.active_identity(),None);
}
