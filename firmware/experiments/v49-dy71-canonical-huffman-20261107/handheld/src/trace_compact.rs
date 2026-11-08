//! Fixed 94-byte, little-endian record + CRC, Base64-armored for mixed logs.
//! Called only for explicit frozen trace exports, never by packet workers.
use crate::streaming::{diagnostic_trace as trace, protocol};
pub const WIRE_BYTES: usize = 94;
pub struct Line { bytes: [u8; 136] }
impl Line { pub fn as_str(&self) -> &str { core::str::from_utf8(&self.bytes).unwrap() } }
fn flags(c:trace::Context, phase:bool, clipped:bool, ambiguous:bool, consumer:bool)->u16 {
    u16::from(c.incoming.frame_valid) | u16::from(c.incoming.offset_valid)<<1
        | u16::from(c.active.frame_valid)<<2 | u16::from(c.active.offset_valid)<<3
        | u16::from(c.queue_valid)<<4 | u16::from(phase)<<5 | u16::from(clipped)<<6
        | u16::from(ambiguous)<<7 | u16::from(consumer)<<8
}
pub fn record(index:u16,r:&trace::Record)->Line {
    pack(0,index,r.epoch,r.sequence,r.time_us,r.received_us,r.context,
        flags(r.context,r.phase_valid,r.duration_clipped,false,r.kind==trace::Kind::Complete),
        r.kind as u8,r.phase as u8,r.phase_since_us,r.detail,r.lock_us,r.qspi_us,r.consumer_us)
}
pub fn failure(index:u16,r:&trace::Failure)->Line {
    pack(1,index,r.epoch,r.sequence,r.time_us,r.received_us,r.context,
        flags(r.context,false,r.duration_clipped,r.tail_ambiguous,r.consumer_us.is_some()),
        255,255,0,r.detail,0,0,r.consumer_us.unwrap_or(0))
}
#[allow(clippy::too_many_arguments)]
fn pack(ty:u8,index:u16,epoch:u32,seq:u64,time:u64,rx:u64,c:trace::Context,
    flags:u16,kind:u8,phase:u8,since:u64,detail:u16,lock:u64,qspi:u64,consumer:u64)->Line {
    let mut b=[0u8;WIRE_BYTES];let mut n=0;
    macro_rules! put {($v:expr)=>{let v=$v.to_le_bytes();b[n..n+v.len()].copy_from_slice(&v);n+=v.len();}}
    put!(1u8);put!(ty);put!(index);put!(epoch);put!(seq);put!(time);put!(rx);
    put!(c.incoming.frame);put!(c.incoming.offset);put!(c.active.frame);put!(c.active.offset);put!(c.queued);
    put!(flags);put!(kind);put!(phase);put!(since);put!(detail);put!(lock);put!(qspi);put!(consumer);
    assert_eq!(n,90);let crc=!protocol::crc_update(!0,&b[..n]);put!(crc);assert_eq!(n,WIRE_BYTES);
    const B64:&[u8;64]=b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut line=Line{bytes:[b'=';136]};line.bytes[..8].copy_from_slice(b"USB_C38 ");
    for (i,chunk) in b.chunks(3).enumerate(){
        let x=(chunk[0]as u32)<<16 | (chunk.get(1).copied().unwrap_or(0)as u32)<<8 | chunk.get(2).copied().unwrap_or(0)as u32;
        let o=8+i*4;line.bytes[o]=B64[(x>>18)as usize];line.bytes[o+1]=B64[((x>>12)&63)as usize];
        if chunk.len()>1{line.bytes[o+2]=B64[((x>>6)&63)as usize];}if chunk.len()>2{line.bytes[o+3]=B64[(x&63)as usize];}
    }line
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn exports_full_width_fields_and_zero_valid_tail(){
        let c=trace::Context{incoming:trace::Position{frame:u32::MAX,offset:u32::MAX,frame_valid:true,offset_valid:true},active:trace::Position::UNKNOWN,queued:32,queue_valid:true};
        let f=trace::Failure{epoch:u32::MAX,sequence:u64::MAX,time_us:u64::MAX,context:c,detail:u16::MAX,received_us:u64::MAX,consumer_us:Some(0),duration_clipped:true,tail_ambiguous:true};
        let line=failure(31,&f);assert_eq!(line.as_str().len(),136);assert!(line.as_str().is_ascii());println!("{}",line.as_str());
    }
}
