//! Zero-copy HC70/HR70 frame validation; semantic dispatch is the native HUD endpoint.
pub const MAX_PAYLOAD: usize=49_152;
pub const MAX_WIRE: usize=MAX_PAYLOAD+36;
#[derive(Debug,PartialEq,Eq)]pub enum Error{Length,Header,Crc,Shape}
#[derive(Debug)]pub struct Frame<'a>{pub response:bool,pub opcode:u8,pub generation:u64,pub frame:u32,pub reference:u32,pub argument:u32,pub payload:&'a[u8]}
fn u32at(b:&[u8],o:usize)->u32{u32::from_le_bytes(b[o..o+4].try_into().unwrap())}
pub fn crc32(b:&[u8])->u32{!crc_extend(!0,b)}
pub fn crc_extend(mut c:u32,b:&[u8])->u32{for &x in b{c^=x as u32;for _ in 0..8{c=(c>>1)^(0xedb88320u32.wrapping_mul(c&1));}}c}
pub fn decode(b:&[u8])->Result<Frame<'_>,Error>{
 if b.len()<36||b.len()>MAX_WIRE{return Err(Error::Length)}
 let response=if &b[..4]==b"HC70"{false}else if &b[..4]==b"HR70"{true}else{return Err(Error::Header)};
 let op=b[5];if b[4]!=1||!(1..=7).contains(&op)||b[6]!=0||b[7]!=0{return Err(Error::Header)}
 let n=u32at(b,8)as usize;if n>MAX_PAYLOAD||n.checked_add(36)!=Some(b.len()){return Err(Error::Length)}
 if crc32(&b[..b.len()-4])!=u32at(b,b.len()-4){return Err(Error::Crc)}
 let arg=u32at(b,28);if !response&&((op==3&&n!=8)||(op==4&&n!=20)||((op==2||op>=5)&&n!=0)||(op==7&&arg!=1)){return Err(Error::Shape)}
 Ok(Frame{response,opcode:op,generation:u64::from_le_bytes(b[12..20].try_into().unwrap()),frame:u32at(b,20),reference:u32at(b,24),argument:arg,payload:&b[32..32+n]})
}
#[cfg(test)]mod tests{use super::*;
 fn msg(op:u8,arg:u32,p:&[u8])->Vec<u8>{let mut b=vec![0u8;32];b[..4].copy_from_slice(b"HC70");b[4]=1;b[5]=op;b[8..12].copy_from_slice(&(p.len()as u32).to_le_bytes());b[12..20].copy_from_slice(&u64::MAX.to_le_bytes());b[28..32].copy_from_slice(&arg.to_le_bytes());b.extend_from_slice(p);b.extend_from_slice(&crc32(&b).to_le_bytes());b}
 #[test]fn vectors_bounds_crc(){for op in 1..=7{let n=match op{1=>MAX_PAYLOAD,3=>8,4=>20,_=>0};let b=msg(op,if op==7{1}else{0},&vec![7;n]);assert_eq!(decode(&b).unwrap().generation,u64::MAX);for i in [0,4,5,6,8,12,20,24,28,b.len()-1]{let mut x=b.clone();x[i]^=128;assert!(decode(&x).is_err())}assert!(decode(&b[..b.len()-1]).is_err());let mut x=b.clone();x.push(0);assert!(decode(&x).is_err());}}
 #[test]fn incremental_crc_matches(){let b=msg(1,0,&[7;401]);let mut c=!0;for s in b.chunks(13){c=crc_extend(c,s)}assert_eq!(!c,crc32(&b));}
}
