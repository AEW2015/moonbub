//! Explicit bounded sequence v3: finite count is part of every packet identity.
use super::framing::crc32;
pub const PORT:u16=5535;
pub const VERSION:u8=3;
pub const MAX_SEQUENCE_FRAMES:u16=12_000;
pub const HEADER:usize=48;
pub const CHUNK:usize=1024;
pub const MAX_PACKET:u32=49_152;
pub const MAX_DATAGRAM:usize=HEADER+CHUNK+4;
#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub struct Identity{pub session:u64,pub frame:u32,pub reference:u32,pub length:u32,pub crc:u32,pub capture_us:u64,pub sequence_count:u16}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Error{Length,Header,Crc,Identity,Offset}
#[derive(Debug)]pub struct Packet<'a>{pub id:Identity,pub offset:u32,pub body:&'a[u8]}
fn n32(b:&[u8],o:usize)->u32{u32::from_le_bytes(b[o..o+4].try_into().unwrap())}
pub fn decode(b:&[u8])->Result<Packet<'_>,Error>{
 if b.len()<HEADER+4||b.len()>MAX_DATAGRAM{return Err(Error::Length)}
 if &b[..4]!=b"DYN1"||b[4]!=VERSION||b[5]!=0||b[6..8]!=48u16.to_le_bytes(){return Err(Error::Header)}
 let n=u16::from_le_bytes(b[44..46].try_into().unwrap())as usize;
 if n==0||n>CHUNK||HEADER+n+4!=b.len(){return Err(Error::Length)}
 if crc32(&b[..HEADER+n])!=n32(b,HEADER+n){return Err(Error::Crc)}
 let id=Identity{session:u64::from_le_bytes(b[8..16].try_into().unwrap()),frame:n32(b,16),reference:n32(b,20),length:n32(b,24),crc:n32(b,32),capture_us:u64::from_le_bytes(b[36..44].try_into().unwrap()),sequence_count:u16::from_le_bytes(b[46..48].try_into().unwrap())};
 if id.session==0||id.sequence_count==0||id.sequence_count>MAX_SEQUENCE_FRAMES||id.length<80||id.length>MAX_PACKET{return Err(Error::Identity)}
 let offset=n32(b,28);let end=offset.checked_add(n as u32).ok_or(Error::Offset)?;
 if offset%1024!=0||end>id.length||n!=(id.length-offset).min(1024)as usize{return Err(Error::Offset)}
 Ok(Packet{id,offset,body:&b[HEADER..HEADER+n]})
}
/// 0=stored-prefix, 1=fully-staged, 2=actually-presented, 3=failed/retained.
/// Next offset acknowledges completed FPGA storage, never mere socket receipt.
pub fn reply(id:Identity,next:u32,status:u8,out:&mut[u8;52]){
 out.fill(0);out[..4].copy_from_slice(b"DYA1");out[4]=VERSION;out[5]=status;out[6..8].copy_from_slice(&48u16.to_le_bytes());
 out[8..16].copy_from_slice(&id.session.to_le_bytes());out[16..20].copy_from_slice(&id.frame.to_le_bytes());out[20..24].copy_from_slice(&id.reference.to_le_bytes());out[24..28].copy_from_slice(&id.length.to_le_bytes());out[28..32].copy_from_slice(&next.to_le_bytes());out[32..36].copy_from_slice(&id.crc.to_le_bytes());out[36..44].copy_from_slice(&id.capture_us.to_le_bytes());out[46..48].copy_from_slice(&id.sequence_count.to_le_bytes());let c=crc32(&out[..48]);out[48..].copy_from_slice(&c.to_le_bytes());
}
#[cfg(test)]mod tests{
 use super::*;
 fn packet(offset:u32,n:usize,total:u32)->Vec<u8>{let mut b=vec![0;48+n+4];b[..4].copy_from_slice(b"DYN1");b[4]=VERSION;b[6..8].copy_from_slice(&48u16.to_le_bytes());b[8..16].copy_from_slice(&7u64.to_le_bytes());b[24..28].copy_from_slice(&total.to_le_bytes());b[28..32].copy_from_slice(&offset.to_le_bytes());b[44..46].copy_from_slice(&(n as u16).to_le_bytes());b[46..48].copy_from_slice(&3u16.to_le_bytes());let c=crc32(&b[..48+n]);b[48+n..].copy_from_slice(&c.to_le_bytes());b}
 #[test]fn exact_chunks_and_tail(){assert_eq!(decode(&packet(0,1024,1100)).unwrap().body.len(),1024);assert_eq!(decode(&packet(1024,76,1100)).unwrap().offset,1024);}
 #[test]fn truncation_corruption_and_extra_bytes(){let b=packet(0,80,80);for i in 0..b.len(){assert!(decode(&b[..i]).is_err());let mut x=b.clone();x[i]^=1;assert!(decode(&x).is_err());}let mut x=b;x.push(0);assert!(decode(&x).is_err());}
 #[test]fn offsets_lengths_and_overflow(){for(o,n,t)in[(1,79,80),(1024,1024,1100),(0,80,1100),(0,1024,49153),(u32::MAX-1023,1024,49152)]{assert!(decode(&packet(o,n,t)).is_err());}}
 #[test]fn feedback_distinguishes_storage_and_presentation(){let id=decode(&packet(0,80,80)).unwrap().id;let mut b=[0;52];reply(id,80,1,&mut b);assert_eq!(b[5],1);assert_eq!(crc32(&b[..48]),n32(&b,48));reply(id,80,2,&mut b);assert_eq!(b[5],2);}
 #[test]fn version_one_rejected_even_with_valid_crc(){let mut b=packet(0,80,80);b[4]=1;let c=crc32(&b[..128]);b[128..].copy_from_slice(&c.to_le_bytes());assert_eq!(decode(&b).unwrap_err(),Error::Header);}
 #[test]fn reply_uses_explicit_version_three_and_count(){let id=decode(&packet(0,80,80)).unwrap().id;let mut b=[0;52];reply(id,80,2,&mut b);assert_eq!(b[4],3);assert_eq!(u16::from_le_bytes(b[46..48].try_into().unwrap()),3);assert_eq!(crc32(&b[..48]),n32(&b,48));}
 #[test]fn invalid_sequence_count_and_old_v2_rejected(){for count in [0u16,12001,u16::MAX]{let mut b=packet(0,80,80);b[46..48].copy_from_slice(&count.to_le_bytes());let c=crc32(&b[..128]);b[128..].copy_from_slice(&c.to_le_bytes());assert_eq!(decode(&b).unwrap_err(),Error::Identity);}let mut b=packet(0,80,80);b[4]=2;let c=crc32(&b[..128]);b[128..].copy_from_slice(&c.to_le_bytes());assert_eq!(decode(&b).unwrap_err(),Error::Header);}
}
